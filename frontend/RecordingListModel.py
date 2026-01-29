import logging
from PyQt6.QtCore import pyqtSlot, QVariant, QAbstractListModel, QModelIndex, Qt

logger = logging.getLogger(__name__)


class RecordingListModel(QAbstractListModel):
    RecIdRole = Qt.ItemDataRole.UserRole + 1
    RoleRole = Qt.ItemDataRole.UserRole + 2
    SourceGazeRole = Qt.ItemDataRole.UserRole + 3
    ArtifactsRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)

    def set_recordings(self, recordings: list) -> None:
        self.beginResetModel()
        self.recordings = recordings
        self.endResetModel()

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
            'artifacts': {},
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
