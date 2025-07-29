import pandas as pd
import numpy as np
import argparse
import json
import logging

from tqdm import tqdm
from pathlib import Path
from map_fixations import fix2AOI



def compute_attention_signals(dfs, min_timestamp, max_timestamp, bin_width_sec=1):
    num_dfs = len(dfs)
    data_table = pd.concat(dfs)
    data_table = data_table[(data_table['start timestamp [sec]'] >= min_timestamp) & (data_table['end timestamp [sec]'] <= max_timestamp)]
    data_table = data_table[['start timestamp [sec]', 'end timestamp [sec]', 'event subtype']]

    if data_table.empty:
        raise ValueError('Provided recordings exhibit no gaze data!')

    time_series = {c: list() for c in data_table['event subtype'].unique()}

    for start_sec in tqdm(np.arange(min_timestamp, max_timestamp, bin_width_sec)):
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


def process_recordings(recordings, aoi_path, root_dir):
    mapped_fix = []

    for rec in tqdm(recordings, disable=True):
        if 'surface_fixations' not in rec['sources']:
            logging.info(f'"surface_fixations" is not a registered source in recording "{rec["id"]}".')
            continue

        out_dir = root_dir / rec['id']
        out_dir.mkdir(exist_ok=True)

        surface_gaze = fix2AOI(rec, aoi_path)
        out_path = out_dir / 'mapped_fix.csv'

        rec['artifacts']['mapped_fixations'] = {'path': str(out_path), 'categories': 'areas_of_interests'}
        logging.info(f'Registered "mapped_fixation" as an artifact in recording "{rec["id"]}"')

        surface_gaze.to_csv(out_path, index=None)
        mapped_fix.append(surface_gaze)
    return mapped_fix


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with open(args.manifest, 'r+') as f:
        manifest = json.load(f)

        if 'areas_of_interests' not in manifest['sources']:
            logging.error("Areas of interests are not specified in 'sources'!")
            exit(1)

        mapped_fix = process_recordings(manifest['recordings'], manifest['sources']['areas_of_interests']['path'], args.out_dir)

        if 'multi_time' not in manifest['artifacts']:
            logging.info("Create multi_time field in manifest")
            manifest['artifacts']['multi_time'] = {}

        out_path = args.out_dir / 'attention.csv'
        attention_signals = compute_attention_signals(mapped_fix, min_timestamp=0, max_timestamp=manifest['duration_sec'], bin_width_sec=0.5)
        attention_signals.to_csv(out_path, index=None)
        manifest['artifacts']['multi_time']['attention'] = {'path': str(out_path), 'categories': 'areas_of_interests'}
        logging.info('Registered "multi_time/attention" as an global artifact')

        f.seek(0)
        json.dump(manifest, f, indent=4)
