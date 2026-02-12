import logging
import numpy as np
import pandas as pd

from TopicCard import TopicCardData
from utils import longest_common_substring
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QAbstractListModel, Qt, QModelIndex, pyqtProperty
from typing import Any
from NotesModel import NotesModel
from StackedSeries import StackedSeries
from ThumbnailModel import ThumbnailModel
from TimelineModel import SubjectMultimodalData

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

    countChanged = pyqtSignal()  # noqa: N815
    cardVisibleChanged = pyqtSignal()  # noqa: N815
    titleChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_title
    startSecChanged = pyqtSignal(int, float)  # noqa: N815 - row, new_start
    endSecChanged = pyqtSignal(int, float)  # noqa: N815 - row, new_end
    hasCardChanged = pyqtSignal(int, bool)  # noqa: N815 - row, new_value
    quotesTextChanged = pyqtSignal(int, 'QVariantMap')  # noqa: N815 - row, new_value
    quotesNoteChanged = pyqtSignal(int, str)  # noqa: N815 - row, new_value
    markedChanged = pyqtSignal(int, bool)  # noqa: N815 - row, new_value
    labelsChanged = pyqtSignal(int)  # noqa: N815 - row, new_value
    attributeChanged = pyqtSignal(int)  # noqa: N815 - row, new_value

    def __init__(self,
                 titles: list[str],
                 has_card: list[bool],
                 start_ts: list[float],
                 end_ts: list[float],
                 transcript: pd.DataFrame,
                 stacked_data: dict[str, StackedSeries],
                 subject_data: dict[str, SubjectMultimodalData],
                 notes_data: NotesModel,
                 roles: list[str],
                 quotes_text: list[dict],
                 quotes_note: list[str],
                 thumbnail_info: list[ThumbnailModel],
                 marked: list[bool],
                 summaries: list[str],
                 labels: list[str],
                 parent: object = None) -> None:
        super().__init__(parent)
        self.roles = roles
        self.titles = titles
        self.indices = list(range(len(titles)))
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.notes_data = notes_data
        self.stacked_data = stacked_data
        self.subject_data = subject_data
        self.has_card = has_card
        self.labels = labels
        self.transcript = transcript
        self.quotes_text = quotes_text
        self.quotes_note = quotes_note 
        self.thumbnail_info = thumbnail_info
        self.marked = marked
        self._summaries = summaries

        self.dataChanged.connect(lambda start, end, role: self.attributeChanged.emit(start.row()))

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
            return self._summaries[row]
        if role == self.LabelsRole:
            return self.labels[row]

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
                self.cardVisibleChanged.emit()
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
        quotes = self.extract_quotes(row, quotes_text)
        return self.setData(index, quotes, self.QuotesTextRole)

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

    @pyqtSlot(int, result=str)
    def getSummary(self, row: int) -> str:  # noqa: N802
        """Get the summary at the specified row (read-only)."""
        if 0 <= row < len(self._summaries):
            return self._summaries[row]
        return ''

    @pyqtSlot(int, str, result=bool)
    def updateField(self, row: int, field_name: str, value: Any) -> bool:  # noqa: N802
        """Update a field by name at the specified row.

        Args:
            row: The row index to update
            field_name: The name of the field ('title', 'startSec', 'endSec', 'hasCard',
                        'quotesText', 'quotesNote', 'marked')
            value: The new value for the field

        Returns:
            True if the update was successful, False otherwise
        """
        role_map = {
            'title': self.TitleRole,
            'startSec': self.StartSecRole,
            'endSec': self.EndSecRole,
            'hasCard': self.HasCardRole,
            'quotesText': self.QuotesTextRole,
            'quotesNote': self.QuotesNoteRole,
            'marked': self.MarkedRole,
        }
        role = role_map.get(field_name)
        if role is None:
            return False
        index = self.index(row, 0)
        return self.setData(index, value, role)

    def extract_quotes(self, index: int, text: str) -> dict:
        text_units = text.split('\n\n')
        text_units = [t.replace('\n', ' ').strip() for t in text_units if len(t) > 0]
        formatted = []
        speaker_quotes = []

        for tu in text_units:
            results = []

            for line in self.GetUtteranceSpeakerPairs(index):
                line_text = line['text'].replace('\n', ' ').strip()
                match = longest_common_substring(tu, line_text)

                src = line['speaker']
                cnt = sum(other_src == src for other_src, _, _ in results)
                results.append((src, cnt, match))

            max_idx = np.argmax([res['size'] for _, _, res in results])
            src, idx, res = results[max_idx]

            if (res['size'] / len(tu)) > 0.5:
                quote_label = f'{src.upper()[:2]}{idx + 1}'

                if quote_label not in self.labels[index]:
                    self.labels[index].append(quote_label)

                formatted.append(
                    f'{tu[0 : res["a"]]} <font color="grey"><b>{quote_label}</b></font> <font color="black"><u>{tu[res["a"] : res["a"] + res["size"]]}</u></font>{tu[res["a"] + res["size"] :]}'
                )
                speaker_quotes.append(
                    {'speaker': src, 'label': quote_label ,'text': tu[res['a'] : res['a'] + res['size']]},
                )
            else:
                formatted.append(tu)

        formatted = '<br><br>'.join(formatted)
        return {'original': text,
                'formatted': formatted,
                'quotes': speaker_quotes}

    @pyqtSlot(int, result=TopicCardData)
    def GetTopicCardData(self, index):
        start_ts = self.start_ts
        end_ts = self.end_ts

        tcd = TopicCardData(self)
        tcd.segment_index = index
        tcd.labels = []
        tcd.title = self.titles[index]
        tcd.marked = self.marked[index]
        tcd.summary = self._summaries[index]

        tcd.dists_stats = {}
        tcd.dists_stats['speaker'] = self.speaker_time_by_role(index)

        for key in self.stacked_data:
            tcd.dists_stats[key] = self.stacked_data[key].slice(start_ts[index], end_ts[index]).LabelDistribution()

        tcd.text_notes = self.quotes_note[index]
        tcd.text_dialogues = self.quotes_text[index]
        tcd.pos_start_sec = start_ts[index]
        tcd.pos_end_sec = end_ts[index]
        tcd.thumbnail_crops = self.thumbnail_info[index]
        tcd.notesHTML = self.get_notes_segment(index).allHTML()
        tcd.dialogue = self.GetUtteranceSpeakerPairs(index)
        return tcd

    def speaker_time_by_role(self, idx: int) -> dict[str, float]:
        start_ts = self.start_ts[idx]
        end_ts = self.end_ts[idx]

        roles = self.roles
        total_dur = end_ts - start_ts

        part = self.transcript[
            (self.transcript['start timestamp [sec]'] >= start_ts)
            & (self.transcript['end timestamp [sec]'] <= end_ts)
        ]
        role_durations = part.groupby('role')['duration [sec]'].sum()
        return {role: float(role_durations.get(role, 0)) / total_dur for role in roles}


    def GetUtteranceSpeakerPairs(self, index: int):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]

        part = self.transcript[
            (self.transcript['start timestamp [sec]'] >= start_ts)
            & (self.transcript['end timestamp [sec]'] <= end_ts)
        ]

        utterances = part['text'].tolist()
        speakers = part['speaker'].tolist()
        start_times = part['start timestamp [sec]'].tolist()
        end_times = part['end timestamp [sec]'].tolist()

        return [{'text': u, 'speaker': s, 'start_time': st, 'end_time': et} for s, u, st, et in zip(speakers, utterances, start_times, end_times)]