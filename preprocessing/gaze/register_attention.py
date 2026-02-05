import pandas as pd
import numpy as np
import argparse
import logging
import matplotlib.pyplot as plt

from tqdm import tqdm
from pathlib import Path
from helper.manifest_manager import ManifestManager


class ProgressiveVisualizer:
    """Handles real-time progressive visualization of attention signals."""
    
    def __init__(self, aoi_names, bin_width_sec, total_bins):
        self.aoi_names = aoi_names
        self.bin_width_sec = bin_width_sec
        self.total_bins = total_bins
        self.update_interval = max(1, total_bins // 50)
        
        # Setup interactive plot
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(14, 6))
        self.fig.canvas.manager.set_window_title('reCAPit - Attention Signal Debug')
        
        # Setup consistent colors
        colors = plt.cm.tab10(np.linspace(0, 1, len(aoi_names)))
        self.color_map = {aoi: colors[i] for i, aoi in enumerate(aoi_names)}
        
        logging.info("Progressive visualization window opened - computation in progress...")
    
    def should_update(self, bin_idx):
        """Check if visualization should be updated at this bin."""
        return bin_idx % self.update_interval == 0
    
    def update(self, time_series, bin_idx):
        """Update the visualization with current data."""
        self.ax.clear()
        time_axis = np.arange(len(time_series[self.aoi_names[0]])) * self.bin_width_sec
        
        for aoi_name in self.aoi_names:
            self.ax.plot(time_axis, time_series[aoi_name], 
                        label=aoi_name, linewidth=2, alpha=0.8, 
                        color=self.color_map[aoi_name])
        
        self.ax.set_xlabel('Time (seconds)', fontsize=12)
        self.ax.set_ylabel('Normalized Attention', fontsize=12)
        progress_pct = (bin_idx / self.total_bins) * 100
        current_time = len(time_series[self.aoi_names[0]]) * self.bin_width_sec
        self.ax.set_title(f'Progressive Attention Signals - {progress_pct:.1f}% Complete (t={current_time:.1f}s)', 
                         fontsize=14, fontweight='bold')
        self.ax.legend(loc='upper right', framealpha=0.9)
        self.ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)
    

def compute_attention_signals(dfs, min_timestamp, max_timestamp, bin_width_sec=1, debug=False, debug_dir=None):
    num_dfs = len(dfs)
    data_table = pd.concat(dfs)
    data_table = data_table[(data_table['start timestamp [sec]'] >= min_timestamp) & (data_table['end timestamp [sec]'] <= max_timestamp)]
    data_table = data_table[['start timestamp [sec]', 'end timestamp [sec]', 'event subtype']]

    if data_table.empty:
        msg = 'Provided recordings exhibit no gaze data!'
        raise ValueError(msg)

    time_series = {c: [] for c in data_table['event subtype'].unique()}
    
    # Initialize progressive visualizer if debug mode is enabled
    visualizer = None
    if debug:
        total_bins = int((max_timestamp - min_timestamp) / bin_width_sec)
        visualizer = ProgressiveVisualizer(list(time_series.keys()), bin_width_sec, total_bins)

    # Main computation loop
    bin_idx = 0
    for start_sec in tqdm(np.arange(min_timestamp, max_timestamp, bin_width_sec)):
        df_copy = data_table.copy(True)
        df_copy['start timestamp [sec]'] = df_copy['start timestamp [sec]'].clip(start_sec, start_sec + bin_width_sec)
        df_copy['end timestamp [sec]'] = df_copy['end timestamp [sec]'].clip(start_sec, start_sec + bin_width_sec)
        df_copy['duration [sec]'] = df_copy['end timestamp [sec]'] - df_copy['start timestamp [sec]']

        out = df_copy.groupby('event subtype').agg("sum")
        for c in time_series:
            norm_aoi_dur = out.loc[c, 'duration [sec]'] / (num_dfs*bin_width_sec) 
            time_series[c].append(norm_aoi_dur if c in out.index else 0)

        # Update visualization if enabled
        if visualizer and visualizer.should_update(bin_idx):
            visualizer.update(time_series, bin_idx)

        bin_idx += 1

    time_series = {c: np.array(v) for c, v in time_series.items()}
    return pd.DataFrame.from_dict(time_series)


def recordings_map_fixations(recordings:list) -> list[pd.DataFrame]:
    all_mapped_fixation = []

    for rec in tqdm(recordings, disable=False):
        if 'mapped_fixations' not in rec['artifacts']:
            continue
        mapped_fix = pd.read_csv(rec['artifacts']['mapped_fixations']['path'])
        all_mapped_fixation.append(mapped_fix)

    return all_mapped_fixation


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--window_size_sec', type=float, default=0.5)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--debug', action='store_true', help='Enable debug visualizations')
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with ManifestManager(args.manifest, args.root_dir) as man:
        mapped_fix = recordings_map_fixations(man.get_recordings())

        out_path = args.root_dir / 'attention.csv'
        attention_signals = compute_attention_signals(
            mapped_fix,
            min_timestamp=0,
            max_timestamp=man.get_duration_sec(),
            bin_width_sec=args.window_size_sec,
            debug=args.debug,
            debug_dir=args.root_dir,
        )
        attention_signals.to_csv(out_path, index=None)

        man.register_multi_time('attention', {'path': str(out_path), 'categories': 'areas_of_interests'})
        logging.info('Registered "multi_time/attention" as an global artifact')