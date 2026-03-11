import cv2 as cv
import numpy as np
import argparse
import hand_detection
import logging
import zarr
import sys
import shutil

from pathlib import Path
from tqdm import tqdm
from helper.manifest_manager import ManifestManager

logger = logging.getLogger(__name__)

def setup_zarr_array(frame_size: tuple[float, float],
                     frame_count: int,
                     fps: float,
                     downsampling_spatial:float,
                     downsampling_temporal:float,
                     path: Path) -> zarr.Array:

    if path.is_dir():
        shutil.rmtree(path)

    frame_width, frame_height = frame_size

    out_fps = fps / downsampling_temporal
    out_frame_count = int(frame_count * out_fps / fps)
    out_frame_width = int(frame_width / downsampling_spatial)
    out_frame_height = int(frame_height / downsampling_spatial)

    z = zarr.create_array(
        store=path,
        shape=(out_frame_count+1, out_frame_height, out_frame_width),
        chunks=(16, out_frame_height, out_frame_width),
        dtype='uint8',
        compressors=zarr.codecs.BloscCodec(
            cname='zstd',
            clevel=1,
            shuffle=zarr.codecs.BloscShuffle.bitshuffle,
        ),
    )

    z.attrs['source_path'] = str(video_info['path'])
    z.attrs['source_fps'] = fps
    z.attrs['source_width'] = frame_width
    z.attrs['source_height'] = frame_height
    z.attrs['width'] = out_frame_width
    z.attrs['height'] = out_frame_height
    z.attrs['fps'] = out_fps

    return z

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--detect_shadows', action='store_true')
    parser.add_argument('--show_output', action='store_true')
    parser.add_argument('--store_video', action='store_true')
    parser.add_argument('--downsampling_spatial', type=int, default=1)
    parser.add_argument('--downsampling_temporal', type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    with ManifestManager(args.manifest, args.root_dir) as man:
        video_info = man.get_video('workspace')
        cap = cv.VideoCapture(video_info['path'])

        fps = cap.get(cv.CAP_PROP_FPS)
        frame_count = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

        out_path = args.root_dir / 'movement_store.zarr'

        z = setup_zarr_array((frame_width, frame_height),
                             frame_count, fps,
                             args.downsampling_spatial,
                             args.downsampling_temporal,
                             out_path)

        logger.info(f'Video Info: {frame_width}x{frame_height}, {fps} FPS, {frame_count} total frames')

        back_sub = cv.createBackgroundSubtractorKNN(history=3000, dist2Threshold=1000, detectShadows=args.detect_shadows)
        hand_detector = hand_detection.HandDetector(num_hands=10, model_asset_path='hand_landmarker_latest.task')

        if args.store_video:
            fourcc = cv.VideoWriter_fourcc(*'avc1')
            writer = cv.VideoWriter(str(args.root_dir / 'activity_knn.mp4'), fourcc=fourcc, fps=fps, frameSize=(frame_width, frame_height))


        with tqdm(total=z.shape[0], unit='frames', unit_scale=args.downsampling_temporal, disable=False) as t:
            while True:
                ret, img = cap.read()
                if not ret:
                    break

                pos_frame = int(cap.get(cv.CAP_PROP_POS_FRAMES))
                pos_msec = int(cap.get(cv.CAP_PROP_POS_MSEC))

                if pos_frame % args.downsampling_temporal != 0:
                    continue

                pos_out_frame = pos_frame // args.downsampling_temporal

                img = cv.resize(img, dsize=None, fx=1./args.downsampling_spatial,
                                fy=1./args.downsampling_spatial, interpolation=cv.INTER_AREA)

                detection_result = hand_detector.detect(img, pos_msec)
                hand_mask = hand_detection.mask_from_hand_landmarks(detection_result, img.shape[:2])
                fg_mask = back_sub.apply(img)

                frame_mask = (fg_mask == 255) & hand_mask
                out_mask = (255*frame_mask).astype(np.uint8)

                z[pos_out_frame] = out_mask

                if args.store_video:
                    out_frame = np.stack([out_mask, out_mask, out_mask], axis=2)
                    out_frame = cv.resize(out_frame, dsize=(frame_width, frame_height), interpolation=cv.INTER_AREA)
                    writer.write(out_frame)

                if args.show_output:
                    cv.imshow('Hand Landmarks', hand_detection.draw_landmarks_on_image(img, detection_result))
                    cv.imshow('Mask', out_mask)
                    cv.imshow('frame', img)

                if args.show_output and (0xff & cv.waitKey(1)) == ord('q'):
                    break

                t.update()

            man.register_source('movement_store', {'path': str(out_path),
                                                   'offset_sec': video_info['offset_sec']})
            logger.info('Registered "movement_store" as a source')

            cap.release()
            if args.store_video:
                writer.release()
