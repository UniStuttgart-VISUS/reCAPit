import cv2 as cv
import pandas as pd
import shapely
import json
import numpy as np
import argparse
import hand_detection

from shapely.ops import unary_union
from pathlib import Path
from tqdm import tqdm


def get_aois(aoi_config_path):
    with open(aoi_config_path, 'r') as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])

        return shapes_geom


# TODO This is rather slow since we iterate over all pixels in polygons bounding box
def get_masks(aois, width, height):
    masks = {}
    for label, shape in tqdm(aois.items()):
        minx, miny, maxx, maxy = shape.bounds
        masks[label] = np.zeros((height, width), dtype=float)

        for x in range(int(minx), int(maxx)):
            for y in range(int(miny), int(maxy)):
                masks[label][y, x] = aois[label].contains(shapely.Point(x, y))
    return masks

def get_merged_aois_masks(aois, width, height):
    mask = np.zeros((height, width), dtype=bool)
    merged_polygon = unary_union(list(aois.values()))
    convex_hull = merged_polygon.convex_hull

    minx, miny, maxx, maxy = convex_hull.bounds

    for x in range(int(minx), int(maxx)):
        for y in range(int(miny), int(maxy)):
            mask[y, x] = convex_hull.contains(shapely.Point(x, y))

    return mask.astype(float)

    """
    for label, shape in tqdm(aois.items()):
        minx, miny, maxx, maxy = shape.bounds

        for x in range(int(minx), int(maxx)):
            for y in range(int(miny), int(maxy)):
                mask[y, x] = np.logical_or(mask[y, x], aois[label].contains(shapely.Point(x, y)))
    """
    return mask.astype(float)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta', type=Path, required=True)
    parser.add_argument('--out_dir', type=Path, required=True)
    parser.add_argument('--detect_shadows', action='store_true')
    parser.add_argument('--show_output', action='store_true')
    parser.add_argument('--store_video', action='store_true')
    parser.add_argument('--downsampling_factor', type=float, default=1)
    args = parser.parse_args()

    with open(args.meta, 'r+') as f:
        meta = json.load(f)

        cap = cv.VideoCapture(meta['sources']['videos']['workspace']['path'])

        fps = cap.get(cv.CAP_PROP_FPS)
        frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

        back_sub = cv.createBackgroundSubtractorKNN(history=3000, dist2Threshold=1000, detectShadows=False)
        hand_detector = hand_detection.HandDetector(num_hands=10, model_asset_path='hand_landmarker_latest.task')

        if args.store_video:
            fourcc = cv.VideoWriter_fourcc(*'avc1')
            writer = cv.VideoWriter(str(args.out_dir / 'activity_knn.mp4'), fourcc=fourcc, fps=fps, frameSize=(frame_width, frame_height))

        aois = get_aois(meta['sources']['areas_of_interests']['path'])
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

            meta['artifacts']['time']['movement']= str(out_path)
            
            f.seek(0)
            json.dump(meta, f, indent=4)
        
            cap.release()
            if args.store_video:
                writer.release()