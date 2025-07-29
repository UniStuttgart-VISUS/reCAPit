import pandas as pd
import numpy as np
import argparse
import cv2 as cv
import matplotlib.cm as cm
import json
import logging

from tqdm import tqdm
from pathlib import Path
from utils import *


def create_heatmap_splatting(pos_x, pos_y, weights, size, kernel_size=151):
    heatmap = np.zeros(size)
    ksh = kernel_size // 2
    
    kernel = gaussian_kernel(kernel_size)
    heatmap = np.pad(heatmap, ((ksh, ksh), (ksh, ksh)))

    for x, y, w in zip(pos_x, pos_y, weights):
        heatmap[y: y+2*ksh+1, x: x+2*ksh+1] += kernel * w

    heatmap = heatmap[ksh: -ksh, ksh: -ksh]
    return heatmap


def fix_in_range(recordings, from_time_sec, to_time_sec):
    fix_pos_x = []
    fix_pos_y = []
    fix_dur_ms = []

    for rec in recordings:
        if 'mapped_fixations' not in rec['artifacts']:
            continue

        surface_fix = pd.read_csv(rec['artifacts']['mapped_fixations']['path'])
        surface_fix['duration [ms]'] = 1e3 * (surface_fix['end timestamp [sec]'] - surface_fix['start timestamp [sec]'])

        within_range = (surface_fix['start timestamp [sec]'] >= from_time_sec) & (surface_fix['end timestamp [sec]'] <= to_time_sec) 
        surface_fix = surface_fix[within_range]

        dur_ms = surface_fix['duration [ms]'].astype(int)
        pos_x = surface_fix['event data'].map(lambda d: int(d.split(';')[0]))
        pos_y = surface_fix['event data'].map(lambda d: int(d.split(';')[1]))

        fix_pos_x.extend(pos_x)
        fix_pos_y.extend(pos_y)
        fix_dur_ms.extend(dur_ms)

    fix_pos_x = np.array(fix_pos_x)
    fix_pos_y = np.array(fix_pos_y)
    fix_dur_ms = np.array(fix_dur_ms)

    return fix_pos_x, fix_pos_y, fix_dur_ms

    
def gaze_heatmap(cap, recordings, start_timestamps, end_timestamps, kernel_size):
    frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH)) 
    frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    for start_ts, end_ts in zip(start_timestamps, end_timestamps):
        fix_pos_x, fix_pos_y, fix_dur_ms = fix_in_range(recordings, start_ts, end_ts)

        fix_pos_x = fix_pos_x.clip(0, frame_width-1)
        fix_pos_y = fix_pos_y.clip(0, frame_height-1)
        weights = fix_dur_ms / 100

        yield create_heatmap_splatting(fix_pos_x, fix_pos_y, weights, (frame_height, frame_width), kernel_size=kernel_size) 

    cap.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--delta_step_sec', type=float, required=False, default=30.)
    parser.add_argument('--kernel_size', type=int, required=False, default=211)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--show_output', action='store_true')
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with open(args.manifest, 'r+') as f:
        manifest = json.load(f)

        if 'videos' not in manifest['sources'] and 'workspace' not in manifest['sources']['videos']:
            logging.error("No workspace video specified in 'sources'!")
            exit(1)

        if 'video_overlay' not in manifest['artifacts']:
            logging.info("Create video_overlay field in manifest")
            manifest['artifacts']['video_overlay'] = {}

        root_dir = args.out_dir
        out_dir = root_dir / 'gaze'
        out_dir.mkdir(exist_ok=True, parents=True)

        cap = cv.VideoCapture(manifest['sources']['videos']['workspace']['path'])
        dur_sec = int(cap.get(cv.CAP_PROP_FRAME_COUNT) / cap.get(cv.CAP_PROP_FPS)) 

        start_timestamps = np.arange(0, dur_sec, args.delta_step_sec)
        end_timestamps = start_timestamps + args.delta_step_sec
        filenames = [f'gaze/{n:04d}.npy' for n in range(len(start_timestamps))]
        heatmaps = gaze_heatmap(cap, manifest['recordings'], start_timestamps, end_timestamps, kernel_size=args.kernel_size)

        df = pd.DataFrame(data=zip(filenames, start_timestamps, end_timestamps), columns=('filename', 'start timestamp [sec]', 'end timestamp [sec]'))
        df.to_csv(root_dir / 'gaze.csv', index=False)

        with tqdm(total=len(start_timestamps), desc='compute heatmaps', unit='heatmap') as t:
            for heatmap, filename in zip(heatmaps, filenames):
                heatmap = heatmap.astype(np.float16)
                np.save(root_dir / filename, heatmap)

                if args.show_output:
                    img = create_heatmap_img(heatmap, colormap=cm.get_cmap('plasma', 9))
                    cv.imshow('heatmap', img)
                    key = cv.waitKey(1)
                    if key & 0xff == ord('q'):
                        break
                t.update()

        manifest['artifacts']['video_overlay']['attention'] = {'path': str(args.out_dir / 'gaze.csv')}
        logging.info('Registered "video_overlay/attention" as an global artifact')

        f.seek(0)
        json.dump(manifest, f, indent=4)

