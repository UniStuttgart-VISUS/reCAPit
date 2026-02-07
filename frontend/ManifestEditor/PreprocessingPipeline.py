import subprocess
import threading
import sys

from collections.abc import Callable
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, QSize, pyqtSignal, pyqtSlot, QDir, pyqtProperty, Qt, QAbstractListModel, QModelIndex, QStringListModel, QVariant

transcript_scripts_dir = Path('../preprocessing/transcript').resolve()
video_scripts_dir = Path('../preprocessing/video/workspace').resolve()
gaze_scripts_dir = Path('../preprocessing/gaze').resolve()
notes_scripts_dir = Path('../preprocessing/notes').resolve()
segmentation_scripts_dir = Path('../preprocessing/segmentation').resolve()


class ProcessManager(QObject):
    completed = pyqtSignal(int)
    stdOutLine = pyqtSignal(str)  # noqa: N815

    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)
        self.process = None

    def start_process(self, cmd: list, cwd: str) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.process = QProcess(self)
        self.process.setWorkingDirectory(cwd)
        #self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.finished.connect(self.completed)
        self.process.start(cmd[0], cmd[1:])

    def _on_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode()
        for line in data.strip().split('\n'):
            print(line)
            self.stdOutLine.emit(line)

    def cleanup(self) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()


