import argparse
import pandas as pd
import json
import shapely

from pathlib import Path


def get_aois(aoi_path):
    with open(aoi_path, 'r') as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])
        return shapes_geom


def fix2AOI(rec, aoi_path):
    surface_gaze = pd.read_csv(rec['sources']['surface_fixations']['path'])
    offset_sec = rec['sources']['surface_fixations']['offset_sec']

    surface_gaze['mapped x [px]'] = surface_gaze['mapped x [px]'].astype(int)
    surface_gaze['mapped y [px]'] = surface_gaze['mapped y [px]'].astype(int)

    surface_gaze['start timestamp [sec]'] = surface_gaze['start timestamp [sec]'] - offset_sec
    surface_gaze['end timestamp [sec]'] = surface_gaze['end timestamp [sec]'] - offset_sec

    surface_gaze = surface_gaze[surface_gaze['within_surface']]

    aois = get_aois(aoi_path)
    labels = []

    for _, row in surface_gaze.iterrows():
        point = shapely.Point((row[['mapped x [px]', 'mapped y [px]']]))
        for label, poly in aois.items():
            if poly.contains(point):
                labels.append(label)
                break
        else:
            labels.append('__NA__')

    surface_gaze['mapped_aoi'] = labels
    surface_gaze = surface_gaze[surface_gaze['mapped_aoi'] != '__NA__'].copy()
    surface_gaze['event data'] = surface_gaze.apply(lambda row: f'{row["mapped x [px]"]};{row["mapped y [px]"]}', axis=1)
    surface_gaze['event type'] = 'attention'
    surface_gaze['event subtype'] = surface_gaze['mapped_aoi']
    surface_gaze = surface_gaze.drop(['mapped_aoi', 'within_surface', 'mapped x [px]', 'mapped y [px]'], axis=1)
    return surface_gaze


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    args = parser.parse_args()