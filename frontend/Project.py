import json
import logging
import sys
import pandas as pd

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from AppConfig import AppConfig
from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from SegmentModel import SegmentModel
from StackedSeries import StackedSeries
from TimelineModel import SubjectMultimodalData
from helper.manifest_manager import ManifestManager
from ManifestEditor import PreprocessingPipeline, Manifest

from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class Project(QObject):
    quit = pyqtSignal()  # noqa: N815

    def __init__(self, engine: QQmlApplicationEngine, parent: object = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.window = None

    def register_multi_time(self, multi_time_info: dict[str, dict]) -> None:
        for mt in self.user_config['streamgraph']:
            path = Path(multi_time_info[mt]['path'])
            if not path.is_file():
                continue

            logger.info('Processing multi time signal %s ...', path)
            signal = pd.read_csv(path)
            stacks = StackedSeries.from_signals(signal, min_ts=self.min_timestamp, max_ts=self.max_timestamp,
                                                labels=self.manifest_model.Labels(),
                                                log_transform=self.user_config['streamgraph'][mt]['log_scale'])
            self.segment_model.register_multi_time(mt, stacks)

    def register_video_overlay(self) -> None:
        for vo in self.manifest['artifacts']['video_overlay']:
            path = Path(self.manifest['artifacts']['video_overlay'][vo]['path'])
            if not path.is_file():
                continue

            logger.info('Processing video overlay %s ...', path)
            heatmap_info = pd.read_csv(path)
            heatmap_info['filename'] = heatmap_info['filename'].apply(lambda x: path.parent / x)
            heatmap_overlay_provider = HeatmapOverlayProvider(heatmap_info, cmap=self.user_config['video_overlay'][vo]['colormap'])
            overlay_root = self.segment_model.add_video_overlay_provider(vo, heatmap_overlay_provider)
            self.engine.addImageProvider(overlay_root, heatmap_overlay_provider)

    def open_project_manifest(self, root_dir: Path, name: str) -> None:
        self.export_dir = root_dir / 'export'
        self.manifest_path = root_dir / 'manifest.json'
        self.preprocessing_pipeline = PreprocessingPipeline.PreprocessingPipeline(self.manifest_path, root_dir, self)

        self.manifest = Manifest.Manifest(self.manifest_path)
        self.manifest.manifestChanged.connect(self.preprocessing_pipeline.reevaluate_pipeline_status)
        self.preprocessing_pipeline.runningStatusChanged.connect(self.manifest.load_from_json)
        self.manifest.load_from_json()

        self.engine.rootContext().setContextProperty('manifest', self.manifest)
        self.engine.rootContext().setContextProperty('preprocessingPipeline', self.preprocessing_pipeline)
        self.engine.load('ManifestEditor/ManifestWindow.qml')

        self.window = self.engine.rootObjects()[-1]
        self.window.setProperty('title', name)
        self.window.closing.connect(self.quit_manifest)


    def open_project_viewer(self, qf: QSurfaceFormat, root_dir: Path, name: str) -> None:
        self.export_dir = root_dir / 'export'
        self.manifest_path = root_dir / 'manifest.json'
        self.user_config_path = root_dir / 'config.json'

        with ManifestManager(self.manifest_path, root_dir, read_only=True) as man:
            self.user_config = json.load(open(self.user_config_path, encoding='utf-8'))

            self.min_timestamp = 0
            self.max_timestamp = man.get_duration_sec()

            segments = man.get_artifact('segments')

            if 'refined' in segments:
                topic_segments_file = Path(segments['refined']['path'])
            elif 'initial' in segments:
                topic_segments_file = Path(segments['initial']['path'])
            else:
                logger.error('No registered segments in manifest!')
                sys.exit()

            if not man.has_global_source('areas_of_interests'):
                logger.error('No registered areas_of_interests in manifest!')
                sys.exit()

            transcript_file = Path(man.get_transcript()['path'])
            aoi_file = Path(man.get_areas_of_interests()['path'])

            if not aoi_file.is_file():
                logger.error('Path "%s" does to refer to valid AOIs!', aoi_file)
                sys.exit()

            if not topic_segments_file.is_file():
                logger.error('Path "%s" does to refer to valid topic segments!', topic_segments_file)
                sys.exit()

            segments = pd.read_csv(topic_segments_file)
            dialogue_line, event_subtypes = SubjectMultimodalData.from_recordings(man.get_recordings(), self.min_timestamp, self.max_timestamp)
            SubjectMultimodalData.fill_missing_datatype(dialogue_line)

            self.manifest_model = AppConfig(man.get_recordings(), man.get_roles(),
                                            man.get_areas_of_interests()['path'],
                                            self.user_config, self.export_dir, event_subtypes)

            self.segment_model = SegmentModel(segments, dialogue_line, self.manifest_model, video_src=man.get_source('videos'))
            self.segment_model.AdjustFilter(self.manifest_model.SegmentMinDurSec(), self.manifest_model.SegmentDisplayDurSec())

            self.register_multi_time(man.get_artifact('multi_time'))

            if man.has_global_artifact('video_overlay'):
                self.register_video_overlay()

            if transcript_file.is_file():
                logger.info('Registering transcript %s ...', transcript_file)
                transcript = pd.read_csv(transcript_file)
                self.segment_model.set_transcript(transcript)

            if man.has_global_artifact('notes'):
                notes_diffs_file = Path(man.get_artifact('notes')['path'])
                logger.info('Registering notes file %s ...', notes_diffs_file)
                notes_model = NotesModel(pd.read_csv(notes_diffs_file))
                self.segment_model.set_notes(notes_model)

            """
            if args.savefile_id is not None:
                load_dir = self.data_dir / 'saved_state' / args.savefile_id
                self.segment_model.import_state(in_dir=Path(load_dir))
                logger.info('Successfully loaded save file: "%s"!', load_dir)
            """

            qf.setSamples(self.user_config['multisampling'])

            self.engine.addImageProvider('thumbnails', self.segment_model.thumbnail_provider)
            self.engine.rootContext().setContextProperty('aoiModel', self.manifest_model)
            self.engine.rootContext().setContextProperty('topicSegments', self.segment_model)
            self.engine.load('App.qml')

            self.window = self.engine.rootObjects()[-1]
            self.window.setProperty('title', name)
            self.window.closing.connect(self.quit_project)

    def delete_window(self) -> None:
        if self.window is not None:
            self.window.deleteLater()
            self.window = None

    @pyqtSlot()
    def quit_manifest(self) -> None:
        self.manifest.write_to_json()
        self.delete_window()
        self.engine.clearComponentCache()
        self.quit.emit()

    def quit_project(self) -> None:
        curr_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')
        curr_time = datetime.now(tz=timezone.utc).strftime('%H-%M-%S')

        export_sub_dir = self.export_dir / curr_date / curr_time
        export_sub_dir.mkdir(parents=True, exist_ok=True)

        if self.manifest_model.export_user_config(self.user_config_path):
            logger.info('Successfully saved user config to: "%s"!', self.user_config_path)

        self.delete_window()
        self.engine.clearComponentCache()

        if self.segment_model.export_state(out_dir=export_sub_dir):
            logger.info('Successfully saved current state to: "%s"!', export_sub_dir)

        self.quit.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pro = Project(engine)
    pro.open_project_manifest(app, Path('C:\\Users\\kochme\\.recapit\\Test2'))

    sys.exit(app.exec())
