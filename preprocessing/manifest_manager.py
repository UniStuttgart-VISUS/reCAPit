from pathlib import Path
import json

class ManifestManager:
    def __init__(self, path: Path, read_only=False):
        self.file = None
        self.path = path
        self.read_only = read_only

    def __enter__(self):
        self.file = open(self.path, 'r' if self.read_only else 'r+')
        self.manifest_json = json.load(self.file)
        assert self.check_integrity()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.read_only:
            assert self.check_integrity()
            self.file.seek(0)
            json.dump(self.manifest_json, self.file, indent=4)
            self.file.truncate()
        self.file.close()

    def check_integrity(self):
        if "language" not in self.manifest_json or not isinstance(self.manifest_json['language'], str):
            return False

        if "duration_sec" not in self.manifest_json or not isinstance(self.manifest_json['duration_sec'], (int, float)):
            return False

        if "roles" not in self.manifest_json or not isinstance(self.manifest_json['roles'], list):
            return False

        if 'recordings' in self.manifest_json and not isinstance(self.manifest_json['recordings'], list):
            return False

        if 'artifacts' in self.manifest_json and not isinstance(self.manifest_json['artifacts'], dict):
            return False

        return True
        
    def get_duration_sec(self):
        try: 
            return self.manifest_json['duration_sec']
        except KeyError as e:
            msg = 'No duration specified in manifest'
            raise Exception(msg) from e

    def get_language(self):
        try: 
            return self.manifest_json['language']
        except KeyError as e:
            msg = 'No language specified in manifest'
            raise Exception(msg) from e


    def get_artifact(self, name):
        try: 
            artifacts = self._artifacts()
            return artifacts[name]
        except KeyError as e:
            msg = f'{name} is not a registered artifact'
            raise Exception(msg) from e

    def _artifacts(self):
        try: 
            return self.manifest_json['artifacts']
        except KeyError as e:
            msg = 'No registered artifacts in manifest'
            raise Exception(msg) from e

    def get_source(self, name):
        try: 
            sources = self._sources()
            return sources[name]
        except KeyError as e:
            msg = f'{name} is not a source'
            raise Exception(msg) from e

    def _sources(self):
        try: 
            return self.manifest_json['sources']
        except KeyError as e:
            msg = 'No sources in manifest'
            raise Exception(msg) from e
            
    def get_video(self, name):
        try: 
            videos = self.get_source('videos')
            return videos[name]
        except Exception as e:
            msg = f'{name} is not a video source'
            raise Exception(msg) from e

    def get_areas_of_interests(self):
        return self.get_source('areas_of_interests')

    def get_transcript(self):
        return self.get_artifact('transcript')

    def get_recordings(self):
        try: 
            return self.manifest_json['recordings']
        except Exception as e:
            msg = 'No recordings in manifest'
            raise Exception(msg) from e

    def get_segments(self, name):
        try: 
            segments = self.get_artifact('segments')
            return segments[name]
        except Exception as e:
            msg = f'{name} are not registered segments'
            raise Exception(msg) from e

    def get_multi_time(self, name):
        try: 
            multi_times = self.get_artifact('multi_time')
            return multi_times[name]
        except Exception as e:
            msg = f'{name} is not a registered multivariate time series'
            raise Exception(msg) from e

    def get_video_overlay(self, name):
        try: 
            video_overlays = self.get_artifact('video_overlay')
            return video_overlays[name]
        except Exception as e:
            msg = f'{name} are is a registered video overlay'
            raise Exception(msg) from e

    def register_artifact(self, name, val, overwrite=True):
        if 'artifacts' not in self.manifest_json:
            self.manifest_json['artifacts'] = {}

        if overwrite or name not in self.manifest_json['artifacts']:
            self.manifest_json['artifacts'][name] = val

    def register_segments(self, name, val):
        self.register_artifact('segments', {}, overwrite=False)
        self.manifest_json['artifacts']['segments'][name] = val


    def register_video_overlay(self, name, val):
        self.register_artifact('video_overlay', {}, overwrite=False)
        self.manifest_json['artifacts']['video_overlay'][name] = val


    def register_multi_time(self, name, val):
        self.register_artifact('multi_time', {}, overwrite=False)
        self.manifest_json['artifacts']['multi_time'][name] = val