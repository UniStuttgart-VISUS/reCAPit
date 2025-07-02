
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--surface_gaze', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--aois', type=Path, required=True)
    args = parser.parse_args()

    surface_gaze = pd.read_csv(args.surface_gaze)
    surface_gaze['mapped x [px]'] = surface_gaze['mapped x [px]'].astype(int)
    surface_gaze['mapped y [px]'] = surface_gaze['mapped y [px]'].astype(int)

    aois = get_aois(args.aois)
    labels = []

    for _, row in surface_gaze.iterrows():
        if not row['within_surface']:
            labels.append('')
            continue

        point = shapely.Point((row[['mapped x [px]', 'mapped y [px]']]))
        for label, poly in aois.items():
            if poly.contains(point):
                labels.append(label)
                break
        else:
            labels.append('')

    surface_gaze['mapped_aoi'] = labels
    surface_gaze.to_csv(args.surface_gaze, index=None)