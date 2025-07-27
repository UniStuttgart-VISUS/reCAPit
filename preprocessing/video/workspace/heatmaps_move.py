import pandas as pd
import numpy as np
import argparse
import logging
import cv2 as cv
import pandas as pd
import json
import hand_detection

from tqdm import tqdm
from scipy.ndimage import correlate1d
from pathlib import Path
from utils import *
from movement import get_aois, get_merged_aois_masks


def mean_activity(cap, hand_detector, back_sub, aoi_mask, start_msec, end_msec, downscale_factor=.5, show_output=True):
    cap.set(cv.CAP_PROP_POS_MSEC, start_msec)
    pos_msec = start_msec

    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH)) 
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    reduced_width = int(width * downscale_factor) 
    reduced_height = int(height * downscale_factor)

    accu = np.zeros((height, width))
    count = 0

    while pos_msec < end_msec:
        ret, img = cap.read()
        pos_msec = int(cap.get(cv.CAP_PROP_POS_MSEC))

        if not ret:
            print('EOF')
            break

        img = cv.resize(img, dsize=(reduced_width, reduced_height), interpolation=cv.INTER_AREA)

        detection_result = hand_detector.detect(img, pos_msec)
        hand_mask = hand_detection.mask_from_hand_landmarks(detection_result, img.shape[:2])

        fg_mask = back_sub.apply(img)
        frame_mask = (fg_mask == 255) & hand_mask
        frame_mask = frame_mask * aoi_mask

        frame_mask = cv.resize(frame_mask.astype(float), dsize=(width, height), interpolation=cv.INTER_AREA)
        accu = accu + frame_mask
        count += 1

        if show_output:
            cv.imshow('FG Mask', cv.resize((255*frame_mask).astype(np.uint8), fx=0.5, fy=0.5, dsize=None, interpolation=cv.INTER_AREA))    
            cv.imshow('Hand Landmarks', hand_detection.draw_landmarks_on_image(img, detection_result))    
            cv.imshow('frame', img)
            cv.waitKey(1)

    cv.destroyAllWindows()
    return accu / count


def activity_heatmap(cap, aois, start_timestamps, end_timestamps, kernel_size, downscale_factor, show_output):
    kernel_1d = gaussian_kernel_1d(kernel_size)

    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH)) 
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    back_sub = cv.createBackgroundSubtractorKNN(history=3000, dist2Threshold=1000, detectShadows=False)
    hand_detector = hand_detection.HandDetector(num_hands=10, model_asset_path='hand_landmarker_latest.task')

    aoi_mask = get_merged_aois_masks(aois, width, height)
    aoi_mask = cv.resize(aoi_mask, fx=downscale_factor, fy=downscale_factor, dsize=None)

    for start_ts, end_ts in zip(start_timestamps, end_timestamps):
        activity = mean_activity(cap, hand_detector, back_sub, aoi_mask, int(start_ts * 1e3), int(end_ts * 1e3), downscale_factor=downscale_factor, show_output=show_output)
        temp = correlate1d(activity, weights=kernel_1d, axis=0, mode='reflect')
        yield correlate1d(temp, weights=kernel_1d, axis=1, mode='reflect')
    cap.release()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--delta_step_sec', type=float, required=False, default=30.)
    parser.add_argument('--kernel_size', type=int, required=False, default=211)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--show_output', action='store_true')
    args = parser.parse_args()

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        if 'areas_of_interests' not in meta['sources']:
            logging.error("Areas of interests are not specified in 'sources'!")
            exit(1)

        if 'videos' not in meta['sources'] and 'workspace' not in meta['sources']['videos']:
            logging.error("No workspace video specified in 'sources'!")
            exit(1)

        if 'video_overlay' not in meta['artifacts']:
            logging.info("Create video_overlay field in manifest")
            meta['artifacts']['video_overlay'] = {}

        root_dir = args.out_dir
        out_dir = root_dir / 'move'
        out_dir.mkdir(exist_ok=True, parents=True)

        aois = get_aois(meta['sources']['areas_of_interests']['path'])

        cap = cv.VideoCapture(meta['sources']['videos']['workspace']['path'])
        dur_sec = int(cap.get(cv.CAP_PROP_FRAME_COUNT) / cap.get(cv.CAP_PROP_FPS)) 

        start_timestamps = np.arange(0, dur_sec, args.delta_step_sec)
        end_timestamps = start_timestamps + args.delta_step_sec - 1e-1

        filenames = [f'move/{n:04d}.npy' for n in range(len(start_timestamps))]
        heatmaps = activity_heatmap(cap, aois, start_timestamps, end_timestamps, kernel_size=args.kernel_size, downscale_factor=.5, show_output=args.show_output)

        df = pd.DataFrame(data=zip(filenames, start_timestamps, end_timestamps), columns=('filename', 'start timestamp [sec]', 'end timestamp [sec]'))
        df.to_csv(root_dir / 'move.csv', index=False)

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

        meta['artifacts']['video_overlay']['movement'] = {'path': str(args.out_dir / 'move.csv')}
        f.seek(0)
        json.dump(meta, f, indent=4)