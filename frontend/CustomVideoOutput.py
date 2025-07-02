from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QVariant, Qt, QUrl
from PyQt6.QtMultimedia import QVideoSink, QMediaPlayer, QVideoFrame
from PyQt6.QtQuick import QQuickItem, QQuickPaintedItem


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