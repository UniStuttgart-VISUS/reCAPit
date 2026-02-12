from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty, QAbstractListModel, Qt, QModelIndex
from PyQt6.QtQuick import QQuickItem
from typing import Any
from utils import linear_layout
from TimelineSegmentModel import TimelineSegmentModel


class CardLayoutModel(QAbstractListModel):
    """Model for card connector layout data."""

    SrcPosXRole = Qt.ItemDataRole.UserRole + 1
    DstPosXRole = Qt.ItemDataRole.UserRole + 2
    CardWidthRole = Qt.ItemDataRole.UserRole + 3
    SegmentWidthRole = Qt.ItemDataRole.UserRole + 4
    SegmentIdx = Qt.ItemDataRole.UserRole + 5

    # Signal emitted when any data in the model changes (not just row count)
    layoutDataChanged = pyqtSignal()  # noqa: N815

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self._data: list[dict] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008, N802
        return len(self._data)

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.SrcPosXRole: b'srcPosX',
            self.DstPosXRole: b'dstPosX',
            self.CardWidthRole: b'cardWidth',
            self.SegmentWidthRole: b'segmentWidth',
            self.SegmentIdx: b'segmentIdx',
        }

    def data_from_segment_idx(self, segment_index: int, role: int) -> Any:
        indices = [self.data(self.createIndex(idx, 0), self.SegmentIdx) for idx in range(self.rowCount())]
        if segment_index not in indices:
            return None

        row = indices.index(segment_index)
        return self.data(self.createIndex(row, 0), role)

    def data(self, index: QModelIndex, role: int) -> Any:
        if not index.isValid() or index.row() >= len(self._data):
            return None

        row = index.row()
        item = self._data[row]

        if role == self.SrcPosXRole:
            return item.get('srcPosX', 0.0)
        if role == self.DstPosXRole:
            return item.get('dstPosX', 0.0)
        if role == self.CardWidthRole:
            return item.get('cardWidth', 0.0)
        if role == self.SegmentWidthRole:
            return item.get('segmentWidth', 0.0)
        if role == self.SegmentIdx:
            return item.get('segmentIdx', -1)

        return None

    def updateData(self, new_data: list[dict]) -> None:  # noqa: N802
        """Update data, only emitting dataChanged for rows that actually changed."""
        old_len, new_len = len(self._data), len(new_data)

        # Handle structural changes with full reset
        if old_len != new_len:
            self.beginResetModel()
            self._data = new_data
            self.endResetModel()
            self.layoutDataChanged.emit()
            return

        # Same length: compare and emit dataChanged for changed rows
        changed = False
        for row, (old, new) in enumerate(zip(self._data, new_data, strict=False)):
            if old != new:
                changed = True
                self._data[row] = new
                idx = self.createIndex(row, 0)
                self.dataChanged.emit(idx, idx, [])

        if changed:
            self.layoutDataChanged.emit()


class LayoutManager(QObject):
    layoutChanged = pyqtSignal(int)  # noqa: N815
    itemsFinalized = pyqtSignal()  # noqa: N815
    maxWidthChanged = pyqtSignal()  # noqa: N815

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._max_width = 15000
        self._card_layout_model = CardLayoutModel(self)
        self._card_layout_model.layoutDataChanged.connect(lambda: self.layoutChanged.emit(-1))

        self.top_width = []
        self.top_center_x = []
        self.top_start_x = []
        self.top_y = []
        self.bottom_width = []
        self.item_ids = []
        self.active = []

    @pyqtProperty(float, notify=maxWidthChanged)
    def max_width(self) -> float:
        return self._max_width

    @max_width.setter
    def max_width(self, val: float) -> float:
        if self._max_width != val:
            self._max_width = val

    @pyqtSlot(int, bool)
    def is_registered(self, item_id: int):
        return item_id in self.item_ids


    @pyqtSlot(int, float, float, float, bool)
    def register_item(self, item_id: int, pos_x: float,
                      pos_y: float, width: float, is_active:bool) -> None:  # noqa: FBT001


        if self.is_registered(item_id):
            return

        self.active.append(is_active)
        self.item_ids.append(item_id)
        self.top_center_x.append(pos_x + .5*width)
        self.top_start_x.append(pos_x)
        self.top_y.append(pos_y)
        self.top_width.append(width)
        self.bottom_width.append(375)

        self._updateCardLayout()

    @pyqtSlot(int, bool)
    def set_active(self, item_id: int, is_active:bool) -> None:  # noqa: FBT001
        if item_id in self.item_ids:
            idx = self.item_ids.index(item_id)
            self.active[idx] = is_active
            self._updateCardLayout()

    @pyqtSlot(int)
    def unregister_item(self, item_id: int) -> None:
        if self.is_registered(item_id):
            idx = self.item_ids.index(item_id)

            del self.active[idx]
            del self.item_ids[idx]
            del self.top_center_x[idx]
            del self.top_start_x[idx]
            del self.top_y[idx]
            del self.top_width[idx]
            del self.bottom_width[idx]

            self._updateCardLayout()


    def _updateCardLayout(self) -> None:  # noqa: N802
        if len(self.item_ids) == 0:
            self._card_layout_model.updateData([])
            return

        out = linear_layout(
            sorted(self.top_center_x), self.bottom_width,
            min_xpos=self.bottom_width[0] / 2,
            max_xpos=self._max_width,
        )

        out = out.tolist() if out is not None else []

        layout_data = [{
            'segmentIdx': self.item_ids[idx],
            'srcPosX': out[idx],
            'dstPosX': self.top_start_x[idx],
            'cardWidth': self.bottom_width[idx],
            'segmentWidth': self.top_width[idx],
        } for idx, _ in enumerate(self.top_center_x) if self.active[idx]]

        self._card_layout_model.updateData(layout_data)


    @pyqtSlot(result=QAbstractListModel)
    def card_layout(self) -> CardLayoutModel:
        return self._card_layout_model


class CardListModel(QAbstractListModel):
    CardDataRole = Qt.ItemDataRole.UserRole + 1
    LayoutRole = Qt.ItemDataRole.UserRole + 2
    IsVisibleRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, timeline_model: TimelineSegmentModel,
                 layout_model: LayoutManager, parent: QObject = None) -> None:
        super().__init__(parent)
        self.timeline_model = timeline_model
        self.layout_model = layout_model
        self.timeline_model.attributeChanged.connect(self.update_data)
        self.layout_model.layoutChanged.connect(self.reset_all)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008, N802
        return self.timeline_model.rowCount()

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.CardDataRole: b'cardDataX',
            self.LayoutRole: b'layoutData',
            self.IsVisibleRole: b'isVisible',
        }

    def reset_all(self):
        self.beginResetModel()
        print('RESET ALL')
        self.endResetModel()

    def update_data(self, row: int) -> None:
        index = self.createIndex(row, 0)
        self.dataChanged.emit(index, index, [self.CardDataRole])
        print(f"update data: {index.row()}")

    def data(self, index: QModelIndex, role: int) -> Any:
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        row = index.row()
        has_layout = self.layout_model.is_registered(row)

        if role == self.CardDataRole:
            return self.timeline_model.GetTopicCardData(row)
        if role == self.LayoutRole:
            layout = self.layout_model.card_layout()
            return {
                'x': layout.data_from_segment_idx(row, CardLayoutModel.SrcPosXRole),
                'width': layout.data_from_segment_idx(row, CardLayoutModel.CardWidthRole),
            } if has_layout else {
                'x': 0,
                'width': 0,
            }
        if role == self.IsVisibleRole:
            return has_layout

        return None
