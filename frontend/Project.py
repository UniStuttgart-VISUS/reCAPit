from pathlib import Path
from AppConfig import AppConfig
from CustomVideoOutput import CustomVideoOutput
from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication
from SegmentModel import SegmentModel
from StackedSeries import StackedSeries
from TimelineModel import SubjectMultimodalData
from datetime import datetime, timezone

from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel

import argparse
import json
import logging
import sys
import threading
import pandas as pd

from Manifest import Manifest
from PreprocessingPipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)

def manifest_with_absolute_paths(root_dir:Path, manifest: dict) -> dict:
    def convert_paths(obj):
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'path' and isinstance(value, str):
                    # Convert relative path to absolute path
                    result[key] = str(root_dir / value)
                else:
                    # Recursively process nested structures
                    result[key] = convert_paths(value)
            return result
        elif isinstance(obj, list):
            # Recursively process list items
            return [convert_paths(item) for item in obj]
        else:
            # Return primitive values as-is
            return obj

    return convert_paths(manifest)


class Project(QObject):
    def __init__(self, engine: QQmlApplicationEngine, parent: object = None) -> None:
        super().__init__(parent)
        self.engine = engine

    def register_multi_time(self) -> None:
        for mt in self.user_config['streamgraph']:
            path = Path(self.manifest['artifacts']['multi_time'][mt]['path'])
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

    def open_project_manifest(self, app:QApplication, root_dir: Path) -> None:
        self.export_dir = root_dir / 'export'
        self.manifest_path = root_dir / 'manifest.json'
        self.preprocessing_pipeline = PreprocessingPipeline(self.manifest_path, root_dir, self)

        self.manifest = Manifest(self.manifest_path)
        self.engine.rootContext().setContextProperty('manifest', self.manifest)
        self.engine.rootContext().setContextProperty('preprocessingPipeline', self.preprocessing_pipeline)
        self.engine.load('windows/ManifestWindow.qml')
        app.aboutToQuit.connect(self.quit_manifest)

    def open_project_viewer(self, app: QApplication, qf: QSurfaceFormat, root_dir: Path, name: str) -> None:
        self.export_dir = root_dir / 'export'
        manifest_path = root_dir / 'manifest.json'
        user_config_path = root_dir / 'config.json'

        self.manifest = json.load(open(manifest_path, encoding='utf-8'))
        self.user_config = json.load(open(user_config_path, encoding='utf-8'))

        self.min_timestamp = 0
        self.max_timestamp = self.manifest['duration_sec']

        if 'refined' in self.manifest['artifacts']['segments']:
            topic_segments_file = Path(self.manifest['artifacts']['segments']['refined']['path'])
        elif 'initial' in self.manifest['artifacts']['segments']:
            topic_segments_file = Path(self.manifest['artifacts']['segments']['initial']['path'])
        else:
            logger.error('No registered segments in manifest!')
            sys.exit()

        if 'areas_of_interests' not in self.manifest['sources']:
            logger.error('No registered areas_of_interests in manifest!')
            sys.exit()

        transcript_file = Path(self.manifest['artifacts']['transcript']['path'])
        aoi_file = Path(self.manifest['sources']['areas_of_interests']['path'])

        if not aoi_file.is_file():
            logger.error('Path "%s" does to refer to valid AOIs!', aoi_file)
            sys.exit()

        if not topic_segments_file.is_file():
            logger.error('Path "%s" does to refer to valid topic segments!', topic_segments_file)
            sys.exit()

        segments = pd.read_csv(topic_segments_file)
        dialogue_line, event_subtypes = SubjectMultimodalData.from_recordings(self.manifest, self.min_timestamp, self.max_timestamp)
        SubjectMultimodalData.fill_missing_datatype(dialogue_line)

        self.manifest_model = AppConfig(self.manifest, self.user_config, self.export_dir, event_subtypes)
        self.segment_model = SegmentModel(segments, dialogue_line, self.manifest_model, video_src=self.manifest['sources']['videos'])
        self.segment_model.AdjustFilter(self.manifest_model.SegmentMinDurSec(), self.manifest_model.SegmentDisplayDurSec())

        self.register_multi_time()

        if 'video_overlay' in self.manifest['artifacts']:
            self.register_video_overlay()

        if transcript_file.is_file():
            logger.info('Registering transcript %s ...', transcript_file)
            transcript = pd.read_csv(transcript_file)
            self.segment_model.set_transcript(transcript)

        if 'notes' in self.manifest['artifacts']:
            notes_diffs_file = Path(self.manifest['artifacts']['notes']['path'])
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

        window = self.engine.rootObjects()[0]
        window.setProperty('title', name)

        app.aboutToQuit.connect(self.quit_project)

    @pyqtSlot()
    def quit_manifest(self) -> None:
        self.manifest.export_to_json(self.manifest_path)

    def quit_project(self) -> None:
        self.engine.deleteLater()
        curr_date = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')
        curr_time = datetime.now(tz=timezone.utc).strftime('%H-%M-%S')

        export_sub_dir = self.export_dir / curr_date / curr_time
        export_sub_dir.mkdir(parents=True, exist_ok=True)

        """
        if self.manifest_model.export_user_config(args.user_config):
            logger.info('Successfully saved user config to: "%s"!', args.user_config)
        """

        if self.segment_model.export_state(out_dir=export_sub_dir):
            logger.info('Successfully saved current state to: "%s"!', export_sub_dir)