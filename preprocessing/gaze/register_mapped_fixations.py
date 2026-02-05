import pandas as pd
import argparse
import sys
import json
import shapely

from pathlib import Path
from helper.manifest_manager import ManifestManager

def read_aois_from_file(aoi_path: Path) -> dict[str, shapely.Polygon]:
    with open(aoi_path) as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])
        return shapes_geom


def map_fixations_to_aois(surface_fixations: pd.DataFrame, 
                          aoi_geometries: dict[str, shapely.Polygon]) -> pd.DataFrame:

    surface_fixations['mapped x [px]'] = surface_fixations['mapped x [px]'].astype(int)
    surface_fixations['mapped y [px]'] = surface_fixations['mapped y [px]'].astype(int)

    surface_fixations = surface_fixations[surface_fixations['within_surface']].copy()

    labels = []

    for _, row in surface_fixations.iterrows():
        point = shapely.Point(row[['mapped x [px]', 'mapped y [px]']])
        for label, poly in aoi_geometries.items():
            if poly.contains(point):
                labels.append(label)
                break
        else:
            labels.append('__NA__')

    surface_fixations['mapped_aoi'] = labels
    surface_fixations = surface_fixations.loc[surface_fixations['mapped_aoi'] != '__NA__'].copy()
    surface_fixations['event data'] = surface_fixations.apply(lambda row: f'{row["mapped x [px]"]};{row["mapped y [px]"]}', axis=1)
    surface_fixations['event type'] = 'attention'
    surface_fixations['event subtype'] = surface_fixations['mapped_aoi']
    return surface_fixations.drop(['mapped_aoi', 'within_surface', 'mapped x [px]', 'mapped y [px]'], axis=1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--rec_id', type=str, required=True)
    args = parser.parse_args()

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec = man.get_recording(args.rec_id)
        workspace_video = man.get_video('workspace')
        gaze_info = rec['sources']['gaze']

        rec_dir = args.root_dir / rec['id']
        rec_dir.mkdir(exist_ok=True, parents=False)

        aoi_path = man.get_areas_of_interests()['path']
        aoi_geometries = read_aois_from_file(aoi_path)

        if 'surface_fixations' not in rec['artifacts']:
            sys.exit()

        surface_fix = pd.read_csv(rec['artifacts']['surface_fixations']['path'])
        mapped_fix = map_fixations_to_aois(surface_fix, aoi_geometries)
        out_path = rec_dir / 'mapped_fixations.csv'

        rec['artifacts']['mapped_fixations'] = {'path': str(out_path), 'categories': 'areas_of_interests'}
        mapped_fix.to_csv(out_path, index=None)
