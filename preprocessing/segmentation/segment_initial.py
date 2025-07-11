
import argparse
import pandas as pd
import json
import matplotlib.pyplot as plt
import ruptures as rpt
import scipy
import numpy as np
import scipy.signal
import logging
from pathlib import Path


def mvt_segmentation(mvt, downsampling_factor=5, min_dur_sec=30, show_plot=True):

    if 'timestamp [sec]' not in mvt.columns:
        logging.warn("Missing timestamp column. Adding timestamp column")
        mvt['timestamp [sec]'] = np.linspace(0, meta['duration_sec'], mvt.shape[0])
    
    preprocessed = pd.DataFrame.copy(mvt)

    if 'timestamp [sec]' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['timestamp [sec]'])

    if 'frame' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['frame'])

    if 'full' in mvt.columns:
        preprocessed = preprocessed.drop(columns=['full'])

    if downsampling_factor > 1:
        preprocessed = scipy.signal.decimate(preprocessed.values, downsampling_factor, axis=0)
    else:
        preprocessed = preprocessed.values

    print(f'Original signal shape: {mvt.shape}, downsampled signal shape: {preprocessed.shape}')

    #min_size = (meta['duration_s'] / mtv.shape[0]) * min_dur_sec / downsampling_factor
    min_size = int(preprocessed.shape[0] * min_dur_sec / meta['duration_sec'])

    print(f"Minimum segment size: {min_size}")

    algo = rpt.Pelt(model="rbf", min_size=min_size, jump=5).fit(preprocessed)
    #algo = rpt.Pelt(model="rbf", min_size=1, jump=1).fit(preprocessed)
    #result = algo.predict(pen=20)
    result = algo.predict(pen=10)

    if show_plot:
        rpt.display(preprocessed, result)
        plt.show()

    return result

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--input_signal', default='attention', required=False)
    parser.add_argument('--downsampling_factor', default=5, required=False, type=int)
    parser.add_argument('--min_dur_sec', default=15, required=False, type=float)
    args = parser.parse_args()

    root_dir = args.meta.parent
    out_path = args.out_dir / 'initial.csv'

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        if args.input_signal not in meta['artifacts']['time']:
            logging.error(f'Signal "{args.input_signal}" not found in meta file.')
            exit(1)

        mtv = pd.read_csv(meta['artifacts']['time'][args.input_signal], encoding='utf-8-sig')
        result = mvt_segmentation(mtv, downsampling_factor=args.downsampling_factor, min_dur_sec=2*args.min_dur_sec, show_plot=True)
        records = []

        for segment_start, segment_end in zip(result[:-1], result[1:]):
            mtv_segment = mtv.iloc[segment_start*args.downsampling_factor:segment_end*args.downsampling_factor]

            start_ts = mtv_segment.iloc[0]['timestamp [sec]']
            end_ts = mtv_segment.iloc[-1]['timestamp [sec]']
            records.append((start_ts, end_ts, end_ts - start_ts))

        out = pd.DataFrame.from_records(data=records, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]'])
        out.to_csv(out_path, index=None, encoding='utf-8-sig')
        meta['artifacts']['segments']['initial'] = str(out_path)

        f.seek(0)
        json.dump(meta, f, indent=4)