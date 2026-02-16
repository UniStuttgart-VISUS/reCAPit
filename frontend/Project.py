import json
import logging
import sys

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from helper.manifest_manager import ManifestManager
from ManifestEditor import PreprocessingPipeline, Manifest

from LayoutManager import CardListModel, LayoutManager
from datetime import datetime, timezone
from pathlib import Path
from Viewer import Viewer

logger = logging.getLogger(__name__)


class Project(QObject):
    quit = pyqtSignal()  # noqa: N815

    def __init__(self, engine: QQmlApplicationEngine, parent: object = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.window = None

    def open_data_manager(self, root_dir: Path, name: str) -> None:
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


    def open_viewer(self, qf: QSurfaceFormat, root_dir: Path, name: str) -> None:
        self.export_dir = root_dir / 'export'
        self.manifest_path = root_dir / 'manifest.json'
        self.user_config_path = root_dir / 'config.json'

        with ManifestManager(self.manifest_path, root_dir, read_only=True) as man:
            self.user_config = json.load(open(self.user_config_path, encoding='utf-8'))

            self.viewer = Viewer(man, self.user_config, self.export_dir)
            self.layout_manager = LayoutManager(self)
            self.card_list_model = CardListModel(self.viewer.timeline_segments,
                                                 self.layout_manager)

            qf.setSamples(self.user_config['multisampling'])

            self.engine.addImageProvider('thumbnails', self.viewer.thumbnail_provider)

            for prov_name, prov in self.viewer.heatmap_overlay_providers.items():
                self.engine.addImageProvider(f'heatmaps_{prov_name}', prov)

            self.engine.rootContext().setContextProperty('cardList', self.card_list_model)
            self.engine.rootContext().setContextProperty('layoutManager', self.layout_manager)
            self.engine.rootContext().setContextProperty('aoiModel', self.viewer.app_config)
            self.engine.rootContext().setContextProperty('timeline_segment_model', self.viewer.timeline_segments)
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

        """
        if self.manifest_model.export_user_config(self.user_config_path):
            logger.info('Successfully saved user config to: "%s"!', self.user_config_path)
        """

        self.delete_window()
        self.engine.clearComponentCache()

        """
        if self.segment_model.export_state(out_dir=export_sub_dir):
            logger.info('Successfully saved current state to: "%s"!', export_sub_dir)
        """

        self.quit.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pro = Project(engine)
    pro.open_data_manager(app, Path('C:\\Users\\kochme\\.recapit\\Test2'))

    sys.exit(app.exec())
