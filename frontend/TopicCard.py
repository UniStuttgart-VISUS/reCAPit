from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QRectF
from PyQt6.QtMultimedia import QVideoSink
from ThumbnailModel import ThumbnailModel
import numpy as np
from dataclasses import asdict
from TranscriptRecord import TranscriptRecord
from TimelineSegment import DisplayState
from utils import extract_quotes

class TopicCardData(QObject):
    titleChanged = pyqtSignal()  # noqa: N815
    markedChanged = pyqtSignal()  # noqa: N815
    userNotesChanged = pyqtSignal()  # noqa: N815
    userQuotesChanged = pyqtSignal()  # noqa: N815
    labelsChanged = pyqtSignal()  # noqa: N815
    thumbnailAdded = pyqtSignal(QVideoSink, float, QRectF, str)  # noqa: N815
    dialogueChanged = pyqtSignal()  # noqa: N815
    displayStateChanged = pyqtSignal()  # noqa: N815
    indexChanged = pyqtSignal()  # noqa: N815

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.pos_start_sec = 0
        self.pos_end_sec = 0
        self.title = ""
        self.labels = []
        self.text_notes = ""
        self.text_quotes = ""
        self.text_quotes_formatted = ""
        self.thumbnail_crops = ThumbnailModel()
        self.dists_stats = {}
        self.marked = False
        self.segment_index = 0
        self.summary = ""
        self.notesHTML = ""
        self.video_overlays = []
        self.dialogue: list[TranscriptRecord] = []
        self.display_state: DisplayState = DisplayState.VISIBLE

    @pyqtProperty(list, notify=dialogueChanged)
    def Dialogue(self) -> list:
        return [asdict(d) for d in self.dialogue]

    @pyqtProperty(str, notify=displayStateChanged)
    def DisplayState(self) -> str:
        print(self.display_state)
        return str(self.display_state)

    @pyqtSlot(result=str)
    def NotesHTML(self) -> str:
        return self.notesHTML

    @pyqtProperty(int, notify=indexChanged)
    def SegmentIndex(self) -> int:
        return self.segment_index

    @pyqtProperty(str, notify=titleChanged)
    def Title(self):
        return self.title

    @Title.setter
    def Title(self, val: str) -> str:
        if val != self.title:
            self.title = val
            self.titleChanged.emit()

    @pyqtSlot(result=str)
    def Summary(self):
        return self.summary

    @pyqtSlot(result='QVariantMap')
    def VideoOverlays(self):
        return self.video_overlays

    @pyqtProperty(list, notify=labelsChanged)
    def Labels(self):
        return self.labels

    @pyqtSlot(str)
    def add_label(self, label: str):
        self.extend_labels([label])

    @pyqtSlot(list)
    def extend_labels(self, labels: list[str]) -> None:
        if len(labels) > 0:
            self.labels.extend(labels)
            self.labelsChanged.emit()

    @pyqtSlot(result=bool)
    def ToggleMark(self):
        self.Marked = not self.Marked
        return self.Marked

    @pyqtProperty(bool, notify=markedChanged)
    def Marked(self):
        return self.marked

    @Marked.setter
    def Marked(self, val: bool):
        if val != self.marked:
            self.marked = val
            self.markedChanged.emit()

    @pyqtProperty(str, notify=userQuotesChanged)
    def UserQuotesFormatted(self):
        return self.text_quotes_formatted

    @pyqtProperty(str, notify=userQuotesChanged)
    def UserQuotes(self):
        return self.text_quotes

    @UserQuotes.setter
    def UserQuotes(self, val: str):
        print(val)
        if self.text_quotes != val:
            self.text_quotes = val

            out = extract_quotes(val, self.dialogue)
            new_labels = [q['label'] for q in out.quotes if q['label'] not in self.labels]

            self.text_quotes_formatted = out.formatted

            self.extend_labels(new_labels)
            self.userQuotesChanged.emit()

    @pyqtProperty(str, notify=userNotesChanged)
    def UserNotes(self):
        return self.text_notes

    @UserNotes.setter
    def UserNotes(self, val: str):
        if self.text_notes != val:
            self.text_notes = val
            self.userNotesChanged.emit()

    @pyqtSlot(result=ThumbnailModel)
    def ThumbnailCrops(self):
        return self.thumbnail_crops

    @pyqtSlot(result=float)
    def PosEndSec(self):
        return self.pos_end_sec

    @pyqtSlot(result=float)
    def PosStartSec(self):
        return self.pos_start_sec

    @pyqtSlot(result='QVariantMap')
    def DistributionsStatistics(self):
        return self.dists_stats