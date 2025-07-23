from PyQt6.QtCore import QObject, pyqtSlot
import numpy as np

class TopicCardData(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pos_start_sec = 0
        self.pos_end_sec = 0
        self.title = ""
        self.labels = []
        self.text_dialogues = ""
        self.text_notes = ""
        self.thumbnail_crops = []
        self.speaker_role_time_distr = {}
        self.aoi_activity_distr = {}
        self.aoi_attention_distr = {}
        self.marked = False
        self.segment_index = 0
        self.keywords_dialogue = []
        self.heatmap_gaze_src = ""
        self.heatmap_move_src = ""
        self.summary = ""

    @pyqtSlot(result=str)
    def HeatmapGazeSource(self):
        return self.heatmap_gaze_src

    @pyqtSlot(result=str)
    def HeatmapMoveSource(self):
        return self.heatmap_move_src

    @pyqtSlot(result=int)
    def SegmentIndex(self):
        return self.segment_index

    @pyqtSlot(result=str)
    def Title(self):
        return self.title

    @pyqtSlot(result=str)
    def Summary(self):
        return self.summary

    @pyqtSlot(result=list)
    def Labels(self):
        return self.labels

    @pyqtSlot(result=bool)
    def ToggleMark(self):
        self.marked = not self.marked
        return self.marked

    @pyqtSlot(result=bool)
    def IsMarked(self):
        return self.marked

    @pyqtSlot(result=str)
    def TextDialoguesOriginal(self):
        return self.text_dialogues['original']

    @pyqtSlot(result=str)
    def TextDialoguesFormatted(self):
        return self.text_dialogues['formatted']

    @pyqtSlot(result=str)
    def TextNotes(self):
        return self.text_notes

    @pyqtSlot(list)
    def SetThumbnailCrops(self, paths):
        self.thumbnail_crops = paths

    @pyqtSlot(result=list)
    def KeywordsDialogue(self):
        return self.keywords_dialogue

    @pyqtSlot(result=str)
    def KeywordsDialogueString(self):
        return ', '.join(self.keywords_dialogue)

    @pyqtSlot(result=list)
    def ThumbnailCrops(self):
        return self.thumbnail_crops

    @pyqtSlot(result=float)
    def PosEndSec(self):
        return self.pos_end_sec

    @pyqtSlot(result=float)
    def PosStartSec(self):
        return self.pos_start_sec

    @pyqtSlot(result='QVariantMap')
    def SpeakerTimeDistribution(self):
        return self.speaker_role_time_distr

    @pyqtSlot(result=str)
    def DominantSpeakerRoleTime(self):
        keys = list(self.speaker_role_time_distr.keys())
        prob = list(self.speaker_role_time_distr.values())

        if len(prob) > 0:
            idx = np.argmax(prob)
            return keys[idx]
        return ""

    @pyqtSlot(result='QVariantMap')
    def AoiActivityDistribution(self):
        return self.aoi_activity_distr

    @pyqtSlot(result='QVariantMap')
    def AoiAttentionDistribution(self):
        return self.aoi_attention_distr