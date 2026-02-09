from pathlib import Path
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication
from datetime import datetime, timezone

from AppConfig import default_config

from PyQt6.QtCore import pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel
from helper.manifest_manager import ManifestManager

import json
import logging

from Project import Project

logger = logging.getLogger(__name__)

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        # Let the base class default method raise the TypeError
        return super().default(obj)

def date_now() -> str:
    return datetime.now(tz=timezone.utc).date().strftime('%Y-%m-%d')

class ProjectManager(QAbstractListModel):
    DirRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    DateCreatedRole = Qt.ItemDataRole.UserRole + 3
    LastOpenedRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, engine: QQmlApplicationEngine,
                 app: QApplication, qf: QSurfaceFormat, parent: object = None) -> None:
        super().__init__(parent)
        self.app = app
        self.engine = engine
        self.qf = qf

        self.engine.rootContext().setContextProperty('projectManager', self)

        self.app_dir = Path(QDir.homePath()) / '.recapit'
        self.app_dir.mkdir(exist_ok=True, parents=False)
        self._projects = []

        self.curr_project = None

    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.DirRole: b'dir',
            self.NameRole: b'name',
            self.DateCreatedRole: b'date_created',
            self.LastOpenedRole: b'last_opened',
        }

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self._projects)

    def data(self, index: QModelIndex, role: int):  # noqa: PLR0911
        if not index.isValid() or index.row() >= len(self._projects):
            return None

        row = index.row()

        if role == self.DirRole:
            return "" # str(self._projects[row]['export_dir'])
        if role == self.NameRole:
            return self._projects[row]['name']
        if role == self.DateCreatedRole:
            return self._projects[row]['date_created']
        if role == self.LastOpenedRole:
            return self._projects[row]['last_opened']
        return None


    @pyqtSlot(int, str)
    def open_project(self, row: int, action: str) -> None:
        if self.curr_project is not None:
            self.curr_project.deleteLater()

        self.curr_project = Project(self.engine, self)
        self.curr_project.quit.connect(self.open_manager)
        name = self._projects[row]['name']
        root_dir = self.app_dir / name

        if action == 'viewer':
            self.curr_project.open_project_viewer(self.qf, root_dir, name)
        elif action == 'manifest':
            self.curr_project.open_project_manifest(root_dir, name)
        else:
            logger.error(f'Unknown action "{action}" on project "{name}"')

        self._projects[row]['last_opened'] = date_now()

    @pyqtSlot(str, result=bool)
    def add_project(self, name: str) -> None:
        if name in [pro['name'] for pro in self._projects]:
            return False

        pro_dir = self.app_dir / name
        if pro_dir.exists():
            return False

        pro_dir.mkdir()

        export_dir = pro_dir / 'export'
        config_path = pro_dir / 'config.json'
        manifest_path = pro_dir / 'manifest.json'

        export_dir.mkdir()

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(ManifestManager.empty_manifest(), f, indent=4)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config(), f, indent=4)

        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)

        date_now_str = date_now()
        self._projects.append({'name': name,
                               'date_created': date_now_str,
                               'last_opened': date_now_str})
        self.endInsertRows()
        return True


    @pyqtSlot()
    def open_manager(self) -> None:
        self.engine.load('windows/ProjectManagerWindow.qml')
        self.app.aboutToQuit.connect(self.quit_manager)

    def export_projects(self) -> bool:
        config_path = self.app_dir / 'config.json'
        out_json = {'projects': self._projects}

        with open(config_path, 'w') as f:
            json.dump(out_json, f, indent=4, cls=ComplexEncoder)

    def parse_projects(self) -> None:
        config_path = self.app_dir / 'config.json'
        with open(config_path) as f:
            config = json.load(f)

            if 'projects' not in config:
                config['projects'] = []

            for pro in config['projects']:
                """
                if 'export_dir' not in pro:
                    logger.error('reCAPit config is invalid: missing "export_dir" entry in project')
                    continue
                """

                if 'name' not in pro:
                    logger.error('reCAPit config is invalid: missing "name" entry in project')
                    continue

                if 'date_created' not in pro:
                    logger.error('reCAPit config is invalid: missing "date_created" entry in project')
                    continue

                if 'last_opened' not in pro:
                    logger.warning('reCAPit config is incomplete: missing "last_opened" entry in project, so it will be added')
                    pro['last_opened'] = 'na-na-na'

                pro_dir = self.app_dir / Path(pro['name'])
                pro_manifest = pro_dir / 'manifest.json'
                pro_config = pro_dir / 'config.json'

                if not pro_dir.is_dir():
                    logger.error(f'Project directory "{pro_dir}" does not exist')
                    continue

                if not pro_manifest.is_file():
                    logger.error(f'Project directory "{pro_dir}" has no manifest.json')
                    continue

                if not pro_config.is_file():
                    logger.error(f'Project directory "{pro_dir}" has no config.json')
                    continue

                self._projects.append({
                                       #'export_dir': pro['export_dir'],
                                       'name': pro['name'],
                                       'date_created': pro['date_created'],
                                       'last_opened': pro['last_opened']})

    def quit_manager(self) -> None:
        self.export_projects()

