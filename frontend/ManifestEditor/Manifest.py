from pathlib import Path
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant
from helper.manifest_manager import ManifestManager

import logging
import sys

from .RecordingListModel import RecordingListModel

logger = logging.getLogger(__name__)

class SourceList(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    CategoryRole = Qt.ItemDataRole.UserRole + 2
    PathRole = Qt.ItemDataRole.UserRole + 3
    IconRole = Qt.ItemDataRole.UserRole + 4
    IsValidFileRole = Qt.ItemDataRole.UserRole + 5

    def __init__(self, manifest_manager: ManifestManager, parent: object = None) -> None:
        super().__init__(parent)
        self._manifest_manager = manifest_manager

    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.NameRole: b'name',
            self.CategoryRole: b'category',
            self.PathRole: b'path',
            self.IconRole: b'icon',
            self.IsValidFileRole: b'isValid',
        }

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self._projects)

    def data(self, index: QModelIndex, role: int):  # noqa: PLR0911
        if not index.isValid() or index.row() >= len(self._projects):
            return None

        self._manifest_manager.get_source()

        return None

    def setData(self, index: QModelIndex, value: QVariant, role: int) -> bool:
        if not index.isValid() or index.row() >= len(self.recordings):
            return False

        row = index.row()

        if role == self.RecIdRole:
            self.recordings[row]['id'] = value
        elif role == self.RoleRole:
            self.recordings[row]['role'] = value
        elif role == self.SourceGazeRole and 'surface_fixations' in self.recordings[row]['sources']:
            self.recordings[row]['sources']['surface_fixations']['path'] = value
        elif role == self.SourceGazeOffsetRole and 'surface_fixations' in self.recordings[row]['sources']:
            print(value)
            self.recordings[row]['sources']['surface_fixations']['offset_sec'] = value
        else:
            return False

        self.dataChanged.emit(index, index)
        return True


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
    manifestChanged = pyqtSignal(bool, bool, bool)  # noqa: N815
    artifactsChanged = pyqtSignal()  # noqa: N815

    @pyqtSlot()
    def on_property_change(self) -> None:
        #self.manifestChanged.emit(self._manifest_manager.has_global_artifact(), True)
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
        self.artifactsChanged.connect(self.on_property_change)

        self._participant_roles.dataChanged.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsInserted.connect(self._sync_roles_to_manifest)
        self._participant_roles.rowsRemoved.connect(self._sync_roles_to_manifest)

        self._recordings.dataChanged.connect(self.on_property_change)
        self._recordings.rowsInserted.connect(self.on_property_change)
        self._recordings.rowsRemoved.connect(self.on_property_change)


    @pyqtSlot()
    def _sync_roles_to_manifest(self) -> None:
        """Sync the roles from the model back to the manifest dictionary."""
        self._manifest_manager.set_roles(self._participant_roles.stringList())
        self.on_property_change()

    def _set_modified(self) -> None:
        if not self._was_modified:
            self._was_modified = True
            self.wasModifiedChanged.emit()

    @pyqtProperty(list, notify=manifestChanged)
    def multi_time_signals(self) -> list[str]:
        if not self._manifest_manager.has_global_artifact('multi_time'):
            return []

        mts = self._manifest_manager.get_artifact('multi_time')
        return mts.keys()

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

    @pyqtProperty(str, notify=audioChanged)
    def audio(self) -> str:
        if self._manifest_manager.has_global_source('audio'):
            return self._manifest_manager.get_source('audio')['path']
        return ''

    @pyqtProperty(str, notify=artifactsChanged)
    def segments_initial(self) -> str:
        if self._manifest_manager.has_global_artifact('segments'):
            segments = self._manifest_manager.get_artifact('segments')
            if 'initial' in segments:
                return segments['initial']['path']
        return ''

    @segments_initial.setter
    def segments_initial(self, val: str) -> None:
        if self.segments_initial != val:
            self._manifest_manager.register_segments('initial', {'path': val})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def segments_refined(self) -> str:
        if self._manifest_manager.has_global_artifact('segments'):
            segments = self._manifest_manager.get_artifact('segments')
            if 'refined' in segments:
                return segments['refined']['path']
        return ''

    @segments_refined.setter
    def segments_refined(self, val: str) -> None:
        if self.segments_refined != val:
            self._manifest_manager.register_segments('refined', {'path': val})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def heatmaps_attention(self) -> str:
        if self._manifest_manager.has_global_artifact('video_overlay'):
            overlays = self._manifest_manager.get_artifact('video_overlay')
            if 'attention' in overlays:
                return overlays['attention']['path']
        return ''

    @heatmaps_attention.setter
    def heatmaps_attention(self, val: str) -> None:
        if self.heatmaps_attention != val:
            self._manifest_manager.register_video_overlay('attention', {'path': val , 'offset_sec': 0})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def heatmaps_movement(self) -> str:
        if self._manifest_manager.has_global_artifact('video_overlay'):
            overlays = self._manifest_manager.get_artifact('video_overlay')
            if 'movement' in overlays:
                return overlays['movement']['path']
        return ''

    @heatmaps_movement.setter
    def heatmaps_movement(self, val: str) -> None:
        if self.heatmaps_movement != val:
            self._manifest_manager.register_video_overlay('movement', {'path': val , 'offset_sec': 0})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def transcript(self) -> str:
        if self._manifest_manager.has_global_artifact('transcript'):
            return self._manifest_manager.get_transcript()['path']
        return ''

    @transcript.setter
    def transcript(self, val: str) -> None:
        if self._manifest_manager.get_transcript()['path'] != val:
            self._manifest_manager.register_transcript({'path': val , 'offset_sec': 0})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def movement(self) -> str:
        if self._manifest_manager.has_global_artifact('multi_time'):
            mts = self._manifest_manager.get_artifact('multi_time')
            if 'movement' in mts:
                return mts['movement']['path']
        return ''

    @movement.setter
    def movement(self, val: str) -> None:
        if self.movement != val:
            self._manifest_manager.register_multi_time('movement', {'path': val , 'offset_sec': 0})
            self.artifactsChanged.emit()

    @pyqtProperty(str, notify=artifactsChanged)
    def attention(self) -> str:
        if self._manifest_manager.has_global_artifact('multi_time'):
            mts = self._manifest_manager.get_artifact('multi_time')
            if 'attention' in mts:
                return mts['attention']['path']
        return ''

    @attention.setter
    def attention(self, val: str) -> None:
        if self.attention != val:
            self._manifest_manager.register_multi_time('attention', {'path': val , 'offset_sec': 0})
            self.artifactsChanged.emit()

    @pyqtProperty(bool, notify=wasModifiedChanged)
    def was_modified(self) -> bool:
        return self._was_modified

    @audio.setter
    def audio(self, val: str) -> None:
        if self.audio != val:
            self._manifest_manager.register_source('audio', {'path': val , 'offset_sec': 0})
            self.audioChanged.emit()

    @pyqtProperty(str, notify=videoWorkspaceChanged)
    def video_workspace(self) -> str:
        if self._manifest_manager.has_global_source('videos'):
            videos = self._manifest_manager.get_source('videos')
            if 'workspace' in videos:
                return videos['workspace']['path']
        return ''

    @video_workspace.setter
    def video_workspace(self, val: str) -> None:
        if self.video_workspace != val:
            self._manifest_manager.register_video('workspace', {'path': val , 'offset_sec': 0})
            self.videoWorkspaceChanged.emit()

    @pyqtProperty(str, notify=videoSideChanged)
    def video_side(self) -> str:
        if self._manifest_manager.has_global_source('videos'):
            videos = self._manifest_manager.get_source('videos')
            if 'side' in videos:
                return videos['side']['path']
        return ''

    @video_side.setter
    def video_side(self, val: str) -> None:
        if self.video_side != val:
            self._manifest_manager.register_video('side', {'path': val , 'offset_sec': 0})
            self.videoSideChanged.emit()

    @pyqtProperty(str, notify=notesChanged)
    def notes(self) -> str:
        if self._manifest_manager.has_global_source('notes_snapshots'):
            return self._manifest_manager.get_source('notes_snapshots')['path']
        return ''

    @notes.setter
    def notes(self, val: str) -> None:
        if self._manifest_manager.get_source('notes_snapshots')['path'] != val:
            self._manifest_manager.register_source('notes_snapshots', {'path': val , 'offset_sec': 0})
            self.notesChanged.emit()

    @pyqtProperty(str, notify=aoiChanged)
    def aoi(self) -> str:
        if self._manifest_manager.has_global_source('areas_of_interests'):
            return self._manifest_manager.get_areas_of_interests()['path']
        return ''

    @aoi.setter
    def aoi(self, val: str) -> None:
        if self.aoi != val:
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
        self._participant_roles.setStringList(self._manifest_manager.get_roles())
        self._recordings.set_recordings(self._manifest_manager.get_recordings())
        self._was_modified = False
        self.manifestChanged.emit(self._manifest_manager.has_global_source('audio'),
                                  # TODO @me: Needs to be fixed
                                  self._manifest_manager.has_global_source('videos') and self._manifest_manager.has_global_source('areas_of_interests'),
                                  self._manifest_manager.has_global_artifact('transcript'))

    @pyqtSlot()
    def write_to_json(self) -> None:
        print('Write')
        self._manifest_manager.save()
