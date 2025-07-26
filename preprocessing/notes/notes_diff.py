import argparse
import pandas as pd
import numpy as np
import json

from bs4 import BeautifulSoup
from pathlib import Path
from docx2python import docx2python
from diff_match_patch import diff_match_patch
from tqdm import tqdm


def strip_chars(x: str):
    return x.replace('\t', '').replace('\n', ' ').replace('\r', '').replace('--', '').replace("'", '').replace("''", '')


def sample_docs(timestamps, sample_dur_sec):
    sample_indices = [0]
    curr_dur = 0

    for idx in range(1, len(timestamps)):
        curr_dur += timestamps[idx] - timestamps[idx-1]

        if curr_dur >= sample_dur_sec:
            sample_indices.append(idx)
            curr_dur = 0
    return sample_indices



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--sample_dur_sec', type=float, default=150)
    args = parser.parse_args()
    root_dir = args.meta.parent

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        doc_versions = []
        timestamps = []
        out = []

        args.out_dir.mkdir(exist_ok=True)
        out_path = args.out_dir / 'notes_diff.csv'

        differ = diff_match_patch()
        differ.Diff_Timeout = 0
        differ.Match_Threshold = .5

        snapshots_dir = Path(meta['sources']['notes_snapshots']['path'])
        docs = list(snapshots_dir.glob('*.docm'))

        for doc_file in tqdm(docs, desc='docx2python', unit='document'):
            timestamps.append(int(doc_file.stem))
            with docx2python(doc_file) as docx_content:
                text = docx_content.text.replace('\n', ' ').replace('\t', '').replace('.', '.\n')
                soup = BeautifulSoup(text, "html.parser")
                cleaned_text = soup.get_text()
                doc_versions.append(cleaned_text)

        timestamps = np.array(timestamps)
        doc_versions = np.array(doc_versions)
        indices = sample_docs(timestamps, args.sample_dur_sec)

        timestamps = timestamps[indices]
        doc_versions = doc_versions[indices]

        for idx in tqdm(range(len(doc_versions) - 1), desc='diff', unit='diffs'):
            diff = differ.diff_main(doc_versions[idx], doc_versions[idx+1], checklines=False)
            differ.diff_cleanupSemantic(diff)
            html = differ.diff_prettyHtml(diff)
            if html == "":
                html = "<span>/</span>"

            insertions = [strip_chars(data) for dt, data in diff if dt == diff_match_patch.DIFF_INSERT]
            deletions = [strip_chars(data) for dt, data in diff if dt == diff_match_patch.DIFF_DELETE]

            insertions = [x.strip() for x in insertions if x != '' and len(x) > 5]
            deletions = [x.strip() for x in deletions if x != '' and len(x) > 5]

            out.append((timestamps[idx], timestamps[idx+1], ';'.join(insertions), ';'.join(deletions), html))


        df = pd.DataFrame(data=out, columns=['start timestamp [sec]', 'end timestamp [sec]', 'insertions', 'deletions', 'html'])
        offset_sec = df['start timestamp [sec]'].iloc[0]

        df['start timestamp [sec]'] = meta['sources']['notes_snapshots']['offset_sec'] + df['start timestamp [sec]'] - offset_sec
        df['end timestamp [sec]'] = meta['sources']['notes_snapshots']['offset_sec'] + df['end timestamp [sec]'] - offset_sec

        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        meta['artifacts']['notes_diff'] = {'path': str(out_path)}

        f.seek(0)
        json.dump(meta, f, indent=4)