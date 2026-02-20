import logging
from helper.manifest_manager import ManifestManager
from PyQt6.QtCore import pyqtSlot, QVariant, QAbstractListModel, QModelIndex, Qt

logger = logging.getLogger(__name__)

class RecordingListModel(QAbstractListModel):
    RecIdRole = Qt.ItemDataRole.UserRole + 1
    RoleRole = Qt.ItemDataRole.UserRole + 2
    SourcesRole = Qt.ItemDataRole.UserRole + 3
    ArtifactsRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, manifest_manager: ManifestManager, parent: object = None) -> None:
        super().__init__(parent)
        self.manifest_manager = manifest_manager

    def reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self.manifest_manager.get_recordings())

    def removeRow(self, row: int, parent=QModelIndex()):  # noqa: ANN201, B008, N802
        return self.removeRows(row, 1, parent)

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:  # noqa: B008, N802
        if row < 0 or row >= len(self.recordings) or count <= 0:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        recordings = self.manifest_manager.get_recordings()

        for idx in range(count):
            if row < len(recordings):
                self.manifest_manager.remove_recording(recordings[idx]['id'])

        self.endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: QVariant, role: int) -> bool:
        if not index.isValid() or index.row() >= self.rowCount():
            return False

        row = index.row()
        rec = self.manifest_manager.get_recordings()[row]

        if role == self.RecIdRole:
            rec.rec_id = value
        elif role == self.RoleRole:
            rec.rec_role = value
        else:
            return False

        print(rec)
        self.dataChanged.emit(index, index)
        return True

    @pyqtSlot(int, str, str)
    def setSourcePath(self, row: int, src_name: str, path: str) -> bool:
        index = self.createIndex(row, 0)
        rec = self.manifest_manager.get_recordings()[row]
        rec.update_source(src_name, 'path', path, src_is_path=True)
        self.dataChanged.emit(index, index)
        return True


    @pyqtSlot(int, str, float)
    def setSourceOffset(self, row: int, src_name: str, offset_sec: str) -> bool:
        index = self.createIndex(row, 0)
        rec = self.manifest_manager.get_recordings()[row]
        rec.update_source(src_name, 'offset_sec', offset_sec, src_is_path=True)
        self.dataChanged.emit(index, index)
        return True

    @pyqtSlot(str, str)
    def add_new(self, rec_id: str, rec_role: str) -> None:
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)
        self.manifest_manager.add_recording(rec_id, rec_role)
        self.endInsertRows()

    @pyqtSlot(str, result=int)
    def str2role(self, role_str: str) -> int:  # noqa: N802
        if role_str == 'recId':
            return self.RecIdRole
        if role_str == 'role':
            return self.RoleRole
        if role_str == 'sources':
            return self.SourcesRole
        if role_str == 'artifacts':
            return self.ArtifactsRole
        return -1

    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.RecIdRole: b'recId',
            self.RoleRole: b'role',
            self.SourcesRole: b'sources',
            self.ArtifactsRole: b'artifacts',
        }

    def data(self, index: QModelIndex, role: int):  # noqa: PLR0911
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        row = index.row()
        rec = self.manifest_manager.get_recordings()[row]

        if role == self.RecIdRole:
            return rec.rec_id
        if role == self.RoleRole:
            return rec.rec_role
        if role == self.SourcesRole:
            src =  rec.get_sources(as_path=True, with_meta=True)
            return src
        if role == self.ArtifactsRole:
            return rec.get_artifacts(as_path=True, with_meta=True)
        return None
