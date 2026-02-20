from pathlib import Path
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant
from helper.manifest_manager import ManifestManager

import logging
from .RecordingListModel import RecordingListModel

logger = logging.getLogger(__name__)

class Manifest(QObject):
    # Notification signals for bindable properties
    languageChanged = pyqtSignal()  # noqa: N815
    durationSecChanged = pyqtSignal()  # noqa: N815
    recordingsChanged = pyqtSignal()  # noqa: N815
    participantRolesChanges = pyqtSignal()  # noqa: N815
    wasModifiedChanged = pyqtSignal()  # noqa: N815
    manifestChanged = pyqtSignal()  # noqa: N815
    artifactsChanged = pyqtSignal()  # noqa: N815
    sourcesChanged = pyqtSignal(str)  # noqa: N815

    @pyqtSlot()
    def on_property_change(self) -> None:
        self.manifestChanged.emit()
        print('write')
        self.write_to_json()

    def __init__(self, manifest_manager: ManifestManager, parent: object = None) -> None:
        super().__init__(parent)

        self._manifest_manager = manifest_manager
        self._participant_roles = QStringListModel()
        self._recordings = RecordingListModel(manifest_manager)

        self.languageChanged.connect(self.on_property_change)
        self.durationSecChanged.connect(self.on_property_change)
        self.sourcesChanged.connect(self.on_property_change)
        self.artifactsChanged.connect(self.on_property_change)

        self._participant_roles.dataChanged.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsInserted.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsRemoved.connect(self._sync_roles_to_manifest)

        self._recordings.dataChanged.connect(self.on_property_change)
        self._recordings.rowsInserted.connect(self.on_property_change)
        self._recordings.rowsRemoved.connect(self.on_property_change)

        self.load_from_json()

    def get_manifest_manager(self) -> ManifestManager:
        return self._manifest_manager

    @pyqtSlot()
    def _sync_roles_to_manifest(self) -> None:
        """Sync the roles from the model back to the manifest dictionary."""
        self._manifest_manager.set_roles(self._participant_roles.stringList())
        self.on_property_change()

    @pyqtSlot(str, result=bool)
    def is_valid_file(self, abs_path: str) -> bool:
        return Path(abs_path).is_file()

    @pyqtSlot(str, str, result=bool)
    def is_valid_dir(self, abs_path: str, file_suffix: str) -> bool:
        abs_path = Path(abs_path)

        if not abs_path.is_dir():
            return False

        files = list(abs_path.iterdir())
        return len(files) > 0 and (file_suffix == '*' or all(f.suffix == file_suffix for f in files))

    @pyqtSlot(result=list)
    def supported_languages(self) -> list[str]:
        return ManifestManager.supported_languages()

    @pyqtSlot(result=list)
    def supported_eye_tracking_devices(self) -> list[str]:
        return ManifestManager.supported_eye_tracking_devices()

    @pyqtProperty('QVariantMap', notify=sourcesChanged)
    def sources(self) -> str:
        # Nested sources can be accessed using forward slash(es)
        # Example: "videos/workspace" -> "workspace" is child of "videos"
        return self._manifest_manager.get_sources(with_meta=True, as_path=True)

    @pyqtSlot(str, str)
    def set_source_path(self, src: str, path: str) -> None:
        self._manifest_manager.update_source(src, 'path', path, src_is_path=True)
        self.sourcesChanged.emit(src)

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
        print(self._manifest_manager.get_roles())
        self._participant_roles.setStringList(self._manifest_manager.get_roles())
        self._recordings.reset()
        self.manifestChanged.emit()

    @pyqtSlot()
    def write_to_json(self) -> None:
        self._manifest_manager.save()
