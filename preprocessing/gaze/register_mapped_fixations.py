import pandas as pd
import argparse
import sys
import json
import logging
import zarr
import shapely

from pathlib import Path
from helper.manifest_manager import ManifestManager

logger = logging.getLogger(__name__)


def read_aois_from_file(aoi_path: Path) -> dict[str, shapely.Polygon]:
    with open(aoi_path) as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])
        return shapes_geom


def map_fixations_to_aois(
    surface_fixations: pd.DataFrame,
    aoi_geometries: dict[str, shapely.Polygon],
) -> pd.DataFrame:
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
    surface_fixations['event data'] = surface_fixations.apply(
        lambda row: f'{row["mapped x [px]"]};{row["mapped y [px]"]}', axis=1,
    )
    surface_fixations['event type'] = 'attention'
    surface_fixations['event subtype'] = surface_fixations['mapped_aoi']
    return surface_fixations.drop(
        ['mapped_aoi', 'within_surface', 'mapped x [px]', 'mapped y [px]'], axis=1,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--rec_id', type=str, required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec = man.get_recording(args.rec_id)

        rec_dir = args.root_dir / rec.rec_id
        rec_dir.mkdir(exist_ok=True, parents=False)

        all_events = []
        categories = []

        if not rec.has_artifact('surface_fixations'):
            surface_fix_path = rec.get_artifact('surface_fixations')['path']
            surface_fix = pd.read_csv(surface_fix_path)

            aoi_path = man.get_source('areas_of_interests')['path']
            aoi_geometries = read_aois_from_file(aoi_path)

            aoi_events = map_fixations_to_aois(surface_fix, aoi_geometries)
            logger.info('Mapped %i fixations to AOIs', len(aoi_events))
            all_events.append(aoi_events)
            categories.append('areas_of_interests')

        mapped_fix = pd.concat(all_events, ignore_index=True)
        out_path = rec_dir / 'mapped_fixations.csv'

        rec.register_artifact('mapped_fixations', {'path': str(out_path),
                                                   'categories': categories})
        mapped_fix.to_csv(out_path, index=None)
