import argparse
import json
import pandas as pd
import logging

from tqdm import tqdm
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--transcript', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with open(args.manifest, 'r+') as f:
        manifest = json.load(f)
        manifest['artifacts']['transcript'] = {'path': str(args.transcript)}
        transcript = pd.read_csv(args.transcript)

        logging.info('Registered "transcript" as an global artifact')

        for rec in tqdm(manifest['recordings'], disable=True):
            out_dir = args.out_dir / rec['id']
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / 'transcript.csv'

            transcript_rec = transcript[transcript['speaker'] == rec['id']].copy()
            transcript_rec['event data'] = transcript_rec['text'] 
            transcript_rec['event type'] = 'speech'
            transcript_rec['event subtype'] = rec['role']
            transcript_rec = transcript_rec.drop(['text', 'speaker'], axis=1)
            transcript_rec.to_csv(out_path, index=None, encoding='utf-8-sig')

            rec['artifacts']['transcript'] = {'path': str(out_path), 'categories': 'roles'}
            logging.info(f'Registered "transcript" as an artifact in recording "{rec["id"]}"')

        f.seek(0)
        json.dump(manifest, f, indent=4)