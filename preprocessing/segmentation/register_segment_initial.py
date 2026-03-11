import argparse
import pandas as pd
import matplotlib.pyplot as plt
import ruptures as rpt
import scipy
import numpy as np
import scipy.signal
import logging

from itertools import pairwise
from pathlib import Path
from helper.manifest_manager import ManifestManager

logger = logging.getLogger(__name__)

def mvt_segmentation(mvt: np.ndarray, duration_sec: float, penalization:int,
                     downsampling_factor:int=5, min_dur_sec:float=30,
                     show_plot=True) -> np.ndarray:

    if 'timestamp [sec]' not in mvt.columns:
        logger.warning('Missing timestamp column. Adding timestamp column')
        mvt['timestamp [sec]'] = np.linspace(0, duration_sec, mvt.shape[0])

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
        preprocessed = preprocessed.to_numpy()

    logger.info(f'Original signal shape: {mvt.shape}, downsampled signal shape: {preprocessed.shape}')

    min_size = int(preprocessed.shape[0] * min_dur_sec / duration_sec)

    algo = rpt.Pelt(model='rbf', min_size=min_size, jump=5).fit(preprocessed)
    result = algo.predict(pen=penalization)

    if show_plot:
        rpt.display(preprocessed, result)
        plt.show()

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--input_signal', default='attention', required=False)
    parser.add_argument('--downsampling_factor', default=5, required=False, type=int)
    parser.add_argument('--penalization', default=10, required=False, type=int)
    parser.add_argument('--min_dur_sec', default=15, required=False, type=float)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    out_path = args.root_dir / 'initial.csv'

    with ManifestManager(args.manifest, args.root_dir) as man:
        # Columns: start timestamp [sec],end timestamp [sec],text,speaker
        transcript = pd.read_csv(man.get_transcript()['path'], encoding='utf-8-sig')

        mtv = pd.read_csv(man.get_multi_time(args.input_signal)['path'], encoding='utf-8-sig')
        result = mvt_segmentation(mtv, man.get_duration_sec(), args.penalization,
                                  downsampling_factor=args.downsampling_factor,
                                  min_dur_sec=2*args.min_dur_sec, show_plot=True)
        records = []

        for segment_start, segment_end in pairwise(result):
            mtv_segment = mtv.iloc[segment_start*args.downsampling_factor:segment_end*args.downsampling_factor]

            start_ts = mtv_segment.iloc[0]['timestamp [sec]']
            end_ts = mtv_segment.iloc[-1]['timestamp [sec]']

            mask_left = transcript['start timestamp [sec]'] >= start_ts
            mask_right = transcript['end timestamp [sec]'] <= end_ts
            mask = mask_left & mask_right

            if not mask.any():
                logger.warning(f'No transcript rows found between {start_ts} and {end_ts}')
                continue

            aligned_start_ts = transcript.loc[mask_left, 'start timestamp [sec]'].iloc[0]
            aligned_end_ts = transcript.loc[mask_right, 'end timestamp [sec]'].iloc[-1]

            logger.info('start (unaligned): %f; start (aligned): %f', start_ts, aligned_start_ts)
            logger.info('end (unaligned): %f; end (aligned): %f', end_ts, aligned_end_ts)

            records.append((aligned_start_ts, aligned_end_ts, aligned_end_ts - aligned_start_ts))

        out = pd.DataFrame.from_records(data=records, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]'])
        out.to_csv(out_path, index=None, encoding='utf-8-sig')
        man.register_segments('initial', {'path': str(out_path)})
        logger.info('Registered "segments/initial" as an global artifact')
