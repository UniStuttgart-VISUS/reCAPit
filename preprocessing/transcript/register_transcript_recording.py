import argparse
import pandas as pd
import logging
import sys
import os

from tqdm import tqdm
from pathlib import Path
from helper.manifest_manager import ManifestManager

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec_root = args.root_dir
        transcript = pd.read_csv(man.get_transcript()['path'])

        for rec in tqdm(man.get_recordings(), disable=True):
            out_dir = rec_root / rec['id']
            out_path = out_dir / 'transcript.csv'
            out_dir.mkdir(exist_ok=True, parents=False)
            transcript_rec = transcript[transcript['speaker'] == rec['id']].copy()
            transcript_rec['event data'] = transcript_rec['text']
            transcript_rec['event type'] = 'speech'
            transcript_rec['event subtype'] = rec['role']

            if transcript_rec.empty:
                logging.error(f'Speaker with id "{rec['id']}" does not exist in transcript!')
                sys.exit(1)

            transcript_rec = transcript_rec.drop(['text', 'speaker'], axis=1)
            transcript_rec.to_csv(out_path, index=None, encoding='utf-8-sig')

            rec['artifacts']['transcript'] = {'path': str(out_path), 'categories': 'roles'}

            logging.info(f'Registered "transcript" as an artifact in recording "{rec["id"]}"')
    sys.exit(0)