from pathlib import Path
import json
import importlib.resources

from copy import deepcopy, copy
from typing import Any, TYPE_CHECKING
from types import TracebackType

if TYPE_CHECKING:
    from io import TextIOWrapper


class ManifestError(Exception):
    pass
"""
def inject_metadata(manifest_flat: dict, meta_flat: dict) -> None:
    manifest_with_meta = {}
    for k, v in manifest_flat.items():
        manifest_with_meta[k] = v
        manifest_with_meta[k]['meta'] = meta_flat[k]
    return manifest_with_meta
"""

def inject_metadata(manifest: dict, meta: dict) -> None:
    manifest_with_meta = {}
    for k, v in manifest.items():
        if isinstance(v, dict) and 'path' in v:
            manifest_with_meta[k] = v
            manifest_with_meta[k]['meta'] = meta[k]
        else:
            manifest_with_meta[k] = inject_metadata(v, meta[k])
    return manifest_with_meta

def _navigate_path(data: dict, path: str) -> dict:
    """Navigate a nested dict via slash-separated path, returning the leaf dict."""
    current = data
    for part in path.split('/'):
        current = current[part]
    return current


def flatten_as_path(d: dict, root: str = '') -> tuple[dict, bool]:
    parent = {}
    is_leaf = True
    for k, v  in d.items():
        # We need to exclude 'meta' subtree, which might be present
        # when "inject_metadata" has been applied on input dict 'd'
        if isinstance(v, dict) and k != 'meta':
            path = f'{root}/{k}' if root != '' else k
            sub, sub_is_leaf = flatten_as_path(v, path)

            if sub_is_leaf:
                parent[path] = sub
            else:
                parent = parent | sub
            is_leaf = False
        else:
            parent[k] = v
    return parent, is_leaf


class Recording:
    def __init__(self, rec_data: dict, manifest_meta: dict) -> None:
        self.rec_data = rec_data
        self.manifest_meta = manifest_meta

    @property
    def rec_id(self) -> str:
        return self.rec_data['id']

    @rec_id.setter
    def rec_id(self, value: str) -> None:
        self.rec_data['id'] = value

    @property
    def rec_role(self) -> str:
        return self.rec_data['id']

    @rec_role.setter
    def rec_role(self, value: str) -> None:
        self.rec_data['role'] = value

    def get_artifact(self, name: str, as_path: bool = True) -> Any:
        try:
            artifacts = self.get_artifacts(with_meta=False, as_path=as_path)
            return artifacts[name]
        except KeyError as e:
            msg = f'{name} is not a registered artifact'
            raise ManifestError(msg) from e

    def get_source(self, name: str, as_path: bool = True) -> Any:
        try:
            sources = self.get_sources(with_meta=False, as_path=as_path)
            return sources[name]
        except KeyError as e:
            msg = f'{name} is not a registered source'
            raise ManifestError(msg) from e

    def get_artifacts(self, as_path: bool = True, with_meta: bool = True) -> dict:  # noqa: FBT001, FBT002
        try:
            artifacts = deepcopy(self.rec_data['artifacts'])

            if with_meta:
                artifacts = inject_metadata(artifacts, self.manifest_meta['artifacts'])
            if as_path:
                artifacts, _ = flatten_as_path(artifacts)

            return artifacts  # noqa: TRY300
        except ManifestError as e:
            raise ManifestError from e

    def get_sources(self, as_path: bool = True, with_meta: bool = True) -> dict:
        try:
            sources = deepcopy(self.rec_data['sources'])

            if with_meta:
                sources = inject_metadata(sources, self.manifest_meta['sources'])
            if as_path:
                sources, _ = flatten_as_path(sources)

            return sources  # noqa: TRY300
        except ManifestError as e:
            raise ManifestError from e

    def has_source(self, name: str, as_path: bool = True) -> bool:
        sources = self.get_sources(with_meta=False, as_path=as_path)
        if name not in sources:
            return False
        return Path(sources[name]['path']).exists()

    def has_artifact(self, name: str, as_path: bool = True) -> bool:
        artifacts = self.get_artifacts(with_meta=False, as_path=as_path)
        if name not in artifacts:
            return False
        return Path(artifacts[name]['path']).exists()

    def update_source(self, src: str, key: str, val: Any, src_is_path: bool) -> None:  # noqa: FBT001
        if src_is_path:
            target = _navigate_path(self.rec_data['sources'], src)
        else:
            target = self.rec_data['sources'][src]
        target[key] = val

    def update_artifact(self, art: str, key: str, val: Any, art_is_path: bool) -> None:  # noqa: FBT001
        if art_is_path:
            target = _navigate_path(self.rec_data['artifacts'], art)
        else:
            target = self.rec_data['artifacts'][art]
        target[key] = val

    def register_source(self, name: str, val: Any, overwrite: bool = True) -> None:
        if 'sources' not in self.rec_data:
            self.rec_data['sources'] = {}

        if overwrite or name not in self.rec_data['sources']:
            self.rec_data['sources'][name] = val

    def register_artifact(self, name: str, val: Any, overwrite: bool = True) -> None:
        if 'artifacts' not in self.rec_data:
            self.rec_data['artifacts'] = {}

        if overwrite or name not in self.rec_data['artifacts']:
            self.rec_data['artifacts'][name] = val



