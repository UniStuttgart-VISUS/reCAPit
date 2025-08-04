import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import cv2 as cv
import pandas as pd
import numpy as np
import argparse
import hand_detection
import logging

from pathlib import Path
from tqdm import tqdm
from utils import get_aois, get_masks
from manifest_manager import ManifestManager


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--detect_shadows', action='store_true')
    parser.add_argument('--show_output', action='store_true')
    parser.add_argument('--store_video', action='store_true')
    parser.add_argument('--downsampling_factor', type=float, default=1)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    with ManifestManager(args.manifest) as man:
        cap = cv.VideoCapture(man.get_video('workspace')['path'])

        fps = cap.get(cv.CAP_PROP_FPS)
        frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

        back_sub = cv.createBackgroundSubtractorKNN(history=3000, dist2Threshold=1000, detectShadows=False)
        hand_detector = hand_detection.HandDetector(num_hands=10, model_asset_path='hand_landmarker_latest.task')

        if args.store_video:
            fourcc = cv.VideoWriter_fourcc(*'avc1')
            writer = cv.VideoWriter(str(args.out_dir / 'activity_knn.mp4'), fourcc=fourcc, fps=fps, frameSize=(frame_width, frame_height))

        aois = get_aois(man.get_areas_of_interests()['path'])
        masks = get_masks(aois, frame_width, frame_height)
        masks = {label: cv.resize(mask, fx=args.downsampling_factor, fy=args.downsampling_factor, dsize=None) for label, mask in masks.items()}

        out = []
        out_path = args.out_dir / 'movement.csv'

        with tqdm(total=frame_count, unit='frames', disable=False) as t:
            while True:
                ret, img = cap.read()
                if not ret:
                    print('EOF')
                    break

                img = cv.resize(img, dsize=None, fx=args.downsampling_factor, fy=args.downsampling_factor, interpolation=cv.INTER_AREA)
                pos_frame = int(cap.get(cv.CAP_PROP_POS_FRAMES))
                pos_msec = int(cap.get(cv.CAP_PROP_POS_MSEC))

                detection_result = hand_detector.detect(img, pos_msec)
                hand_mask = hand_detection.mask_from_hand_landmarks(detection_result, img.shape[:2])
                fg_mask = back_sub.apply(img)

                frame_mask = (fg_mask == 255) & hand_mask
                out_mask = (255*frame_mask).astype(np.uint8)
                
                if args.store_video:
                    out_frame = np.stack([out_mask, out_mask, out_mask], axis=2)
                    out_frame = cv.resize(out_frame, dsize=(frame_width, frame_height), interpolation=cv.INTER_AREA)
                    writer.write(out_frame)

                total_foreground = frame_mask.sum() / (img.shape[0]*img.shape[1])

                if args.show_output:
                    cv.imshow('Hand Landmarks', hand_detection.draw_landmarks_on_image(img, detection_result))    
                    cv.imshow('Mask', out_mask)    
                    cv.imshow('frame', img)

                out_row = [pos_frame, pos_msec*1e-3, total_foreground]

                for label, aoi_mask in masks.items():
                    fg_mask_aoi = frame_mask * aoi_mask
                    aoi_foreground = fg_mask_aoi.sum() / aoi_mask.sum()
                    out_row.append(aoi_foreground)

                out.append(out_row)

                if args.show_output and (0xff & cv.waitKey(1)) == ord('q'):
                    break

                t.update()

            columns = ['frame', 'timestamp [sec]', 'full'] + list(aois.keys())
            df = pd.DataFrame(out, columns=columns)
            df.to_csv(out_path, index=False)

            man.register_multi_time('movement', {'path': str(out_path), 'categories': 'areas_of_interests'})
            logging.info('Registered "multi_time/movement" as an global artifact')
            
            cap.release()
            if args.store_video:
                writer.release()