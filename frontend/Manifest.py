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

from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant

import argparse
import json
import logging
import sys
import threading
import pandas as pd

logger = logging.getLogger(__name__)


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

class RecordingListModel(QAbstractListModel):
    RecIdRole = Qt.ItemDataRole.UserRole + 1
    RoleRole = Qt.ItemDataRole.UserRole + 2
    SourceGazeRole = Qt.ItemDataRole.UserRole + 3
    ArtifactsRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, recordings, parent: object = None) -> None:
        super().__init__(parent)
        self.recordings = recordings

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self.recordings)

    def removeRow(self, row: int, parent=QModelIndex()):  # noqa: ANN201, B008, N802
        return self.removeRows(row, 1, parent)

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:  # noqa: B008, N802
        if row < 0 or row >= len(self.recordings) or count <= 0:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            if row < len(self.recordings):
                del self.recordings[row]

        self.endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: QVariant, role: int) -> bool:
        if not index.isValid() or index.row() >= len(self.recordings):
            return False

        row = index.row()
        print(role)

        if role == self.RecIdRole:
            self.recordings[row]['id'] = value
        elif role == self.RoleRole:
            self.recordings[row]['role'] = value
        elif role == self.SourceGazeRole:
            self.recordings[row]['sources']['surface_fixations']['path'] = value
        else:
            return False

        self.dataChanged.emit(index, index)
        return True

    @pyqtSlot(str, str)
    def add_new(self, rec_id: str, rec_role: str) -> None:
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)

        self.recordings.append({
            'id': rec_id,
            'role': rec_role,
            'sources': {
                'surface_fixations': {
                    'path': '',
                    'offset_sec': '',
                },
            },
        })
        self.endInsertRows()

    @pyqtSlot(str, result=int)
    def str2role(self, role_str: str) -> int:  # noqa: N802
        if role_str == 'recId':
            return self.RecIdRole
        if role_str == 'role':
            return self.RoleRole
        if role_str == 'sourceGaze':
            return self.SourceGazeRole
        return -1

    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.RecIdRole: b'recId',
            self.RoleRole: b'role',
            self.SourceGazeRole: b'sourceGaze',
        }

    def data(self, index: QModelIndex, role: int):  # noqa: PLR0911
        if not index.isValid() or index.row() >= len(self.recordings):
            return None

        row = index.row()

        if role == self.RecIdRole:
            return self.recordings[row]['id']
        if role == self.RoleRole:
            return self.recordings[row]['role']
        if role == self.SourceGazeRole:
            if 'surface_fixations' in self.recordings[row]['sources']:
                return self.recordings[row]['sources']['surface_fixations']['path']
            return ''
        return None


