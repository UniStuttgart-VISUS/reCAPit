import subprocess
import threading
import sys

from collections.abc import Callable
from subprocess import CompletedProcess
from pathlib import Path
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant

transcript_script_path = Path('../preprocessing/transcript').resolve()

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
    transcriptCompleted = pyqtSignal(int)  # noqa: N815
    pipelineRunningChanged = pyqtSignal()  # noqa: N815
    stdOutLine = pyqtSignal(str)  # noqa: N815

    def __init__(self, meta_file: Path, root_dir: Path, parent: object = None) -> None:
        super().__init__(parent)

        self.meta_file = meta_file
        self.root_dir = root_dir
        self.active_thread = None
        self.transcriptCompleted.connect(self.pipelineRunningChanged)

    @pyqtProperty(bool, notify=pipelineRunningChanged)
    def pipeline_running(self) -> str:
        return self.active_thread is not None and self.active_thread.is_alive()

    @pyqtSlot()
    def run_transcript(self) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_transcript_global.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]

        if self.active_thread is not None and self.active_thread.is_alive():
            return

        self.active_thread = popen_and_call(self.transcriptCompleted.emit,
                                            self.stdOutLine.emit, cmd, transcript_script_path)
        self.pipelineRunningChanged.emit()