class ManifestManager:
    def __init__(self, path: Path, root_dir: Path, read_only: bool = False) -> None:
        self.file: TextIOWrapper | None = None
        self.root_dir: Path = root_dir
        self.path: Path = path
        self.read_only: bool = read_only
        self.manifest_json: dict[str, Any] = {}
        self.manifest_meta: dict[str, Any] = {}
        self.recordings = []

        with importlib.resources.open_text('helper', 'manifest_meta.json') as file:
            self.manifest_meta = json.load(file)

    def __enter__(self) -> 'ManifestManager':  # noqa: PYI034
        self.file = open(self.path, 'r' if self.read_only else 'r+')
        self.manifest_json = json.load(self.file)
        self.recordings.clear()

        for rec in self.manifest_json['recordings']:
            self.recordings.append(Recording(rec, self.manifest_meta['recordings']))

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

    def reload_from_file(self) -> None:
        if self.file is None:
            raise RuntimeError
        # We discard all the changes made to the manifest!
        self.file.close()
        self.__enter__()

    @DeprecationWarning
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
            self.manifest_json['recordings'] = [rec.rec_data for rec in self.recordings]
            json.dump(self.manifest_json, f, indent=4)

    def check_integrity(self) -> bool:
        return True

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

    def get_recordings(self) -> list[Recording]:
        return self.recordings

    def get_recording(self, rec_id: str) -> None:
        for rec in self.get_recordings():
            if rec.rec_id == rec_id:
                return rec
        raise ValueError

    def add_recording(self, rec_id: str, rec_role: str) -> None:
        rec = Recording({
            'id': rec_id,
            'role': rec_role,
            # TODO @me: Sources should be set in the UI not here
            'sources': {
                'gaze': {'path': 'undefined', 'offset_sec': 0},
                'faces': {'path': 'undefined'},
            },
            'artifacts': {},
        }, self.manifest_meta['recordings'])
        self.recordings.append(rec)

    def remove_recording(self, rec_id: int) -> None:
        try:
            rec_ids = [rec.rec_id for rec in self.get_recordings()]
            index = rec_ids.index(rec_id)

            if index == -1:
                raise RuntimeError
            del self.recordings[index]
        except (KeyError, IndexError) as e:
            msg = f'Cannot remove recording at index {index}'
            raise ManifestError(msg) from e

    def has_artifact(self, name: str, as_path: bool = True) -> bool:
        artifacts = self.get_artifacts(with_meta=False, as_path=as_path)
        if name not in artifacts:
            return False
        return Path(artifacts[name]['path']).exists()

    def has_source(self, name: str, as_path: bool = True) -> bool:
        sources = self.get_sources(with_meta=False, as_path=as_path)
        if name not in sources:
            return False
        return Path(sources[name]['path']).exists()

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

    def get_sources(self, as_path: bool = True, with_meta: bool = True) -> dict:  # noqa: FBT001, FBT002
        try:
            sources = deepcopy(self._sources())

            if with_meta:
                sources = inject_metadata(sources,
                                            self.manifest_meta['sources'])
            if as_path:
                sources, _ = flatten_as_path(sources)

            return sources  # noqa: TRY300
        except ManifestError as e:
            raise ManifestError from e

    def get_artifacts(self, as_path: bool = True, with_meta: bool = True) -> dict:  # noqa: FBT001, FBT002
        try:
            artifacts = deepcopy(self._artifacts())

            if with_meta:
                artifacts = inject_metadata(artifacts,
                                            self.manifest_meta['artifacts'])
            if as_path:
                artifacts, _ = flatten_as_path(artifacts)

            return artifacts  # noqa: TRY300
        except ManifestError as e:
            raise ManifestError from e

    def update_source(self, src: str, key: str, val: Any, src_is_path: bool) -> None:  # noqa: FBT001
        sources = self._sources()
        target = _navigate_path(sources, src) if src_is_path else sources[src]
        target[key] = val

    def update_artifact(self, art: str, key: str, val: Any, art_is_path: bool) -> None:  # noqa: FBT001
        artifacts = self._artifacts()
        target = _navigate_path(artifacts, art) if art_is_path else artifacts[art]
        target[key] = val

    def get_video(self, name: str) -> Any:
        try:
            videos = self.get_source('videos')
            return videos[name]
        except ManifestError as e:
            msg = f'{name} is not a video source'
            raise ManifestError(msg) from e

    def get_transcript(self) -> Any:
        return self.get_artifact('transcript')

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
            # TODO @me: Sources should be set in the UI not here
            'sources': {
                'audio': {'path': 'undefined', 'offset_sec': 0},
                'videos': {
                    'workspace': {'path': 'undefined', 'offset_sec': 0},
                    'side': {'path': 'undefined', 'offset_sec': 0},
                },
                'notes_snapshots': {'path': 'undefined', 'offset_sec': 0},
                'areas_of_interests': {'path': 'undefined', 'offset_sec': 0},
             },
            'artifacts': {},
        }

    @staticmethod
    def supported_languages() -> list[str]:
        return ['english', 'german', 'french', 'spanish', 'italian']


