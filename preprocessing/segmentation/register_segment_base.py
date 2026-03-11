import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging
from pathlib import Path
from helper.manifest_manager import ManifestManager

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    out_path = args.root_dir / 'base.csv'

    with ManifestManager(args.manifest, args.root_dir) as man:
        dur_sec = man.get_duration_sec()
        out = pd.DataFrame(data=[(0.0, dur_sec, dur_sec)], columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]'])
        out.to_csv(out_path, index=None, encoding='utf-8-sig')
        man.register_segments('base', {'path': str(out_path)})
        logger.info('Registered "segments/base" as an global artifact')
