import argparse
import json
import pandas as pd
import logging

from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        if 'transcript' not in meta['artifacts']:
            logging.error("Transcript is not specified in artifacts!")
            exit(1)

        transcript = pd.read_csv(meta['artifacts']['transcript']['path'])

        for rec in meta['recordings']:
            out_dir = args.out_dir / rec['id']
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / 'transcript.csv'

            transcript_rec = transcript[transcript['speaker'] == rec['id']].copy()
            transcript_rec['event data'] = transcript_rec['text'] 
            transcript_rec['event type'] = 'speech'
            transcript_rec['event subtype'] = rec['role']
            transcript_rec = transcript_rec.drop(['text', 'speaker'], axis=1)
            transcript_rec.to_csv(out_path, index=None, encoding='utf-8-sig')

            rec['artifacts']['transcript'] = {'path': str(out_path)}


        f.seek(0)
        json.dump(meta, f, indent=4)