if __name__ == '__main__':

    d1 = {"artifacts": {
        "transcript": {
            "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\transcript.csv",
            "offset_sec": 0.0,
        },
        "multi_time": {
            "movement": {
                "x": {
                    "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\movement_x.csv",
                    "categories": "areas_of_interests"
                },
                "y": {
                    "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\movement_y.csv",
                    "categories": "areas_of_interests"
                },
            },
            "attention": {
                "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\attention.csv",
                "categories": "areas_of_interests",
            }
        },
        "segments": {
            "initial": {
                "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\initial.csv"
            },
        },
    }}

    d2 = {"sources": {
        "audio": {
            "path": "E:/workshops/seyda/genai-physicalization/auio.wav",
            "offset_sec": 1242.0,
        },
        "videos": {
            "workspace": {
                "path": "E:/workshops/seyda/genai-physicalization/videos/top_down_audio.mp4",
                "offset_sec": 0,
            },
            "side": {
                "path": "E:/workshops/seyda/genai-physicalization/videos/side.mp4",
                "offset_sec": 0.0,
            },
        },
        "areas_of_interests": {
            "path": "E:/workshops/seyda/genai-physicalization/aois_areas.json",
            "offset_sec": 0,
        },
        "movement_store": {
            "path": "C:\\Users\\kochme\\.recapit\\GenAI-Physicalization\\movement_store.zarr",
            "offset_sec": 0,
        },
    }}

    man = ManifestManager(Path(), Path())

    #print(flatten_nested(d2['sources'])[0].keys())

    source_flat, _ = flatten_as_path(d2['sources'])
    meta_flat, _ = flatten_as_path(man.manifest_meta['sources'])
    
    sm = inject_metadata(d2['sources'], man.manifest_meta['sources'])
    flat, _ = flatten_as_path(sm)
    print(flat)