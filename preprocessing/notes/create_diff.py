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
    return x.replace('\t', '').replace('\n', ' ').replace('--', '').replace("'", '').replace("''", '')
    return x


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--notes_dir', type=Path, required=True)
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()

    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    doc_versions = []
    timestamps = []

    every_nth = 5
    args.out_dir.mkdir(exist_ok=True)

    differ = diff_match_patch()
    differ.Diff_Timeout = 0
    differ.Match_Threshold = .5

    docs = list(args.notes_dir.glob('*.docm'))
    docs = docs[::every_nth]

    for doc_file in docs:
        timestamps.append(int(doc_file.stem))
        print(doc_file)
        with docx2python(doc_file) as docx_content:
            text = docx_content.text.replace('\n', ' ').replace('\t', '').replace('.', '.\n')
            soup = BeautifulSoup(text, "html.parser")
            cleaned_text = soup.get_text()
            doc_versions.append(cleaned_text)

    out = []

    for idx in tqdm(range(len(doc_versions) - 1), unit='diffs'):
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

    global_ts = 1e-9*meta["start_time_system_s"]
    df['start timestamp [sec]'] = df['start timestamp [sec]'] - global_ts
    df['end timestamp [sec]'] = df['end timestamp [sec]'] - global_ts
    df.to_csv(args.out_dir / 'diffs.csv', index=False, encoding="utf-8-sig  ")