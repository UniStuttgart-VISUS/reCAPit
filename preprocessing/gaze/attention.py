import pandas as pd
import numpy as np
import argparse
import json

from pathlib import Path


def compute_attention_signals(recordings, min_timestamp, max_timestamp, bin_width_sec=1):
    dfs = [pd.read_csv(rec['artifacts']['mapped_fixations']) for rec in recordings if 'mapped_fixations' in rec['artifacts']]
    num_dfs = len(dfs)

    data_table = pd.concat(dfs)
    data_table = data_table[(data_table['start timestamp [sec]'] >= min_timestamp) & (data_table['end timestamp [sec]'] <= max_timestamp)]
    data_table = data_table[['start timestamp [sec]', 'end timestamp [sec]', 'event subtype']]

    if data_table.empty:
        raise ValueError('Provided recordings exhibit no gaze data!')

    time_series = {c: list() for c in data_table['event subtype'].unique()}

    for start_sec in np.arange(min_timestamp, max_timestamp, bin_width_sec):
        df_copy = data_table.copy(True)
        df_copy['start timestamp [sec]'] = df_copy['start timestamp [sec]'].clip(start_sec, start_sec + bin_width_sec)
        df_copy['end timestamp [sec]'] = df_copy['end timestamp [sec]'].clip(start_sec, start_sec + bin_width_sec)
        df_copy['duration [sec]'] = df_copy['end timestamp [sec]'] - df_copy['start timestamp [sec]']

        out = df_copy.groupby('event subtype').agg("sum")
        for c in time_series.keys():
            norm_aoi_dur = out.loc[c, 'duration [sec]'] / (num_dfs*bin_width_sec) 
            time_series[c].append(norm_aoi_dur if c in out.index else 0)

    time_series = {c: np.array(v) for c, v in time_series.items()}
    out =  pd.DataFrame.from_dict(time_series)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()

    out_path = args.out_dir / 'attention.csv'

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        attention_signals = compute_attention_signals(meta['recordings'], min_timestamp=0, max_timestamp=meta['duration_sec'], bin_width_sec=0.5)
        attention_signals.to_csv(out_path, index=None)

        meta['artifacts']['multi_time']['attention'] = {'path': str(out_path), 'categories': 'areas_of_interests'}

        f.seek(0)
        json.dump(meta, f, indent=4)
