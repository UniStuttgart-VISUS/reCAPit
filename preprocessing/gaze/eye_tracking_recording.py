import pandas as pd
import numpy as np
import json
from pathlib import Path
from abc import ABC, abstractmethod

class EyeTrackingRecording(ABC):
    """."""

    @abstractmethod
    def read_fixations(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def read_camera_intrinsics(self) -> dict[str, np.ndarray]:
        pass

    @abstractmethod
    def get_scene_camera_video(self) -> Path:
        pass

    @abstractmethod
    def get_recording_info(self) -> dict[str, any]:
        pass


class PupilInvisibleRecording(EyeTrackingRecording):
    def __init__(self, rec_dir: Path) -> None:
        super().__init__()
        self.rec_dir = rec_dir
        self.export_dir = rec_dir / 'export'

        if not self.export_dir.is_dir():
            raise ValueError

    def read_fixations(self) -> pd.DataFrame:
        world = pd.read_csv(self.export_dir / 'world.csv')
        world = world.reset_index().rename(columns={'index': 'frame'})

        fix = pd.read_csv(self.export_dir / 'fixations.csv')
        fix['center timestamp [ns]'] = ((fix['start timestamp [ns]'] + fix['end timestamp [ns]']) // 2).astype(int)
        fix = pd.merge_asof(fix, world, left_on='center timestamp [ns]', right_on='timestamp [ns]', direction='nearest')

        fix['start timestamp [sec]'] = 1e-9 * fix['start timestamp [ns]']
        fix['end timestamp [sec]'] = 1e-9 * fix['end timestamp [ns]']

        return fix.drop(columns=['start timestamp [ns]', 'end timestamp [ns]', 'center timestamp [ns]'])


    def get_recording_info(self) -> dict[str, any]:
        info_path_option_2 = self.rec_dir / 'info.json'
        info_path_option_1 = self.rec_dir / 'info.invisible.json'

        if info_path_option_1.exists():
            info_path = info_path_option_1
        elif info_path_option_2.exists():
            info_path = info_path_option_2
        else:
            raise ValueError

        with open(info_path) as f:
            info = json.load(f)
            return {'offset_sec': 1e-9*info['start_time'],
                    'duration_sec': 1e-9*info['duration'],
                    'id': info['recording_id']}

    def read_camera_intrinsics(self) -> dict[str, np.ndarray]:
        dtype=np.dtype(
            [
                ('serial', '5a'),
                ('scene_camera_matrix', '(3,3)d'),
                ('scene_distortion_coefficients', '8d'),
                ('rotation_matrix', '(3,3)d'),
            ],
        )

        data = np.fromfile(self.rec_dir / 'calibration.bin', dtype=dtype, count=1)

        return {
            # Camera Matrix: 3x3
            'K': np.array(data[0][1]).reshape((3,3)),
            # Distortion coefficients: 8
            'D': np.array(data[0][2]),
        }

    def get_scene_camera_video(self) -> Path:
        matching_files = [f for f in Path(self.rec_dir).glob('*world*') if f.suffix.lower() == '.mp4']

        if len(matching_files) != 1:
            raise ValueError

        return matching_files[0]

class PupilNeonRecording(EyeTrackingRecording):
    def __init__(self, rec_dir: Path) -> None:
        super().__init__()
        self.rec_dir = rec_dir
        self.export_dir = rec_dir / 'export'

        if not self.export_dir.is_dir():
            raise ValueError

    def read_fixations(self) -> pd.DataFrame:
        world = pd.read_csv(self.export_dir / 'world.csv')
        world = world.reset_index().rename(columns={'index': 'frame'})

        fix = pd.read_csv(self.export_dir / 'fixations.csv')
        fix['center timestamp [ns]'] = ((fix['start timestamp [ns]'] + fix['end timestamp [ns]']) // 2).astype(int)
        fix = pd.merge_asof(fix, world, left_on='center timestamp [ns]', right_on='timestamp [ns]', direction='nearest')

        fix['start timestamp [sec]'] = 1e-9 * fix['start timestamp [ns]']
        fix['end timestamp [sec]'] = 1e-9 * fix['end timestamp [ns]']

        return fix.drop(columns=['start timestamp [ns]', 'end timestamp [ns]', 'center timestamp [ns]'])

    def get_recording_info(self) -> dict[str, any]:
        info_path_option_2 = self.rec_dir / 'info.json'
        info_path_option_1 = self.rec_dir / 'info.neon.json'

        if info_path_option_1.exists():
            info_path = info_path_option_1
        elif info_path_option_2.exists():
            info_path = info_path_option_2
        else:
            raise ValueError

        with open(info_path) as f:
            info = json.load(f)
            return {'offset_sec': 1e-9*info['start_time'],
                    'duration_sec': 1e-9*info['duration'],
                    'id': info['recording_id']}

    def read_camera_intrinsics(self) -> dict[str, np.ndarray]:
        dtype=np.dtype(
            [
                ('version', 'u1'),
                ('serial', '6a'),
                ('scene_camera_matrix', '(3,3)d'),
                ('scene_distortion_coefficients', '8d'),
                ('scene_extrinsics_affine_matrix', '(4,4)d'),
                ('right_camera_matrix', '(3,3)d'),
                ('right_distortion_coefficients', '8d'),
                ('right_extrinsics_affine_matrix', '(4,4)d'),
                ('left_camera_matrix', '(3,3)d'),
                ('left_distortion_coefficients', '8d'),
                ('left_extrinsics_affine_matrix', '(4,4)d'),
                ('crc', 'u4'),
            ],
        )

        data = np.fromfile(self.rec_dir / 'calibration.bin', dtype=dtype, count=1)

        return {
            # Camera Matrix: 3x3
            'K': np.array(data[0][2]).reshape((3,3)),
            # Distortion coefficients: 8
            'D': np.array(data[0][3]),
        }

    def get_scene_camera_video(self) -> Path:
        matching_files = [f for f in Path(self.rec_dir).glob('*Scene*') if f.suffix.lower() == '.mp4']

        if len(matching_files) != 1:
            raise ValueError

        return matching_files[0]

def eye_tracking_recording_factory(rec_dir: str, device_name: str) -> EyeTrackingRecording:
    if device_name == 'pupil-labs-invisible':
        return PupilInvisibleRecording(rec_dir)
    if device_name == 'pupil-labs-neon':
        return PupilNeonRecording(rec_dir)

    msg = f'Unknown device: {device_name}'
    raise ValueError(msg)
