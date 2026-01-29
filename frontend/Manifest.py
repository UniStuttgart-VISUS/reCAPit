from pathlib import Path
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant
from helper.manifest_manager import ManifestManager

import logging
import sys

from RecordingListModel import RecordingListModel

logger = logging.getLogger(__name__)

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
    manifestChanged = pyqtSignal(dict)  # noqa: N815

    @pyqtSlot()
    def on_property_change(self) -> None:
        self.manifestChanged.emit(self._manifest_manager.manifest_json.copy())
        self.write_to_json()

    def __init__(self, manifest_path: Path, parent: object = None) -> None:
        super().__init__(parent)

        self._manifest_manager = ManifestManager(manifest_path, Path(''), read_only=False)

        self._participant_roles = QStringListModel()
        self._recordings = RecordingListModel()

        self.languageChanged.connect(self.on_property_change)
        self.durationSecChanged.connect(self.on_property_change)
        self.audioChanged.connect(self.on_property_change)
        self.aoiChanged.connect(self.on_property_change)
        self.notesChanged.connect(self.on_property_change)
        self.videoWorkspaceChanged.connect(self.on_property_change)
        self.videoSideChanged.connect(self.on_property_change)
        self.recordingsChanged.connect(self.on_property_change)

        self._participant_roles.dataChanged.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsInserted.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsRemoved.connect(self._sync_roles_to_manifest)

        self._recordings.dataChanged.connect(self.on_property_change)
        self._recordings.rowsInserted.connect(self.on_property_change)
        self._recordings.rowsRemoved.connect(self.on_property_change)

        self.load_from_json()

    @pyqtSlot()
    def _sync_roles_to_manifest(self) -> None:
        """Sync the roles from the model back to the manifest dictionary."""
        self._manifest_manager.set_roles(self._participant_roles.stringList())
        self.on_property_change()

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
        return ManifestManager.supported_languages()

    @pyqtProperty(str, notify=audioChanged)
    def audio(self) -> str:
        return self._manifest_manager.get_source('audio')['path']

    @pyqtProperty(bool, notify=wasModifiedChanged)
    def was_modified(self) -> bool:
        return self._was_modified

    @audio.setter
    def audio(self, val: str) -> None:
        if self._manifest_manager.get_source('audio')['path'] != val:
            self._manifest_manager.register_source('audio', {'path': val , 'offset_sec': 0})
            self.audioChanged.emit()

    @pyqtProperty(str, notify=videoWorkspaceChanged)
    def video_workspace(self) -> str:
        return self._manifest_manager.get_video('workspace')['path']

    @video_workspace.setter
    def video_workspace(self, val: str) -> None:
        if self._manifest_manager.get_video('workspace')['path'] != val:
            self._manifest_manager.register_video('workspace', {'path': val , 'offset_sec': 0})
            self.videoWorkspaceChanged.emit()

    @pyqtProperty(str, notify=videoSideChanged)
    def video_side(self) -> str:
        return self._manifest_manager.get_video('side')['path']

    @video_side.setter
    def video_side(self, val: str) -> None:
        if self._manifest_manager.get_video('side')['path'] != val:
            self._manifest_manager.register_video('side', {'path': val , 'offset_sec': 0})
            self.videoSideChanged.emit()

    @pyqtProperty(str, notify=notesChanged)
    def notes(self) -> str:
        return self._manifest_manager.get_source('notes_snapshots')['path']

    @notes.setter
    def notes(self, val: str) -> None:
        if self._manifest_manager.get_source('notes_snapshots')['path'] != val:
            self._manifest_manager.register_source('notes_snapshots', {'path': val , 'offset_sec': 0})
            self.notesChanged.emit()

    @pyqtProperty(str, notify=aoiChanged)
    def aoi(self) -> str:
        return self._manifest_manager.get_areas_of_interests()['path']

    @aoi.setter
    def aoi(self, val: str) -> None:
        if self._manifest_manager.get_areas_of_interests()['path'] != val:
            self._manifest_manager.register_source('areas_of_interests', {'path': val, 'offset_sec': 0})
            self.aoiChanged.emit()

    @pyqtProperty(float, notify=durationSecChanged)
    def duration_sec(self) -> float:
        return self._manifest_manager.get_duration_sec()

    @duration_sec.setter
    def duration_sec(self, val: float) -> None:
        if self._manifest_manager.get_duration_sec() != val:
            self._manifest_manager.set_duration_sec(val)
            self.durationSecChanged.emit()


    @pyqtProperty(str, notify=languageChanged)
    def language(self) -> str:
        return self._manifest_manager.get_language()


    @language.setter
    def language(self, val: str) -> None:
        if self._manifest_manager.get_language() != val:
            self._manifest_manager.set_language(val)
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

    @pyqtSlot()
    def load_from_json(self) -> None:
        self._manifest_manager.load()
        print(self._manifest_manager.manifest_json)
        self._participant_roles.setStringList(self._manifest_manager.get_roles())
        self._recordings.set_recordings(self._manifest_manager.get_recordings())
        self._was_modified = False
        self.on_property_change()

    @pyqtSlot()
    def write_to_json(self) -> None:
        self._manifest_manager.save()


if __name__ == '__main__':
    from Project import Project

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pro = Project(engine)
    pro.open_project_manifest(app, Path('C:\\Users\\kochme\\.recapit\\test'))

    sys.exit(app.exec())

