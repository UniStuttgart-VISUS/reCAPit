import cv2
import numpy as np
import argparse
import pandas as pd
import sys
from marker_mapper import MarkerMapper

from helper.manifest_manager import ManifestManager
from pathlib import Path
from eye_tracking_recording import eye_tracking_recording_factory, EyeTrackingRecording

from utils import draw_gaze, draw_tags, draw_coord_label, draw_progress_bar, remove_time_offset, trim
from pupil_apriltags import Detector


def calc_surface_fixations(recording: EyeTrackingRecording,
                           at_detector: Detector, sm: MarkerMapper,
                           show_output: bool = False) -> pd.DataFrame:

    curr_fix_idx = 0
    mapped_fix = []

    cap = cv2.VideoCapture(recording.get_scene_camera_video())
    camera_intr = recording.read_camera_intrinsics()
    fix = recording.read_fixations()
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while cap.isOpened() and curr_fix_idx < len(fix.index):
        ret, img = cap.read()
        if not ret:
            break

        frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        curr_fix = fix.iloc[curr_fix_idx]

        undistorted = cv2.undistort(img, camera_intr['K'], camera_intr['D'])
        undistorted_gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
        tags_undistorted = at_detector.detect(undistorted_gray)
        found_mapping, _ = sm.update_transform(tags_undistorted)

        if frame_pos == curr_fix['frame']:
            fx, fy = curr_fix[['fixation x [px]', 'fixation y [px]']]
            sx, sy = sm.map_coord(fx, fy) if found_mapping else (-1, -1)

            mapped_fix.append((curr_fix['start timestamp [sec]'],
                               curr_fix['end timestamp [sec]'],
                               sm.on_surface(sx, sy),
                               int(sx), int(sy)))
            curr_fix_idx += 1
        elif frame_pos > fix.iloc[curr_fix_idx]['frame']:
            msg = 'Fixations are not sorted by frames'
            raise RuntimeError(msg)

        if show_output:
            fx, fy = curr_fix[['fixation x [px]', 'fixation y [px]']]
            progress = frame_pos / frame_count

            if found_mapping:
                sx, sy = sm.map_coord(fx, fy)
                warped = sm.map_frame(undistorted)
                draw_gaze(warped, sx, sy)
                draw_coord_label(warped, 'dst', sx, sy)
                cv2.imshow('dst', warped)

            draw_gaze(undistorted, fx, fy)
            draw_tags(undistorted, tags_undistorted)
            draw_coord_label(undistorted, 'src', fx, fy)
            draw_progress_bar(undistorted, progress)

            cv2.imshow('src', undistorted)

            if 0xff & cv2.waitKey(1) == ord('q'):
                break

    cv2.destroyAllWindows()
    cap.release()

    return pd.DataFrame.from_records(mapped_fix, columns=['start timestamp [sec]', 'end timestamp [sec]', 
                                                          'within_surface', 'mapped x [px]', 'mapped y [px]'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--rec_id', type=str, required=True)
    parser.add_argument('--min_tags', type=int, required=True)
    parser.add_argument('--device_name', type=str, required=True)
    parser.add_argument('--april_tag_family', type=str, choices=['tag36h11'], required=True)
    parser.add_argument('--show_output', action='store_true', help='Displays streamed gaze/video data')
    args = parser.parse_args()

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec = man.get_recording(args.rec_id)
        if not rec.has_source('gaze'):
            sys.exit()

        workspace_video = man.get_video('workspace')
        gaze_info = rec.get_source('gaze')
        rec_dir = args.root_dir / rec.rec_id
        rec_dir.mkdir(exist_ok=True, parents=False)
        duration_sec = man.get_duration_sec()

        at_detector = Detector(
            families=args.april_tag_family,
            nthreads=4,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )
        ref_tags, ref_size = MarkerMapper.find_reference_tags(workspace_video['path'],
                                                              at_detector, args.min_tags,
                                                              max_trials=30,
                                                              show_output=args.show_output)
        sm = MarkerMapper(ref_tags, ref_size)

        et_recording = eye_tracking_recording_factory(Path(gaze_info['path']), args.device_name)
        rec_info = et_recording.get_recording_info()

        surface_fixations = calc_surface_fixations(et_recording, at_detector, sm,
                                                   show_output=args.show_output)


        remove_time_offset(surface_fixations, rec_info['offset_sec'] + gaze_info['offset_sec'])
        surface_fixations = trim(surface_fixations, duration_sec)

        out_path_surf = rec_dir / 'surface_fixations.csv'
        surface_fixations.to_csv(out_path_surf, index=None)
        rec.register_artifact('surface_fixations', {'path': str(out_path_surf), 'offset_sec': 0.0})