class Manifest(QObject):
    # Notification signals for bindable properties
    languageChanged = pyqtSignal()  # noqa: N815
    durationSecChanged = pyqtSignal()  # noqa: N815
    audioChanged = pyqtSignal()  # noqa: N815
    aoiChanged = pyqtSignal()  # noqa: N815
    notesChanged = pyqtSignal()  # noqa: N815
    videoWorkspaceChanged = pyqtSignal()  # noqa: N815
    videoSideChanged = pyqtSignal()  # noqa: N815
    recordingsChanged = pyqtSignal()  # noqa: N815
    participantRolesChanges = pyqtSignal()  # noqa: N815
    wasModifiedChanged = pyqtSignal()  # noqa: N815

    def __init__(self, manifest_path: Path, parent: object = None) -> None:
        super().__init__(parent)

        with open(manifest_path, encoding='utf-8') as f:
            self._manifest = json.load(f)

            self._supported_languages = ['auto', 'english', 'german', 'french', 'spanish', 'italian']

            self._participant_roles = QStringListModel()
            self._participant_roles.setStringList(self._manifest['roles'])

            self._participant_roles.dataChanged.connect(self._sync_roles_to_manifest)
            self._participant_roles.rowsInserted.connect(self._sync_roles_to_manifest)
            self._participant_roles.rowsRemoved.connect(self._sync_roles_to_manifest)

            if self._manifest['language'] not in self._supported_languages:
                msg = f'Manifest specifies unsupported language: "{self._manifest["language"]}"'
                raise RuntimeError(msg)

            self._recordings = RecordingListModel(self._manifest['recordings'])
            self._sources = {}
            self._arts = {}
            self._was_modified = False

    def _sync_roles_to_manifest(self) -> None:
        """Sync the roles from the model back to the manifest dictionary."""
        self._manifest['roles'] = self._participant_roles.stringList()

    def _set_modified(self) -> None:
        if not self._was_modified:
            self._was_modified = True
            self.wasModifiedChanged.emit()

    @pyqtSlot(str, result=bool)
    def is_valid_file(self, abs_path: str) -> bool:
        return Path(abs_path).is_file()

    @pyqtSlot(str, result=bool)
    def is_valid_notes_dir(self, abs_path: str) -> bool:
        abs_path = Path(abs_path)

        if not abs_path.is_dir():
            return False
        return all(file.suffix == '.docm' for file in abs_path.glob('*'))

    @pyqtSlot(result=list)
    def supported_languages(self) -> list[str]:
        return self._supported_languages

    @pyqtProperty(str, notify=audioChanged)
    def audio(self) -> str:
        return self._manifest['sources']['audio']['path']

    @pyqtProperty(bool, notify=wasModifiedChanged)
    def was_modified(self) -> bool:
        return self._was_modified

    @audio.setter
    def audio(self, val: str) -> None:
        if self._manifest['sources']['audio']['path'] != val:
            self._manifest['sources']['audio']['path'] = val
            self.audioChanged.emit()

    @pyqtProperty(str, notify=videoWorkspaceChanged)
    def video_workspace(self) -> str:
        return self._manifest['sources']['videos']['workspace']['path']

    @video_workspace.setter
    def video_workspace(self, val: str) -> None:
        if self._manifest['sources']['videos']['workspace']['path'] != val:
            self._manifest['sources']['videos']['workspace']['path'] = val
            self.videoWorkspaceChanged.emit()

    @pyqtProperty(str, notify=videoSideChanged)
    def video_side(self) -> str:
        return self._manifest['sources']['videos']['side']['path']

    @video_side.setter
    def video_side(self, val: str) -> None:
        if self._manifest['sources']['videos']['side']['path'] != val:
            self._manifest['sources']['videos']['side']['path'] = val
            self.videoSideChanged.emit()

    @pyqtProperty(str, notify=notesChanged)
    def notes(self) -> str:
        return self._manifest['sources']['notes_snapshots']['path']

    @notes.setter
    def notes(self, val: str) -> None:
        if self._manifest['sources']['notes_snapshots']['path'] != val:
            self._manifest['sources']['notes_snapshots']['path'] = val
            self.notesChanged.emit()

    @pyqtProperty(str, notify=aoiChanged)
    def aoi(self) -> str:
        return self._manifest['sources']['areas_of_interests']['path']

    @aoi.setter
    def aoi(self, val: str) -> None:
        if self._manifest['sources']['areas_of_interests']['path'] != val:
            self._manifest['sources']['areas_of_interests']['path'] = val
            self.aoiChanged.emit()

    @pyqtProperty(float, notify=durationSecChanged)
    def duration_sec(self) -> float:
        return self._manifest['duration_sec']

    @duration_sec.setter
    def duration_sec(self, val: float) -> None:
        if self._manifest['duration_sec'] != val:
            self._manifest['duration_sec'] = val
            self.durationSecChanged.emit()


    @pyqtProperty(str, notify=languageChanged)
    def language(self) -> str:
        return self._manifest['language']


    @language.setter
    def language(self, val: str) -> None:
        if self._manifest['language'] != val:
            self._manifest['language'] = val
            self.languageChanged.emit()


    @pyqtProperty(RecordingListModel, notify=recordingsChanged)
    def recordings(self) -> RecordingListModel:
        return self._recordings


    @pyqtProperty(QStringListModel, notify=participantRolesChanges)
    def participant_roles(self) -> QStringListModel:
        return self._participant_roles


    @participant_roles.setter
    def participant_roles(self, value: QStringListModel) -> None:
        self._participant_roles = value
        self.participantRolesChanges.emit()

    def export_to_json(self, manifest_path:Path) -> None:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self._manifest, f, indent=4)


if __name__ == '__main__':
    from Project import Project

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pro = Project(engine)
    pro.open_project_manifest(app, Path('C:\\Users\\kochme\\.recapit\\test'))

    sys.exit(app.exec())

