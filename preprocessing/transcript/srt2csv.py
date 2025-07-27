import subtitle_parser
import argparse
from pathlib import Path
import pandas as pd
import re


def timestamp_to_sec(ts):
    hour, min, sec, ms = ts
    return 3600*hour + 60*min + sec + 1e-3*ms

def timestamp_formatted(ts):
    hour, min, sec, ms = ts
    return f'{hour:02d}:{min:02d}:{sec:02d}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    with open(args.input, 'r') as input_file:
        parser = subtitle_parser.SrtParser(input_file)
        parser.parse()

    parser.print_warnings()
    output = []

    for subtitle in parser.subtitles:
        text = subtitle.text
        text = re.sub(r'\(.+\)', '', text)
        text = re.sub(r'^-', '', text)
        text = text.strip()

        output.append((timestamp_formatted(subtitle.start), timestamp_formatted(subtitle.end) ,timestamp_to_sec(subtitle.start), timestamp_to_sec(subtitle.end), text))

    df = pd.DataFrame(output, columns=['start timestamp [hh:mm:ss]', 'end timestamp [hh:mm:ss]', 'start timestamp [sec]', 'end timestamp [sec]', 'text'])
    df['Speaker'] = ''

    df['start timestamp [sec]'] = df['start timestamp [sec]'] - df['start timestamp [sec]'].iloc[0]
    df['end timestamp [sec]'] = df['end timestamp [sec]'] - df['start timestamp [sec]'].iloc[0]
    df.to_csv(args.output, index=False, float_format='%.3f')