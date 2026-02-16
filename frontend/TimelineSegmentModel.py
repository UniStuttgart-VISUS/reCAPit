import logging

from TopicCard import TopicCardData
from utils import speaker_time_by_role
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QAbstractListModel, Qt, QModelIndex, pyqtProperty, QRectF
from typing import Any
from NotesModel import NotesModel
from StackedSeries import StackedSeries
from ThumbnailModel import ThumbnailModel
from TimelineModel import SubjectMultimodalData
from PyQt6.QtMultimedia import QVideoSink
from TimelineSegment import TimelineSegment, DisplayState
from TranscriptRecord import TranscriptRecord
from HeatmapProvider import HeatmapOverlayProvider
from ThumbnailProvider import ThumbnailProvider
from dataclasses import asdict


class TimelineSegmentModel(QAbstractListModel):
    TitleRole = Qt.ItemDataRole.UserRole + 1
    SegmentIndexRole = Qt.ItemDataRole.UserRole + 2
    StartSecRole = Qt.ItemDataRole.UserRole + 3
    EndSecRole = Qt.ItemDataRole.UserRole + 4
    TimestampedEventsRole = Qt.ItemDataRole.UserRole + 5
    StackedDataRole = Qt.ItemDataRole.UserRole + 6
    SequenceDataRole = Qt.ItemDataRole.UserRole + 7
    HasCardRole = Qt.ItemDataRole.UserRole + 8
    QuotesTextRole = Qt.ItemDataRole.UserRole + 9
    QuotesNoteRole = Qt.ItemDataRole.UserRole + 10
    ThumbnailInfoRole = Qt.ItemDataRole.UserRole + 11
    MarkedRole = Qt.ItemDataRole.UserRole + 12
    SummariesRole = Qt.ItemDataRole.UserRole + 13
    LabelsRole = Qt.ItemDataRole.UserRole + 14
    TranscriptRecordsRole = Qt.ItemDataRole.UserRole + 15
    DisplayStateRole = Qt.ItemDataRole.UserRole + 16 # highlighted; visible; hidden;

    countChanged = pyqtSignal()  # noqa: N815
    cardVisibleChanged = pyqtSignal(int, bool)  # noqa: N815
    titleChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_title
    startSecChanged = pyqtSignal(int, float)  # noqa: N815 - row, new_start
    endSecChanged = pyqtSignal(int, float)  # noqa: N815 - row, new_end
    hasCardChanged = pyqtSignal(int, bool)  # noqa: N815 - row, new_value
    quotesTextChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_value
    quotesNoteChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_value
    markedChanged = pyqtSignal(int, bool)  # noqa: N815 - row, new_value
    labelsChanged = pyqtSignal(int)  # noqa: N815 - row, new_value
    transcriptRecordsChanged = pyqtSignal(int)  # noqa: N815 - row, new_value
    displayStateChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_value

    resetTopicCard = pyqtSignal(int)  # noqa: N815 - row, new_value

    def __init__(self,
                 segments: list[TimelineSegment],
                 transcripts_records: list[list[TranscriptRecord]],
                 stacked_data: dict[str, StackedSeries],
                 subject_data: dict[str, SubjectMultimodalData],
                 thumbnail_provider: ThumbnailProvider,
                 overlay_providers: dict[str, HeatmapOverlayProvider],
                 notes_data: NotesModel,
                 roles: list[str],
                 parent: object = None) -> None:
        super().__init__(parent)

        num_segments = len(segments)

        self.titles = [seg.title for seg in segments]
        self.start_ts = [seg.start_ts for seg in segments]
        self.end_ts = [seg.end_ts for seg in segments]
        self.summaries = [seg.summary for seg in segments]

        # Fields from TimelineSegment dataclass
        self.marked = [seg.marked for seg in segments]
        self.has_card = [seg.has_card for seg in segments]
        self.labels = [list(seg.labels) for seg in segments]
        self.quotes_text = [seg.quotes_text.original for seg in segments]
        self.quotes_note = [seg.quotes_note for seg in segments]
        self.display_state = [DisplayState.VISIBLE for _ in range(num_segments)]

        # Runtime-dependent fields (not part of dataclass)
        self.thumbnail_info = [ThumbnailModel(self) for _ in range(num_segments)]
        self.video_overlay_info = [{} for _ in range(num_segments)]

        self.indices = list(range(num_segments))
        self.heatmap_overlay_providers = overlay_providers
        self.thumbnail_provider = thumbnail_provider

        for provider in self.heatmap_overlay_providers.values():
            provider.segments_start = self.start_ts
            provider.segments_end = self.end_ts

        for segment_idx in range(num_segments):
            self.video_overlay_info[segment_idx] = {
                name: f'image://heatmaps_{name}/' + provider.img_id(segment_idx)
                for name, provider in self.heatmap_overlay_providers.items()
            }

        self.roles = roles
        self.notes_data = notes_data
        self.stacked_data = stacked_data
        self.subject_data = subject_data
        self.transcript_records = transcripts_records

    @pyqtProperty(int, notify=countChanged)
    def count(self) -> int:
        return self.rowCount()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self.indices)

    def get_stacked_segment(self, index:int) -> dict[str, StackedSeries]:
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return [mt.slice(start_ts, end_ts) for mt in self.stacked_data.values()]

    def get_subject_segment(self, index: int) -> dict[str, SubjectMultimodalData]:
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return {
            rec_id: multimodal_data.slice(start_ts, end_ts)
            for rec_id, multimodal_data in self.subject_data.items()
        }

    def get_notes_segment(self, index: int) -> NotesModel:
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return self.notes_data.slice(start_ts, end_ts)


    def roleNames(self) -> dict[int, str]:  # noqa: N802
        return {
            self.TitleRole: b'title',
            self.SegmentIndexRole: b'segmentIdx',
            self.StartSecRole: b'startSec',
            self.EndSecRole: b'endSec',
            self.TimestampedEventsRole: b'timeEvents',
            self.StackedDataRole: b'stackedData',
            self.SequenceDataRole: b'seqData',
            self.HasCardRole: b'hasCard',
            self.QuotesTextRole: b'quotesText',
            self.QuotesNoteRole: b'quotesNote',
            self.ThumbnailInfoRole: b'thumbnailInfo',
            self.MarkedRole: b'marked',
            self.SummariesRole: b'summaries',
            self.LabelsRole: b'labels',
            self.TranscriptRecordsRole: b'transcriptRecords',
            self.DisplayStateRole: b'displayState',
        }

    def data(self, index: QModelIndex, role: int) -> Any:  # noqa: PLR0911
        if not index.isValid() or index.row() >= len(self.indices):
            return None

        row = index.row()

        if role == self.TitleRole:
            return self.titles[row]
        if role == self.SegmentIndexRole:
            return self.indices[row]
        if role == self.StartSecRole:
            return self.start_ts[row]
        if role == self.EndSecRole:
            return self.end_ts[row]
        if role == self.TimestampedEventsRole:
            return self.get_notes_segment(row)
        if role == self.StackedDataRole:
            return self.get_stacked_segment(row)
        if role == self.SequenceDataRole:
            return self.get_subject_segment(row)
        if role == self.HasCardRole:
            return self.has_card[row]
        if role == self.QuotesTextRole:
            return self.quotes_text[row]
        if role == self.QuotesNoteRole:
            return self.quotes_note[row]
        if role == self.ThumbnailInfoRole:
            return self.thumbnail_info[row]
        if role == self.MarkedRole:
            return self.marked[row]
        if role == self.SummariesRole:
            return self.summaries[row]
        if role == self.LabelsRole:
            return self.labels[row]
        if role == self.TranscriptRecordsRole:
            return [asdict(tr) for tr in self.transcript_records[index]]
        if role == self.DisplayStateRole:
            return str(self.display_state[row])

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QModelIndex, value: Any, role: int) -> bool:  # noqa: N802, PLR0911
        if not index.isValid() or index.row() >= len(self.indices):
            return False

        row = index.row()

        if role == self.TitleRole:
            if self.titles[row] != value:
                self.titles[row] = value
                self.dataChanged.emit(index, index, [role])
                self.titleChanged.emit(row, value)
            return True

        if role == self.DisplayStateRole:
            if self.display_state[row] != DisplayState(value):
                self.display_state[row] = DisplayState(value)
                self.dataChanged.emit(index, index, [role])
                self.displayStateChanged.emit(row, value)
            return True

        if role == self.TranscriptRecordsRole:
            if self.transcript_records[row] != value:
                self.transcript_records[row] = value
                self.dataChanged.emit(index, index, [role])
                self.transcriptRecordsChanged.emit(row, value)
            return True

        if role == self.LabelsRole:
            if self.labels[row] != value:
                self.labels[row] = value
                self.dataChanged.emit(index, index, [role])
                self.labelsChanged.emit(row, value)
            return True

        if role == self.StartSecRole:
            if self.start_ts[row] != value:
                self.start_ts[row] = value
                self.dataChanged.emit(index, index, [role])
                self.startSecChanged.emit(row, value)
            return True

        if role == self.EndSecRole:
            if self.end_ts[row] != value:
                self.end_ts[row] = value
                self.dataChanged.emit(index, index, [role])
                self.endSecChanged.emit(row, value)
            return True

        if role == self.HasCardRole:
            if self.has_card[row] != value:
                self.has_card[row] = value
                self.dataChanged.emit(index, index, [role])
                self.hasCardChanged.emit(row, value)
                self.cardVisibleChanged.emit(row, value)
            return True

        if role == self.QuotesTextRole:
            if self.quotes_text[row] != value:
                self.quotes_text[row] = value
                self.dataChanged.emit(index, index, [role])
                self.quotesTextChanged.emit(row, value)
            return True

        if role == self.QuotesNoteRole:
            if self.quotes_note[row] != value:
                self.quotes_note[row] = value
                self.dataChanged.emit(index, index, [role])
                self.quotesNoteChanged.emit(row, value)
            return True

        if role == self.MarkedRole:
            if self.marked[row] != value:
                self.marked[row] = value
                self.dataChanged.emit(index, index, [role])
                self.markedChanged.emit(row, value)
            return True

        return False

    @pyqtSlot(int, str)
    def setTitle(self, row: int, title: str) -> bool:  # noqa: N802
        """Update the title at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, title, self.TitleRole)

    @pyqtSlot(int, float)
    def setStartSec(self, row: int, start_sec: float) -> bool:  # noqa: N802
        """Update the start timestamp at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, start_sec, self.StartSecRole)

    @pyqtSlot(int, float)
    def setEndSec(self, row: int, end_sec: float) -> bool:  # noqa: N802
        """Update the end timestamp at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, end_sec, self.EndSecRole)

    @pyqtSlot(int, bool)
    def setHasCard(self, row: int, has_card: bool) -> bool:  # noqa: N802
        """Update the hasCard flag at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, has_card, self.HasCardRole)

    @pyqtSlot(int, str)
    def setQuotesText(self, row: int, quotes_text: str) -> bool:  # noqa: N802
        """Update the quotes text at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, quotes_text, self.QuotesTextRole)

    @pyqtSlot(int, str)
    def setDisplayState(self, row: int, display_state: str) -> bool:  # noqa: N802
        """Update the quotes text at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, DisplayState(display_state), self.DisplayStateRole)

    @pyqtSlot(int, str)
    def setQuotesNote(self, row: int, quotes_note: str) -> bool:  # noqa: N802
        """Update the quotes note at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, quotes_note, self.QuotesNoteRole)

    @pyqtSlot(int, bool)
    def setMarked(self, row: int, marked: bool) -> bool:  # noqa: N802
        """Update the marked flag at the specified row."""
        index = self.index(row, 0)
        return self.setData(index, marked, self.MarkedRole)

    @pyqtSlot(int, result=bool)
    def isMarked(self, row: int) -> bool:  # noqa: N802
        index = self.index(row, 0)
        return self.data(index, self.MarkedRole)

    @pyqtSlot(int, result=bool)
    def hasCard(self, row: int) -> bool:  # noqa: N802
        index = self.index(row, 0)
        return self.data(index, self.HasCardRole)

    @pyqtSlot(int)
    def toggleMarked(self, row: int) -> bool:  # noqa: N802
        """Update the marked flag at the specified row."""
        index = self.index(row, 0)
        marked = self.data(index, self.MarkedRole)
        return self.setData(index, not marked, self.MarkedRole)

    @pyqtSlot(int, result=ThumbnailModel)
    def getThumbnailInfo(self, row: int) -> ThumbnailModel:  # noqa: N802
        """Get the thumbnail info model at the specified row."""
        if 0 <= row < len(self.thumbnail_info):
            return self.thumbnail_info[row]
        return None

    @pyqtSlot(int, list, int, str)
    def add_thumbnail(self, row: int, img_id: str, aoi_scores: list,
                      pos_sec: float, label: str) -> None:
        index = self.index(row, 0)
        if 0 <= row < len(self.thumbnail_info):
            self.thumbnail_info[row].append(img_id, aoi_scores, pos_sec, label)
            self.dataChanged.emit(index, index, [self.ThumbnailInfoRole])

    @pyqtSlot(int, list, int, str)
    def remove_thumbnail(self, row: int, crop_idx: int) -> None:
        index = self.index(row, 0)
        if 0 <= row < len(self.thumbnail_info) and 0 <= row < len(self.labels):
            del self.labels[row][crop_idx]
            self.thumbnail_info[row].removeRow(crop_idx)
            self.dataChanged.emit(index, index, [self.ThumbnailInfoRole, self.LabelsRole])

    @pyqtSlot(int, str)
    def add_label(self, row: int, label: str) -> None:
        index = self.index(row, 0)
        if 0 <= row < len(self.labels):
            self.labels[row].append(label)
            self.dataChanged.emit(index, index, [self.LabelsRole])

    @pyqtSlot(int, result=str)
    def getSummary(self, row: int) -> str:  # noqa: N802
        """Get the summary at the specified row (read-only)."""
        if 0 <= row < len(self.summaries):
            return self.summaries[row]
        return ''

    @pyqtSlot()
    def reset_segments(self):
        self.beginResetModel()
        self.endResetModel()

    @pyqtSlot(int, result=TopicCardData)
    def topic_card_data(self, index: int) -> TopicCardData:
        print(f'Generate topic card for: {index}')
        start_ts = self.start_ts
        end_ts = self.end_ts

        tcd = TopicCardData(self)
        tcd.segment_index = index
        tcd.labels = []
        tcd.title = self.titles[index]
        tcd.marked = self.marked[index]
        tcd.summary = self.summaries[index]

        tcd.dists_stats = {}
        tcd.dists_stats['speaker'] = speaker_time_by_role(self.transcript_records[index],
                                                          self.roles,
                                                          self.end_ts[index]-self.start_ts[index])

        for key in self.stacked_data:
            tcd.dists_stats[key] = self.stacked_data[key].slice(start_ts[index], end_ts[index]).LabelDistribution()

        tcd.text_notes = self.quotes_note[index]
        tcd.text_quotes = self.quotes_text[index]
        tcd.pos_start_sec = start_ts[index]
        tcd.pos_end_sec = end_ts[index]
        tcd.thumbnail_crops = self.thumbnail_info[index]
        tcd.notesHTML = self.get_notes_segment(index).allHTML()
        tcd.dialogue = self.transcript_records[index]
        tcd.video_overlays = self.video_overlay_info[index]
        tcd.display_state = self.display_state[index]
        return tcd

    @pyqtSlot(QVideoSink, float, int, QRectF, str, result=str)
    def register_video_crop(
        self,
        video_sink: QVideoSink,
        pos_ms: float,
        segment_idx: int,
        selection_norm: QRectF,
        overlay_src: str,
    ) -> str:

        img = video_sink.videoFrame().toImage()
        size = img.size()

        norm_x = selection_norm.x()
        norm_y = selection_norm.y()
        norm_width = selection_norm.width()
        norm_height = selection_norm.height()

        x = int(norm_x * size.width())
        y = int(norm_y * size.height())

        width = int(norm_width * size.width())
        height = int(norm_height * size.height())

        crop = img.copy(x, y, width, height)
        img_id, label = self.thumbnail_provider.add_to_collection(
            segment_idx, crop, overlay_src,
        )

        self.add_label(segment_idx, label)
        self.add_thumbnail(segment_idx, img_id, {}, pos_ms*1e-3, label)
        return label

    @pyqtSlot(int, int)
    def deregister_video_crop(self, segment_idx: int, crop_idx: int) -> None:
        self.remove_thumbnail(segment_idx, crop_idx)

    @pyqtSlot(list, result=bool)
    def keyword_match(self, keywords: list[str]) -> bool:
        has_matched = False

        for segment_idx in range(len(self.start_ts)):
            records = self.transcript_records[segment_idx]
            segment_txt = '.'.join([r.text.lower() for r in records])

            for kw in keywords:
                if kw.lower() in segment_txt:
                    self.setDisplayState(segment_idx, DisplayState.HIGHLIGHTED)
                    #self.resetTopicCard.emit(segment_idx)
                    has_matched = True
                    break

        return has_matched
