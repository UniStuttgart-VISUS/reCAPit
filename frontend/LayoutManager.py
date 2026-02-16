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
    SegmentIdxRole = Qt.ItemDataRole.UserRole + 5

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
            self.SegmentIdxRole: b'segmentIdx',
        }

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
        if role == self.SegmentIdxRole:
            return item.get('segmentIdx', -1)

        return None

    @pyqtSlot(int, result=float)
    def getDstPosX(self, row: int) -> float:
        index = self.createIndex(row, 0)
        return self.data(index, self.DstPosXRole)

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
        self.maxWidthChanged.connect(self.updateCardLayout)

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
            self.maxWidthChanged.emit()

    @pyqtSlot(int, bool)
    def is_registered(self, item_id: int):
        return item_id in self.item_ids

    @pyqtSlot()
    def unregister_all(self) -> None:
        self.top_width.clear()
        self.top_center_x.clear()
        self.top_start_x.clear()
        self.top_y.clear()
        self.bottom_width.clear()
        self.item_ids.clear()
        self.active.clear()

    @pyqtSlot(int)
    def register_item(self, item_id: int) -> None:  # noqa: FBT001

        if self.is_registered(item_id):
            return

        self.active.append(False)
        self.item_ids.append(item_id)
        self.top_center_x.append(0)
        self.top_start_x.append(0)
        self.top_y.append(0)
        self.top_width.append(0)
        self.bottom_width.append(375)


    @pyqtSlot(int, float, float, float, bool)
    def update_item(self, item_id: int, pos_x: float,
                    pos_y: float, width: float, is_active:bool) -> None:  # noqa: FBT001

        if not self.is_registered(item_id):
            return

        idx = self.item_ids.index(item_id)

        self.active[idx] = is_active
        self.top_center_x[idx] = pos_x + .5*width
        self.top_start_x[idx] = pos_x
        self.top_y[idx] = pos_y
        self.top_width[idx] = width

    @pyqtSlot(int, bool)
    def set_active(self, item_id: int, is_active:bool) -> None:  # noqa: FBT001
        if item_id in self.item_ids:
            idx = self.item_ids.index(item_id)
            self.active[idx] = is_active

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


    @pyqtSlot()
    def updateCardLayout(self) -> None:  # noqa: N802
        active_indices = [idx for idx, val in enumerate(self.active) if val]

        if len(self.item_ids) == 0 or len(active_indices) == 0:
            self._card_layout_model.updateData([])
            return

        top_center_x = [self.top_center_x[idx] for idx in active_indices]
        bottom_width = [self.bottom_width[idx] for idx in active_indices]

        out = linear_layout(
            sorted(top_center_x), bottom_width,
            min_xpos=bottom_width[0] / 2,
            max_xpos=self._max_width,
        )

        out = out.tolist() if out is not None else []

        layout_data = [{
            'segmentIdx': self.item_ids[dst_idx],
            'srcPosX': out[src_idx],
            'dstPosX': self.top_start_x[dst_idx],
            'cardWidth': bottom_width[src_idx],
            'segmentWidth': self.top_width[dst_idx],
        } for src_idx, dst_idx in enumerate(active_indices)]

        self._card_layout_model.updateData(layout_data)


    @pyqtSlot(result=QAbstractListModel)
    def card_layout(self) -> CardLayoutModel:
        return self._card_layout_model


class CardListModel(QAbstractListModel):
    CardDataRole = Qt.ItemDataRole.UserRole + 1
    LayoutRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, timeline_model: TimelineSegmentModel,
                 layout_model: LayoutManager, parent: QObject = None) -> None:
        super().__init__(parent)
        self.timeline_model = timeline_model
        self.layout_model = layout_model
        self.timeline_model.displayStateChanged.connect(self.fetch_topic_card_data)
        self.layout_model.layoutChanged.connect(self.reset_all)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008, N802
        return self.layout_model.card_layout().rowCount()

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.CardDataRole: b'cardDataX',
            self.LayoutRole: b'layoutData',
        }

    def reset_all(self):
        self.beginResetModel()
        self.endResetModel()

    @pyqtSlot(int)
    def fetch_topic_card_data(self, row: int) -> None:
        index = self.createIndex(row, 0)
        self.dataChanged.emit(index, index, [self.CardDataRole])

    def data(self, index: QModelIndex, role: int) -> Any:
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        layout = self.layout_model.card_layout()

        if role == self.CardDataRole:
            segment_idx = layout.data(index, CardLayoutModel.SegmentIdxRole)
            return self.timeline_model.topic_card_data(segment_idx)
        if role == self.LayoutRole:
            return {
                'srcPosX': layout.data(index, CardLayoutModel.SrcPosXRole),
                'cardWidth': layout.data(index, CardLayoutModel.CardWidthRole),
            }
        return None
