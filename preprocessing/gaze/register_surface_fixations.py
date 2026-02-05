import cv2
import numpy as np
import argparse
import pandas as pd
import sys
from marker_mapper import MarkerMapper

from helper.manifest_manager import ManifestManager
from pathlib import Path
from eyetracking_device import device_factory, EyeTrackingDevice
from map_fixations import map_fixations_on_aois

from utils import draw_gaze, draw_tags
from pupil_apriltags import Detector


def calc_surface_fixations(device: EyeTrackingDevice,
                      at_detector: Detector, sm: MarkerMapper,
                      show_output: bool = False) -> pd.DataFrame:

    curr_fix_idx = 0
    mapped_fix = []

    cap = cv2.VideoCapture(device.get_scene_camera_video())
    rec_info = device.get_recording_info()
    camera_intr = device.read_camera_intrinsics()
    fix = device.read_fixations()

    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            break

        frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        curr_fix = fix.iloc[curr_fix_idx]

        if curr_fix_idx > 15:
            break

        undistorted = cv2.undistort(img, camera_intr['K'], camera_intr['D'])
        undistorted_gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
        tags_undistorted = at_detector.detect(undistorted_gray)
        found_mapping, _ = sm.update_transform(tags_undistorted)

        if frame_pos == curr_fix['frame']:
            fx, fy = curr_fix[['fixation x [px]', 'fixation y [px]']]
            sx, sy = sm.map_coord(fx, fy) if found_mapping else (-1, -1)

            mapped_fix.append((sm.on_surface(sx, sy), sx, sy))
            print(mapped_fix[-1])
            curr_fix_idx += 1
        elif frame_pos > fix.iloc[curr_fix_idx]['frame']:
            msg = 'Fixations are not sorted by frames'
            raise RuntimeError(msg)

        if show_output:
            fx, fy = fix.iloc[curr_fix_idx][['fixation x [px]', 'fixation y [px]']]

            draw_gaze(undistorted, fx, fy)
            draw_tags(undistorted, tags_undistorted)

            if found_mapping:
                cv2.imshow('warped', sm.map_frame(undistorted))

            #cv2.imshow('original', img)
            cv2.imshow('undistorted', undistorted)

            if 0xff & cv2.waitKey(1) == ord('q'):
                break

    surface_fixations = pd.DataFrame.from_records(mapped_fix, columns=['within_surface', 'mapped x [px]', 'mapped y [px]'])
    surface_fixations['start timestamp [sec]'] = 1e-9 * fix['start timestamp [ns]'] - rec_info['offset_sec']
    surface_fixations['end timestamp [sec]'] = 1e-9 * fix['end timestamp [ns]'] - rec_info['offset_sec']
    surface_fixations['mapped x [px]'] = surface_fixations['mapped x [px]'].astype(int)
    surface_fixations['mapped y [px]'] = surface_fixations['mapped y [px]'].astype(int)
    return surface_fixations


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--rec_id', type=str, required=True)
    parser.add_argument('--min_tags', type=int, required=True)
    parser.add_argument('--april_tag_family', type=str, choices=['tag36h11'])
    parser.add_argument('--show_output', action='store_true', help='Displays streamed gaze/video data')
    args = parser.parse_args()

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec = man.get_recording(args.rec_id)
        if 'gaze' not in rec['sources']:
            sys.exit()

        workspace_video = man.get_video('workspace')
        gaze_info = rec['sources']['gaze']
        rec_dir = args.root_dir / rec['id']
        rec_dir.mkdir(exist_ok=True, parents=False)

        at_detector = Detector(
            families=args.april_tag_family,
            nthreads=1,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )
        ref_tags, ref_size = MarkerMapper.find_reference_tags(workspace_video['path'],
                                                              at_detector, args.min_tags,
                                                              show_output=args.show_output)
        sm = MarkerMapper(ref_tags, ref_size)

        device = device_factory(Path(gaze_info['path']), gaze_info['hardware'])
        surface_fixations = calc_surface_fixations(device, at_detector, sm,
                                                    show_output=args.show_output)

        surface_fixations['start timestamp [sec]'] = surface_fixations['start timestamp [sec]'] - gaze_info['offset_sec']
        surface_fixations['end timestamp [sec]'] = surface_fixations['end timestamp [sec]'] - gaze_info['offset_sec']

        out_path_surf = rec_dir / 'surface_fixations.csv'
        surface_fixations.to_csv(out_path_surf, index=None)
        rec['artifacts']['surface_fixations'] = {'path': str(out_path_surf), 'categories': 'areas_of_interests'}