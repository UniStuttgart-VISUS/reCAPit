from pathlib import Path
import json
from typing import Any, TYPE_CHECKING
from types import TracebackType

if TYPE_CHECKING:
    from io import TextIOWrapper


class ManifestError(Exception):
    pass


class ManifestManager:
    def __init__(self, path: Path, root_dir: Path, read_only: bool = False) -> None:
        self.file: TextIOWrapper | None = None
        self.root_dir: Path = root_dir
        self.path: Path = path
        self.read_only: bool = read_only
        self.manifest_json: dict[str, Any] = {}

    def __enter__(self) -> 'ManifestManager':
        self.file = open(self.path, 'r' if self.read_only else 'r+')
        self.manifest_json = json.load(self.file)
        if not self.check_integrity():
            msg = 'Manifest integrity check failed'
            raise ManifestError(msg)
        return self

    def __exit__(self, exc_type: type | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        if not self.read_only:
            if not self.check_integrity():
                msg = 'Manifest integrity check failed'
                raise ManifestError(msg)
            self.file.seek(0)
            json.dump(self.manifest_json, self.file, indent=4)
            self.file.truncate()
        self.file.close()

    def load(self) -> dict[str, Any]:
        with open(self.path, encoding='utf-8') as f:
            self.manifest_json = json.load(f)
        if not self.check_integrity():
            msg = 'Manifest integrity check failed'
            raise ManifestError(msg)
        return self.manifest_json

    def save(self) -> None:
        if self.read_only:
            msg = 'Cannot save in read-only mode'
            raise RuntimeError(msg)
        if not self.check_integrity():
            msg = 'Manifest integrity check failed'
            raise ManifestError(msg)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest_json, f, indent=4)

    def check_integrity(self) -> bool:
        if 'language' not in self.manifest_json or not isinstance(self.manifest_json['language'], str) or self.manifest_json['language'] not in ManifestManager.supported_languages():
            return False

        if 'duration_sec' not in self.manifest_json or not isinstance(self.manifest_json['duration_sec'], (int, float)):
            return False

        if 'roles' not in self.manifest_json or not isinstance(self.manifest_json['roles'], list):
            return False

        if 'recordings' in self.manifest_json and not isinstance(self.manifest_json['recordings'], list):
            return False

        return not ('artifacts' in self.manifest_json and not isinstance(self.manifest_json['artifacts'], dict))

    def get_duration_sec(self) -> int | float:
        try:
            return self.manifest_json['duration_sec']
        except KeyError as e:
            msg = 'No duration specified in manifest'
            raise ManifestError(msg) from e

    def get_language(self) -> str:
        try:
            return self.manifest_json['language']
        except KeyError as e:
            msg = 'No language specified in manifest'
            raise ManifestError(msg) from e

    def get_roles(self) -> list[str]:
        try:
            return self.manifest_json['roles']
        except KeyError as e:
            msg = 'No roles specified in manifest'
            raise ManifestError(msg) from e

    def get_artifact(self, name: str) -> Any:
        try:
            artifacts = self._artifacts()
            return artifacts[name]
        except KeyError as e:
            msg = f'{name} is not a registered artifact'
            raise ManifestError(msg) from e

    def _artifacts(self) -> dict[str, Any]:
        try:
            return self.manifest_json['artifacts']
        except KeyError as e:
            msg = 'No registered artifacts in manifest'
            raise ManifestError(msg) from e

    def get_source(self, name: str) -> Any:
        try:
            sources = self._sources()
            return sources[name]
        except KeyError as e:
            msg = f'{name} is not a source'
            raise ManifestError(msg) from e

    def _sources(self) -> dict[str, Any]:
        try:
            return self.manifest_json['sources']
        except KeyError as e:
            msg = 'No sources in manifest'
            raise ManifestError(msg) from e

    def get_video(self, name: str) -> Any:
        try:
            videos = self.get_source('videos')
            return videos[name]
        except ManifestError as e:
            msg = f'{name} is not a video source'
            raise ManifestError(msg) from e


    def get_areas_of_interests(self) -> Any:
        return self.get_source('areas_of_interests')


    def get_transcript(self) -> Any:
        return self.get_artifact('transcript')


    def get_recordings(self) -> list[Any]:
        try:
            return self.manifest_json['recordings']
        except KeyError as e:
            msg = 'No recordings in manifest'
            raise ManifestError(msg) from e

    def get_segments(self, name: str) -> Any:
        try:
            segments = self.get_artifact('segments')
            return segments[name]
        except (KeyError, ManifestError) as e:
            msg = f'{name} are not registered segments'
            raise ManifestError(msg) from e

    def get_multi_time(self, name: str) -> Any:
        try:
            multi_times = self.get_artifact('multi_time')
            return multi_times[name]
        except (KeyError, ManifestError) as e:
            msg = f'{name} is not a registered multivariate time series'
            raise ManifestError(msg) from e

    def get_video_overlay(self, name: str) -> Any:
        try:
            video_overlays = self.get_artifact('video_overlay')
            return video_overlays[name]
        except (KeyError, ManifestError) as e:
            msg = f'{name} are is a registered video overlay'
            raise ManifestError(msg) from e

    def register_artifact(self, name: str, val: Any, overwrite: bool = True) -> None:
        if 'artifacts' not in self.manifest_json:
            self.manifest_json['artifacts'] = {}

        if overwrite or name not in self.manifest_json['artifacts']:
            self.manifest_json['artifacts'][name] = val

    def register_segments(self, name: str, val: Any) -> None:
        self.register_artifact('segments', {}, overwrite=False)
        self.manifest_json['artifacts']['segments'][name] = val

    def register_video_overlay(self, name: str, val: Any) -> None:
        self.register_artifact('video_overlay', {}, overwrite=False)
        self.manifest_json['artifacts']['video_overlay'][name] = val

    def register_multi_time(self, name: str, val: Any) -> None:
        self.register_artifact('multi_time', {}, overwrite=False)
        self.manifest_json['artifacts']['multi_time'][name] = val

    def set_duration_sec(self, duration: int | float) -> None:
        if not isinstance(duration, (int, float)):
            msg = 'Duration must be a number'
            raise TypeError(msg)
        self.manifest_json['duration_sec'] = duration

    def set_language(self, language: str) -> None:
        if not isinstance(language, str):
            msg = 'Language must be a string'
            raise TypeError(msg)
        self.manifest_json['language'] = language

    def register_source(self, name: str, val: Any, overwrite: bool = True) -> None:
        if 'sources' not in self.manifest_json:
            self.manifest_json['sources'] = {}

        if overwrite or name not in self.manifest_json['sources']:
            self.manifest_json['sources'][name] = val

    def register_video(self, name: str, val: Any) -> None:
        self.register_source('videos', {}, overwrite=False)
        self.manifest_json['sources']['videos'][name] = val

    def set_areas_of_interests(self, val: Any) -> None:
        self.register_source('areas_of_interests', val, overwrite=True)

    def register_transcript(self, val: Any) -> None:
        self.register_artifact('transcript', val, overwrite=True)

    def add_recording(self, recording: Any) -> None:
        if 'recordings' not in self.manifest_json:
            self.manifest_json['recordings'] = []

        if not isinstance(self.manifest_json['recordings'], list):
            msg = 'Recordings must be a list'
            raise TypeError(msg)

        self.manifest_json['recordings'].append(recording)

    def set_recordings(self, recordings: list[Any]) -> None:
        if not isinstance(recordings, list):
            msg = 'Recordings must be a list'
            raise TypeError(msg)
        self.manifest_json['recordings'] = recordings

    def remove_recording(self, index: int) -> None:
        try:
            del self.manifest_json['recordings'][index]
        except (KeyError, IndexError) as e:
            msg = f'Cannot remove recording at index {index}'
            raise ManifestError(msg) from e

    def add_role(self, role: Any) -> None:
        if 'roles' not in self.manifest_json:
            self.manifest_json['roles'] = []

        if not isinstance(self.manifest_json['roles'], list):
            msg = 'Roles must be a list'
            raise TypeError(msg)

        self.manifest_json['roles'].append(role)

    def set_roles(self, roles: list[Any]) -> None:
        if not isinstance(roles, list):
            msg = 'Roles must be a list'
            raise TypeError(msg)
        self.manifest_json['roles'] = roles

    def remove_role(self, index: int) -> None:
        try:
            del self.manifest_json['roles'][index]
        except (KeyError, IndexError) as e:
            msg = f'Cannot remove role at index {index}'
            raise ManifestError(msg) from e

    @staticmethod
    def empty_manifest() -> dict:
        return {
            'language': 'auto',
            'duration_sec': 0.,
            'roles': [],
            'recordings': [],
            'sources': {
                'notes_snapshots': {
                    'path': '',
                    'offset_sec': 0.,
                },
                'areas_of_interests': {
                    'path': '',
                    'offset_sec': 0.,
                },
                'audio': {
                    'path': '',
                    'offset_sec': 0.,
                },
                'videos': {
                    'workspace': {
                        'path': '',
                        'offset_sec': 0.,
                    },
                    'side': {
                        'path': '',
                        'offset_sec': 0.,
                    },
                },
            },
            'artifacts': {},
        }

    @staticmethod
    def supported_languages() -> list[str]:
        return ['auto', 'english', 'german', 'french', 'spanish', 'italian']