class PreprocessingPipeline(QObject):
    transcriptGlobalCompleted = pyqtSignal(int)  # noqa: N815
    transcriptRecordingCompleted = pyqtSignal(int)  # noqa: N815
    videoMovementCompleted = pyqtSignal(int)  # noqa: N815
    videoHeatmapGazeCompleted = pyqtSignal(int)  # noqa: N815
    videoHeatmapMoveCompleted = pyqtSignal(int)  # noqa: N815
    gazeAttentionCompleted = pyqtSignal(int)  # noqa: N815
    notesCompleted = pyqtSignal(int)  # noqa: N815
    segmentInitialCompleted = pyqtSignal(int)  # noqa: N815
    segmentRefineCompleted = pyqtSignal(int)  # noqa: N815
    segmentAttributesCompleted = pyqtSignal(int)  # noqa: N815
    gazeSurfaceMappingCompleted = pyqtSignal(int)  # noqa: N815
    gazeAOIMappingCompleted = pyqtSignal(int)  # noqa: N815
    runningStatusChanged = pyqtSignal()  # noqa: N815

    videoMovementReady = pyqtSignal()  # noqa: N815
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
        self.videoMovementCompleted.connect(self.runningStatusChanged)
        self.videoHeatmapGazeCompleted.connect(self.runningStatusChanged)
        self.videoHeatmapMoveCompleted.connect(self.runningStatusChanged)
        self.gazeAttentionCompleted.connect(self.runningStatusChanged)
        self.notesCompleted.connect(self.runningStatusChanged)
        self.segmentInitialCompleted.connect(self.runningStatusChanged)
        self.segmentRefineCompleted.connect(self.runningStatusChanged)
        self.segmentAttributesCompleted.connect(self.runningStatusChanged)
        self.gazeSurfaceMappingCompleted.connect(self.runningStatusChanged)
        self.gazeAOIMappingCompleted.connect(self.runningStatusChanged)

        self._global_transcript_ready = False
        self._recording_transcript_ready = False
        self._video_movement_ready = False

        self.process_manager = ProcessManager()
        self.process_manager.stdOutLine.connect(self.stdOutLine)

    @pyqtSlot(bool, bool, bool)
    def reevaluate_pipeline_status(self, global_transcript_ready:bool, video_movement_ready:bool, split_transcript_ready: bool) -> None:
        self._global_transcript_ready = global_transcript_ready
        self.globalTranscriptReadyChanged.emit()

        self._recording_transcript_ready = split_transcript_ready
        self.recordingTranscriptReadyChanged.emit()

        self._video_movement_ready = video_movement_ready
        self.videoMovementReady.emit()

    @pyqtProperty(bool, notify=runningStatusChanged)
    def pipeline_running(self) -> str:
        return self.active_thread is not None and self.active_thread.is_alive()

    @pyqtProperty(bool, notify=globalTranscriptReadyChanged)
    def global_transcript_ready(self) -> bool:
        return self._global_transcript_ready

    @pyqtProperty(bool, notify=recordingTranscriptReadyChanged)
    def recording_transcript_ready(self) -> bool:
        return self._recording_transcript_ready

    @pyqtProperty(bool, notify=videoMovementReady)
    def video_movement_ready(self) -> bool:
        return self._video_movement_ready

    @pyqtSlot(int, str, str, bool)
    def run_transcript_global(self, num_speakers: int, 
                              hf_token: str, device: str,
                              speaker_identification_enabled: bool) -> None:

        if not speaker_identification_enabled:
            num_speakers = 0
            hf_token = ''

        if device == 'GPU':
            device = 'cuda'
        elif device == 'CPU':
            device = 'cpu'

        cmd = [
            'uv', 'run', 'python', 'register_transcript_global.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--num_speakers', str(num_speakers),
            '--hf_token', str(hf_token),
            '--device', str(device),
        ]
        cmd.append('--show_output')

        self.process_manager.start_process(cmd, str(transcript_scripts_dir))
        self.process_manager.completed.connect(self.transcriptGlobalCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot()
    def run_transcript_recording(self) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_transcript_recording.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]
        self.process_manager.start_process(cmd, str(transcript_scripts_dir))
        self.process_manager.completed.connect(self.transcriptRecordingCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(float)
    def run_attention(self, window_size_sec:float) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_attention.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--window_size_sec', str(window_size_sec),
        ]
        cmd.append('--debug')
        print(' '.join(cmd))
        self.process_manager.start_process(cmd, str(gaze_scripts_dir))
        self.process_manager.completed.connect(self.gazeAttentionCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(str, int, str)
    def run_gaze_surf_mapping(self, rec_id: str, min_tags:int, april_tag_family:str) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_surface_fixations.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--rec_id', str(rec_id),
            '--min_tags', str(min_tags),
            '--april_tag_family', str(april_tag_family),
        ]
        cmd.append('--show_output')
        print(' '.join(cmd).replace('\\', '\\\\'))
        self.process_manager.start_process(cmd, str(gaze_scripts_dir))
        self.process_manager.completed.connect(self.gazeSurfaceMappingCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(str)
    def run_gaze_aoi_mapping(self, rec_id: str) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_mapped_fixations.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--rec_id', str(rec_id),
        ]
        self.process_manager.start_process(cmd, str(gaze_scripts_dir))
        self.process_manager.completed.connect(self.gazeAOIMappingCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(float, bool)
    def run_video_movement(self, downsampling_factor:float, detect_shadows:bool) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_movement.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--downsampling_factor', str(downsampling_factor),
        ]

        if detect_shadows:
            cmd.append('--detect_shadows')

        cmd.append('--show_output')

        self.process_manager.start_process(cmd, str(video_scripts_dir))
        self.process_manager.completed.connect(self.videoMovementCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(float, float)
    def run_video_heatmap_gaze(self, step_size:float, kernel_size:int) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_heatmaps_gaze.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--delta_step_sec', str(step_size),
            '--kernel_size', str(int(kernel_size)),
        ]

        cmd.append('--show_output')
        self.process_manager.start_process(cmd, str(video_scripts_dir))
        self.process_manager.completed.connect(self.videoHeatmapGazeCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(float, float)
    def run_video_heatmap_move(self, step_size:float, kernel_size:int) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_heatmaps_move.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--delta_step_sec', str(step_size),
            '--kernel_size', str(int(kernel_size)),
        ]

        cmd.append('--show_output')
        print(' '.join(cmd))
        self.process_manager.start_process(cmd, str(video_scripts_dir))
        self.process_manager.completed.connect(self.videoHeatmapMoveCompleted)
        self.runningStatusChanged.emit()


    @pyqtSlot()
    def run_notes(self) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_notes.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]
        self.runningStatusChanged.emit()

    @pyqtSlot(str, float, float)
    def run_segment_initial(self, input_signal:str,
                            downsampling_factor:float,
                            min_dur_sec: float) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_segment_initial.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--input_signal', str(input_signal),
            '--downsampling_factor', str(downsampling_factor),
            '--min_dur_sec', str(min_dur_sec),
        ]
        self.process_manager.start_process(cmd, str(segmentation_scripts_dir))
        self.process_manager.completed.connect(self.segmentInitialCompleted)
        self.runningStatusChanged.emit()


    @pyqtSlot(str, float, float)
    def run_segment_refine(self, similarity_threshold:float,
                            gap_threshold:float,
                            min_dur_sec: float) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_segment_refine.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--similarity_threshold', str(similarity_threshold),
            '--gap_threshold', str(gap_threshold),
            '--min_dur_sec', str(min_dur_sec),
        ]
        self.process_manager.start_process(cmd, str(segmentation_scripts_dir))
        self.process_manager.completed.connect(self.segmentRefineCompleted)
        self.runningStatusChanged.emit()

    @pyqtSlot(str, str)
    def run_segment_attributes(self,
                               gpt_model:str,
                               open_ai_key:str) -> None:
        cmd = [
            'uv', 'run', 'python', 'register_segment_attributes.py',
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
            '--gpt_model', str(gpt_model),
            '--target_segments', 'refined',
            #'--open_ai_key', str(open_ai_key),
        ]
        self.process_manager.start_process(cmd, str(segmentation_scripts_dir))
        self.process_manager.completed.connect(self.segmentsAttributesCompleted)
        self.runningStatusChanged.emit()
