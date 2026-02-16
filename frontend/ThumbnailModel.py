from PyQt6.QtCore import pyqtSignal, QAbstractListModel, Qt, QModelIndex, pyqtProperty
from typing import Any


class ThumbnailModel(QAbstractListModel):
    ImgIdRole = Qt.ItemDataRole.UserRole + 1
    PathRole = Qt.ItemDataRole.UserRole + 2
    AoiScores = Qt.ItemDataRole.UserRole + 3
    PosSecRole = Qt.ItemDataRole.UserRole + 4
    LabelRole = Qt.ItemDataRole.UserRole + 5

    countChanged = pyqtSignal()  # noqa: N815

    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)
        self.thumbnail_data = []

    @pyqtProperty(int, notify=countChanged)
    def count(self):  # noqa: ANN201
        return self.rowCount()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self.thumbnail_data)

    def removeRow(self, row: int, parent=QModelIndex()):  # noqa: ANN201, B008, N802
        return self.removeRows(row, 1, parent)

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:  # noqa: B008, N802
        if row < 0 or row >= len(self.thumbnail_data) or count <= 0:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            if row < len(self.thumbnail_data):
                del self.thumbnail_data[row]
        self.endRemoveRows()
        self.countChanged.emit()
        return True

    def append(self, img_id: str, aoi_scores: dict[str, float],
               pos_sec: float, label: str) -> None:
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)

        info = {
            'img_id': img_id,
            'path': 'image://thumbnails/' + img_id,
            'aoi_scores': aoi_scores,
            'pos_sec': pos_sec,
            'label': label,
        }

        self.thumbnail_data.append(info)
        self.countChanged.emit()
        self.endInsertRows()


    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.ImgIdRole: b'imgId',
            self.PathRole: b'path',
            self.AoiScores: b'aoiScores',
            self.PosSecRole: b'posSec',
            self.LabelRole: b'label',
        }

    def data(self, index: QModelIndex, role: int) -> Any:  # noqa: PLR0911
        if not index.isValid() or index.row() >= len(self.thumbnail_data):
            return None

        row = index.row()

        if role == self.ImgIdRole:
            return self.thumbnail_data[row]['img_id']
        if role == self.PathRole:
            return self.thumbnail_data[row]['path']
        if role == self.AoiScores:
            return self.thumbnail_data[row]['aoi_scores']
        if role == self.PosSecRole:
            return self.thumbnail_data[row]['pos_sec']
        if role == self.LabelRole:
            return self.thumbnail_data[row]['label']

        return None