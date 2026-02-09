import argparse
import pandas as pd
import matplotlib.pyplot as plt
import ruptures as rpt
import scipy
import numpy as np
import scipy.signal
import logging
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
        mtv = pd.read_csv(man.get_multi_time(args.input_signal)['path'], encoding='utf-8-sig')
        result = mvt_segmentation(mtv, man.get_duration_sec(), args.penalization,
                                  downsampling_factor=args.downsampling_factor,
                                  min_dur_sec=2*args.min_dur_sec, show_plot=True)
        records = []

        for segment_start, segment_end in zip(result[:-1], result[1:]):
            mtv_segment = mtv.iloc[segment_start*args.downsampling_factor:segment_end*args.downsampling_factor]

            start_ts = mtv_segment.iloc[0]['timestamp [sec]']
            end_ts = mtv_segment.iloc[-1]['timestamp [sec]']
            records.append((start_ts, end_ts, end_ts - start_ts))

        out = pd.DataFrame.from_records(data=records, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]'])
        out.to_csv(out_path, index=None, encoding='utf-8-sig')
        man.register_segments('initial', {'path': str(out_path)})
        logger.info('Registered "segments/initial" as an global artifact')
