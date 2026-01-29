import subprocess
import threading
import sys

from collections.abc import Callable
from subprocess import CompletedProcess
from pathlib import Path
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant

transcript_scripts_dir = Path('../preprocessing/transcript').resolve()

def popen_and_call(on_exit: Callable[[int], None],
                   on_output: Callable[[str], None], cmd: list, cwd: str) -> None:

    def run_in_thread(on_exit: Callable[[int], None],
                      on_output: Callable[[str], None], cmd: list, cwd: str) -> None:

        proc = subprocess.Popen(cmd,
                                cwd=cwd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1,
                                universal_newlines=True,
                                )
        for line in proc.stdout:
            on_output(line.rstrip())

        return_code = proc.wait()
        on_exit(return_code)

    thread = threading.Thread(target=run_in_thread, args=(on_exit, on_output, cmd, cwd))
    thread.start()
    return thread


class PreprocessingPipeline(QObject):
    transcriptGlobalCompleted = pyqtSignal(int)  # noqa: N815
    transcriptRecordingCompleted = pyqtSignal(int)  # noqa: N815
    runningStatusChanged = pyqtSignal()  # noqa: N815
    globalTranscriptReadyChanged = pyqtSignal()  # noqa: N815
    recordingTranscriptReadyChanged = pyqtSignal()  # noqa: N815
    stdOutLine = pyqtSignal(str)  # noqa: N815

    def __init__(self, meta_file: Path, root_dir: Path, parent: object = None) -> None:
        super().__init__(parent)

        self.meta_file = meta_file
        self.root_dir = root_dir
        self.active_thread = None
        self.transcriptGlobalCompleted.connect(self.runningStatusChanged)
        self.transcriptRecordingCompleted.connect(self.runningStatusChanged)

        self._global_transcript_ready = False
        self._recording_transcript_ready = False

    @pyqtSlot(dict)
    def reevaluate_pipeline_status(self, manifest: dict) -> None:
        self._global_transcript_ready = 'audio' in manifest['sources']
        self.globalTranscriptReadyChanged.emit()

        self._recording_transcript_ready = 'transcript' in manifest['artifacts']
        self.recordingTranscriptReadyChanged.emit()

    @pyqtProperty(bool, notify=runningStatusChanged)
    def pipeline_running(self) -> str:
        return self.active_thread is not None and self.active_thread.is_alive()

    @pyqtProperty(bool, notify=globalTranscriptReadyChanged)
    def global_transcript_ready(self) -> bool:
        return self._global_transcript_ready

    @pyqtProperty(bool, notify=recordingTranscriptReadyChanged)
    def recording_transcript_ready(self) -> bool:
        return self._recording_transcript_ready

    @pyqtSlot()
    def run_transcript_global(self) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_transcript_global.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]
        if self.active_thread is not None and self.active_thread.is_alive():
            return

        self.active_thread = popen_and_call(self.transcriptGlobalCompleted.emit,
                                            self.stdOutLine.emit, cmd, transcript_scripts_dir)
        self.runningStatusChanged.emit()

    @pyqtSlot()
    def run_transcript_recording(self) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_transcript_recording.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]
        if self.active_thread is not None and self.active_thread.is_alive():
            return

        self.active_thread = popen_and_call(self.transcriptRecordingCompleted.emit,
                                            self.stdOutLine.emit, cmd, transcript_scripts_dir)
        self.runningStatusChanged.emit()
