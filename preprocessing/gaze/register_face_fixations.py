import cv2
import sys
import argparse
import logging
import numpy as np
import pandas as pd
import insightface
import warnings

from itertools import chain
from pathlib import Path
from tqdm import tqdm
from pandas import DataFrame
from helper.manifest_manager import ManifestManager, Recording
from eye_tracking_recording import eye_tracking_recording_factory

import utils
from utils import remove_time_offset, trim

logger = logging.getLogger(__name__)

class FaceDetection:
    """
    A class that is used for face detection

    """
    def __init__(
        self,
        video_path: Path,
        fixations_data: pd.DataFrame,
        output_folder: Path,
        show_output: bool,
    ):
        self.model = self.get_model()
        self.video_path = video_path
        self.output_folder = output_folder
        self.fixations_data = fixations_data
        self.show_output = show_output
        self.ref_faces = {}

    def get_model(self):
        model = insightface.app.FaceAnalysis(providers=['CUDAExecutionProvider'])
        model.prepare(ctx_id=0, det_size=(640, 640))
        return model

    def add_reference_face(self, rec: Recording) -> None:
        """Load reference face embeddings from a directory of images."""
        face_embeddings = []
        faces_dir = Path(rec.get_source('faces')['path'])

        for img_path in faces_dir.iterdir():
            if img_path.suffix in ('.jpg', '.png'):
                img = cv2.imread(str(img_path))
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                faces = self.model.get(img_rgb)

                if faces and len(faces) == 1:
                    face = faces[0]
                    embedding = face.embedding
                    face_embeddings.append(
                        {'file_name': img_path.stem, 'embeddings': embedding},
                    )
                elif faces:
                    msg = f'More than one face detected in {img_path}'
                    raise ValueError(msg)
                else:
                    msg = f'No face detected in {img_path}'
                    raise ValueError(msg)

        self.ref_faces[rec.rec_id] = face_embeddings


    def match_face(self, target_embedding: np.ndarray,
                   exclude_ids: list=[]) -> tuple[str, float]:
        """Return the name and similarity score for the best-matching reference face."""
        max_similarity = -1
        matched_file_name = 'Unknown'
        matched_rec_id = '-1'

        for rec_id, face_embeddings in self.ref_faces.items():
            similarities = ([utils.calculate_similarity(target_embedding, fe['embeddings'])
                             for fe in face_embeddings])

            max_sim = np.max(similarities)

            if max_sim > max_similarity and rec_id not in exclude_ids:
                max_similarity = max_sim
                matched_rec_id = rec_id
                matched_file_name = face_embeddings[np.argmax(similarities)]['file_name']

        return matched_rec_id, matched_file_name, max_similarity

    def _map_frame_faces(
        self,
        frame: np.ndarray,
        faces: list,
        gaze_x: int,
        gaze_y: int,
    ) -> list[dict]:
        """Process all detected faces in a single frame and return fixation records."""
        matches = []
        for face in faces:
            bbox = face.bbox.astype(int)
            bbox = utils.enlarge_bbox(bbox, self._bbox_scale_h, self._bbox_scale_v)
            matched_rec_id, matched_name, detection_conf = self.match_face(face.embedding)

            gaze_bbox_dist = utils.distance_face_bbox_gaze(bbox, gaze_x, gaze_y)
            gaze_bbox_intersect = gaze_bbox_dist <= self._gaze_radius

            if self.show_output:
                utils.draw_bbox_on_video(frame, bbox, f'{matched_rec_id} ({matched_name})', gaze_bbox_intersect)

            if gaze_bbox_intersect:
                x_min, y_min, x_max, y_max = bbox
                matches.append({
                    'label': matched_rec_id,
                    'name': matched_name,
                    'abs_x': gaze_x,
                    'abs_y': gaze_y,
                    'rel_x': (gaze_x - x_min) / (x_max - x_min),
                    'rel_y': (gaze_y - y_min) / (y_max - y_min),
                    'confidence_spatial': 1 - gaze_bbox_dist / self._gaze_radius,
                    'confidence_detection': detection_conf,
                })
        return matches

    def map_fixations(
        self,
        gaze_radius: int = 25,
        bbox_scale_horizontal: float = 1.0,
        bbox_scale_vertical: float = 1.0,
    ) -> DataFrame:
        """Detect faces in the video and map fixations to detected faces."""
        self._gaze_radius = gaze_radius
        self._bbox_scale_h = bbox_scale_horizontal
        self._bbox_scale_v = bbox_scale_vertical

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error('Could not open video: %s', self.video_path)
            return DataFrame()

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fix_count = len(self.fixations_data.index)
        mapped_fix = []
        curr_fix_idx = 0

        while cap.isOpened() and curr_fix_idx < fix_count:
            ret, frame = cap.read()
            if not ret:
                break

            frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            curr_fix = self.fixations_data.iloc[curr_fix_idx]

            if frame_pos == curr_fix['frame']:
                logger.info('Processed fixation: %i out of %i', (curr_fix_idx + 1), fix_count)

                fix_id = int(curr_fix['fixation id'])
                fix_x = int(curr_fix['fixation x [px]'])
                fix_y = int(curr_fix['fixation y [px]'])

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                faces = self.model.get(rgb_frame)
                matches = self._map_frame_faces(frame, faces, fix_x, fix_y)

                # Sort matches by geometric mean between spatial and detection confidence
                # Hightest at first index
                matches.sort(key=lambda m: m['confidence_spatial']*m['confidence_detection'],
                             reverse=True)

                if len(matches) > 0:
                    out = matches[0]
                    mapped_fix.append({'start timestamp [sec]': curr_fix['start timestamp [sec]'],
                                       'end timestamp [sec]': curr_fix['end timestamp [sec]'],
                                       'event data': f'looks at {out["label"]}',
                                       'event type': 'attention',
                                       'event subtype': out['label']})

                if self.show_output:
                    progress = frame_pos / total_frames
                    utils.draw_gaze(frame, fix_x, fix_y)
                    utils.draw_coord_label(frame, 'Fixation Id', fix_id, fix_id)
                    utils.draw_progress_bar(frame, progress)
                    cv2.imshow('face_bbox', frame)
                    if cv2.waitKey(0) & 0xFF == ord('q'):
                        break

                curr_fix_idx += 1
            elif frame_pos > curr_fix['frame']:
                msg = 'Fixations are not sorted by frames'
                raise RuntimeError(msg)

        cap.release()
        if self.show_output:
            cv2.destroyAllWindows()

        return DataFrame.from_records(mapped_fix)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Map gaze fixations to detected faces using manifest-defined inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--root_dir', type=Path, required=True)
    parser.add_argument('--rec_id', type=str, required=True)
    parser.add_argument('--device_name', type=str, required=True)
    parser.add_argument('--bbox_scale_horizontal', type=float, default=1.0)
    parser.add_argument('--bbox_scale_vertical', type=float, default=1.0)
    parser.add_argument('--gaze_radius', type=float, default=25.0)
    parser.add_argument('--show_output', action='store_true', help='Display video during processing')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    with ManifestManager(args.manifest, args.root_dir) as man:
        rec = man.get_recording(args.rec_id)

        if not rec.has_source('faces'):
            logger.error('Recording %s has no "faces" source', args.rec_id)
            sys.exit()

        if not rec.has_source('gaze'):
            logger.error('Recording %s has no "gaze" source', args.rec_id)
            sys.exit()

        faces_dir = Path(rec.get_source('faces')['path'])
        gaze_info = rec.get_source('gaze')

        et_recording = eye_tracking_recording_factory(
            Path(gaze_info['path']), args.device_name,
        )

        video_path = et_recording.get_scene_camera_video()
        fixations_data = et_recording.read_fixations()
        rec_info = et_recording.get_recording_info()
        duration_sec = man.get_duration_sec()

        rec_dir = args.root_dir / rec.rec_id
        rec_dir.mkdir(exist_ok=True, parents=False)

        face_detection = FaceDetection(
            video_path=video_path,
            fixations_data=fixations_data,
            output_folder=rec_dir,
            show_output=args.show_output,
        )

        for other_rec in man.get_recordings():
            if not other_rec.has_source('faces'):
                logger.error('Recording "%s" has no face directory!', other_rec.rec_id)
                continue

            if other_rec.rec_id != rec.rec_id:
                logger.info('Added faces dir of recording %s', other_rec.rec_id)
                face_detection.add_reference_face(other_rec)

        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
            mapped_fix = face_detection.map_fixations(
                args.gaze_radius,
                args.bbox_scale_horizontal,
                args.bbox_scale_vertical,
            )

            out_path = rec_dir / 'face_fixations.csv'

            remove_time_offset(mapped_fix, rec_info['offset_sec'] + gaze_info['offset_sec'])
            mapped_fix = trim(mapped_fix, duration_sec)
            mapped_fix.to_csv(out_path, index=False, float_format='%.3f')

            rec.register_artifact('face_fixations', {'path': str(out_path), 'offset_sec': 0.0})
            logger.info('Mapped fixations to faces of recording %s', rec.rec_id)
