import cv2 as cv
import pandas as pd
import argparse
import logging
import zarr
import sys

from pathlib import Path
from tqdm import tqdm
from utils import get_aois, get_masks
from helper.manifest_manager import ManifestManager

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    with ManifestManager(args.manifest, args.root_dir) as man:
        cap = cv.VideoCapture(man.get_video('workspace')['path'])
        movement_store_info = man.get_source('movement_store')

        z = zarr.open(movement_store_info['path'], mode='r')
        source_fps = z.attrs['source_fps']
        fps = z.attrs['fps']

        source_width = z.attrs['source_width']
        source_height = z.attrs['source_height']
        width = z.attrs['width']
        height = z.attrs['height']

        aois = get_aois(man.get_source('areas_of_interests')['path'])
        masks = get_masks(aois, source_width, source_height)
        masks = {label: cv.resize(mask, dsize=(width, height)) for label, mask in masks.items()}

        out = []
        out_path = args.root_dir / 'movement.csv'

        for frame_pos in tqdm(range(z.shape[0])):
            frame_mask = z[frame_pos]

            src_frame_pos = int(frame_pos * fps / source_fps)
            src_frame_sec = frame_pos / fps

            total_foreground = frame_mask.sum() / (width * height)
            out_row = [src_frame_pos, src_frame_sec, total_foreground]

            for aoi_mask in masks.values():
                fg_mask_aoi = frame_mask * aoi_mask
                aoi_foreground = fg_mask_aoi.sum() / aoi_mask.sum()
                out_row.append(aoi_foreground)

            out.append(out_row)

        columns = ['frame', 'timestamp [sec]', 'full', *list(aois.keys())]
        df = pd.DataFrame(out, columns=columns)
        df.to_csv(out_path, index=False)

        man.register_multi_time('movement', {'path': str(out_path), 'categories': 'areas_of_interests'})
        logger.info('Registered "multi_time/movement" as an global artifact')