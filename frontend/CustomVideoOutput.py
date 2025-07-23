from PyQt6.QtCore import pyqtProperty
from PyQt6.QtMultimedia import QVideoSink
from PyQt6.QtQuick import QQuickPaintedItem


class CustomVideoOutput(QQuickPaintedItem):
    #positionChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_sink = QVideoSink()
        self.video_sink.videoFrameChanged.connect(self.onVideoFrameChanged)

    @pyqtProperty(QVideoSink)
    def videoSink(self):
        return self.video_sink

    def onVideoFrameChanged(self, frame):
        self.update()

    def paint(self, painter):
        pass