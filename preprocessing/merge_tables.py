import pandas as pd
import argparse
import json
import shapely

from pathlib import Path
from tqdm import tqdm


def get_aoi_shapes(aoi_path):
    with open(aoi_path, 'r') as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])
        return shapes_geom


def merge_surface(df, time_delta_threshold=.5):
    merged_rows = []
    for _, row in df.iterrows():
        if len(merged_rows) > 1:
            time_delta = row['start timestamp [sec]'] - merged_rows[-1]['end timestamp [sec]']
            event_data_match = row['event data'] == merged_rows[-1]['event data']

            if time_delta < time_delta_threshold and event_data_match:
                merged_rows[-1]['end timestamp [sec]'] = row['end timestamp [sec]']
            else:
                merged_rows.append(row)
        else:
            merged_rows.append(row)
    return pd.DataFrame(merged_rows)


def merge_speech(df, time_delta_threshold=.5):
    merged_rows = []
    for _, row in df.iterrows():
        if len(merged_rows) > 1:
            time_delta = row['start timestamp [sec]'] - merged_rows[-1]['end timestamp [sec]']

            if time_delta < time_delta_threshold:
                merged_rows[-1]['end timestamp [sec]'] = row['end timestamp [sec]']
                merged_rows[-1]['event data'] = merged_rows[-1]['event data'] + " " + row['event data']
            else:
                merged_rows.append(row)
        else:
            merged_rows.append(row)
    return pd.DataFrame(merged_rows)


def rec_table(rec_id, rec_dir, rec_offset, aoi_shapes, all_speakers):
    data = []

    if (rec_dir / 'fixations.csv').is_file():
        fixations = pd.read_csv(rec_dir / 'fixations.csv')
        fixations['start'] = 1e-9*(fixations['start timestamp [ns]'] - rec_offset)
        fixations['end'] = 1e-9*(fixations['end timestamp [ns]'] - rec_offset)

        surface_gaze = pd.read_csv(rec_dir / 'surface_fix.csv')
        surface_gaze = surface_gaze[surface_gaze['within_surface']]
        surface_gaze['mapped x [px]'] = surface_gaze['mapped x [px]'].astype(int)
        surface_gaze['mapped y [px]'] = surface_gaze['mapped y [px]'].astype(int)
        surface_gaze['fixation index'] = surface_gaze['fixation index'].astype(int)

        for _, row in surface_gaze.iterrows():
            start_sec = fixations['start'].iloc[row['fixation index']-1]
            end_sec = fixations['end'].iloc[row['fixation index']-1]
            point = shapely.Point((row[['mapped x [px]', 'mapped y [px]']]))

            for label, poly in aoi_shapes.items():
                if poly.contains(point):
                    data.append((start_sec, end_sec, 'Surface hit', 'Scene', label))
                    break

    speaker_source = all_speakers[all_speakers['speaker'] == rec_id]
    for _, row in speaker_source.iterrows():
        data.append((row['start timestamp [sec]'], row['end timestamp [sec]'], 'Speech', 'na' , row['text']))

    df = pd.DataFrame(data=data, columns=['start timestamp [sec]', 'end timestamp [sec]', 'event type', 'event subtype', 'event data'])
    df = df.sort_values('start timestamp [sec]')
    return df


def merge_table(table):
    merged_surf = merge_surface(table[table['event type'] == 'Surface hit'], time_delta_threshold=1)
    if not merged_surf.empty:
        merged_surf = merged_surf[(merged_surf['end timestamp [sec]'] - merged_surf['start timestamp [sec]']) >= 0.1]
        merged_surf = merge_surface(merged_surf, time_delta_threshold=1)

    merged_speech = merge_speech(table[table['event type'] == 'Speech'], time_delta_threshold=1)
    merged_table = pd.concat([merged_surf, merged_speech], axis=0)
    merged_table = merged_table.sort_values('start timestamp [sec]')
    return merged_table


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    args = parser.parse_args()
    
    root_dir = args.meta.parent
    meta = json.load(open(args.meta, 'r'))

    aoi_shapes = get_aoi_shapes(root_dir / meta['areas_of_interests'])
    speaker_source = pd.read_csv(root_dir / meta['speaker_transcript'])
    global_start = meta['start_time_system_s']

    for rec in tqdm(meta['recordings']):
        rec_dir = root_dir / rec['dir']
        rec_id = rec['id']

        table = rec_table(rec_id, rec_dir, global_start, aoi_shapes, speaker_source)
        table.to_csv(rec_dir / 'data.csv', index=False, encoding='utf-8')

        merged_table = merge_table(table)
        merged_table.to_csv(rec_dir / 'merged_data.csv', index=False, encoding='utf-8')