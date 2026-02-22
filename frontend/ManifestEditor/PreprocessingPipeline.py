import json
from functools import partial
from . import Manifest

from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, pyqtSignal, pyqtSlot, pyqtProperty, QAbstractListModel, Qt, QModelIndex, QVariant
from helper.manifest_manager import ManifestManager, Recording

scripts_root = Path('../preprocessing').resolve()
transcript_scripts_dir = Path('../preprocessing/transcript').resolve()
video_scripts_dir = Path('../preprocessing/video').resolve()
gaze_scripts_dir = Path('../preprocessing/gaze').resolve()
notes_scripts_dir = Path('../preprocessing/notes').resolve()
segmentation_scripts_dir = Path('../preprocessing/segmentation').resolve()


def get_merged_scripts_info(target_dirs: list[str]) -> list[dict]:
    scripts_info = []
    for dir_name in target_dirs:
        with open(scripts_root / dir_name / 'scripts_info.json') as file:
            scripts_info.extend(json.load(file))
    return scripts_info

def get_argument_configs(script_info: dict) -> dict[str, dict]:
    bool_configs = {}
    int_configs = {}
    real_configs = {}
    string_configs = {}
    selection_configs = {}

    for arg_name, arg_data in script_info['script_args'].items():
        if 'config' not in arg_data:
            continue

        arg_data['config']['id'] = arg_name

        if arg_data['type'] == 'bool':
            arg_data['config']['value'] = 'yes' if arg_data['default'] else 'no'
            bool_configs[arg_name] = arg_data['config']

        elif arg_data['type'] == 'real':
            arg_data['config']['value'] = arg_data['default']
            real_configs[arg_name] = arg_data['config']

        elif arg_data['type'] == 'int':
            arg_data['config']['value'] = arg_data['default']
            int_configs[arg_name] = arg_data['config']

        elif arg_data['type'] == 'string':
            arg_data['config']['value'] = arg_data['default']
            string_configs[arg_name] = arg_data['config']

        elif arg_data['type'] == 'selection':
            arg_data['config']['value'] = arg_data['default']
            selection_configs[arg_name] = arg_data['config']

    return {
        'bool': bool_configs,
        'int': int_configs,
        'real': real_configs,
        'string': string_configs,
        'selection': selection_configs,
    }

class ProcessingScriptsModel(QAbstractListModel):
    TitleRole = Qt.ItemDataRole.UserRole + 1
    DescriptionRole = Qt.ItemDataRole.UserRole + 2
    DependenciesRole = Qt.ItemDataRole.UserRole + 3
    RealParamsRole = Qt.ItemDataRole.UserRole + 4
    IntParamsRole = Qt.ItemDataRole.UserRole + 5
    BoolParamsRole = Qt.ItemDataRole.UserRole + 6
    TextParamsRole = Qt.ItemDataRole.UserRole + 7
    SelectionParamsRole = Qt.ItemDataRole.UserRole + 8
    IsRunningRole = Qt.ItemDataRole.UserRole + 9
    DependenciesSatisfiedRole = Qt.ItemDataRole.UserRole + 10
    OutputRole = Qt.ItemDataRole.UserRole + 11
    ScriptTargetRole = Qt.ItemDataRole.UserRole + 12
    ScriptDirRole = Qt.ItemDataRole.UserRole + 13

    def __init__(self, scripts_info: dict, manifest: Manifest.Manifest, parent: object = None) -> None:
        super().__init__(parent)

        self.manifest_manager = manifest.get_manifest_manager()
        self.scripts_info = scripts_info
        self.is_running = [False] * len(self.scripts_info)
        self.reset()

    @pyqtSlot()
    def reset(self) -> None:
        self.beginResetModel()
        # We inject additional parameters at runtime.
        # For example, with scripts targeting recordings, we need an additional recording selection  # noqa: E501
        self.add_dynamic_args()
        self.script_configs = [get_argument_configs(si) for si in self.scripts_info]
        self.endResetModel()

    def add_dynamic_args(self) -> None:
        rec_ids = [rec.rec_id for rec in self.manifest_manager.get_recordings()]

        # When there are no recordings yet defined
        if len(rec_ids) == 0:
            return

        for idx in range(len(self.scripts_info)):
            if self.scripts_info[idx]['script_target'] == 'recording':
                arg_info = {'type': 'selection',
                            'default': rec_ids[0],
                            'config': {
                                'name': 'Recording Id',
                                'options': rec_ids,
                            }}
                self.scripts_info[idx]['script_args']['--rec_id'] = arg_info

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: ARG002, B008, N802
        return len(self.scripts_info)

    @pyqtSlot(str, result=int)
    def str2role(self, role_str: str) -> int:  # noqa: N802
        return {
            'scriptTitle': self.TitleRole,
            'scriptDescription': self.DescriptionRole,
            'scriptDependencies': self.DependenciesRole,
            'scriptRealParams': self.RealParamsRole,
            'scriptIntParams': self.IntParamsRole,
            'scriptBoolParams': self.BoolParamsRole,
            'scriptTextParams': self.TextParamsRole,
            'scriptSelectionParams': self.SelectionParamsRole,
            'scriptRunning': self.IsRunningRole,
            'scriptDependenciesSatisfied': self.DependenciesSatisfiedRole,
            'scriptOutput': self.OutputRole,
            'scriptTarget': self.ScriptTargetRole,
            'scriptDir': self.ScriptDirRole,
        }.get(role_str, -1)

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.TitleRole: b'scriptTitle',
            self.DescriptionRole: b'scriptDescription',
            self.DependenciesRole: b'scriptDependencies',
            self.RealParamsRole: b'scriptRealParams',
            self.IntParamsRole: b'scriptIntParams',
            self.BoolParamsRole: b'scriptBoolParams',
            self.TextParamsRole: b'scriptTextParams',
            self.SelectionParamsRole: b'scriptSelectionParams',
            self.IsRunningRole: b'scriptRunning',
            self.DependenciesSatisfiedRole: b'scriptDependenciesSatisfied',
            self.OutputRole: b'scriptOutput',
            self.ScriptTargetRole: b'scriptTarget',
            self.ScriptDirRole: b'scriptDir',
        }

    def is_all_data_valid(self, row: int, data_key: str) -> bool:
        data_exist = self.eval_data_validity(row, data_key)
        sources_exist = all(d['exists'] for d in data_exist['sources'])
        artifacts_exist = all(d['exists'] for d in data_exist['artifacts'])
        return sources_exist and artifacts_exist

    def eval_data_validity(self, row: int, data_key: str) -> dict:
        data = self.scripts_info[row].get(data_key, {})

        global_data = {
            'sources': [
                {'name': d, 'exists': self.manifest_manager.has_source(d)}
                for d in data.get('sources', [])
            ],
            'artifacts': [
                {'name': d, 'exists': self.manifest_manager.has_artifact(d)}
                for d in data.get('artifacts', [])
            ],
        }

        if 'recordings' in data:
            if '--rec_id' in self.script_configs[row]['selection']:
                rec_id = self.script_configs[row]['selection']['--rec_id']['value']
                rec = self.manifest_manager.get_recording(rec_id)

                rec_data = {
                    'sources': [
                        {'name': f'{d} :: {rec_id}', 'exists': rec.has_source(d)}
                        for d in data['recordings'].get('sources', [])
                    ],
                    'artifacts': [
                        {'name': f'{d} :: {rec_id}', 'exists': rec.has_artifact(d)}
                        for d in data['recordings'].get('artifacts', [])
                    ],
                }
            else:
                # Dummy recording data to show user that recordings need to be added
                rec_data = {'sources': [{'name': 'has recordings', 'exists': False}],
                            'artifacts': []}
        else:
            rec_data = {'sources': [], 'artifacts': []}

        return {
            'sources': global_data['sources'] + rec_data['sources'],
            'artifacts': global_data['artifacts'] + rec_data['artifacts'],
        }

    def eval_output(self, row: int) -> dict:
        output = self.scripts_info[row].get('output', {})
        return {
            'sources': [
                {'name': d, 'exists': self.manifest_manager.has_source(d)}
                for d in output.get('sources', [])
            ],
            'artifacts': [
                {'name': d, 'exists': self.manifest_manager.has_artifact(d)}
                for d in output.get('artifacts', [])
            ],
        }

    @pyqtSlot(int, str, 'QVariant')
    def set_script_arg(self, row: int, arg_id: str, value: object) -> None:
        arg_type = self.scripts_info[row]['script_args'][arg_id]['type']
        coerce = {'real': float, 'int': int, 'selection': str, 'bool': str, 'string': str}
        self.script_configs[row][arg_type][arg_id]['value'] = coerce[arg_type](value)

        if arg_id == '--rec_id':
            index = self.createIndex(row, 0)
            self.dataChanged.emit(index, index, [self.DependenciesRole,
                                                 self.DependenciesSatisfiedRole,
                                                 self.OutputRole])

    def get_cmd_args(self, row:int) -> list[str]:
        if row >= self.rowCount():
            raise ValueError

        cmd = []
        index = self.createIndex(row, 0)

        for c in self.data(index, ProcessingScriptsModel.RealParamsRole):
            cmd.append(str(c['id']))
            cmd.append(str(c['value']))

        for c in self.data(index, ProcessingScriptsModel.IntParamsRole):
            cmd.append(str(c['id']))
            cmd.append(str(c['value']))

        for c in self.data(index, ProcessingScriptsModel.TextParamsRole):
            cmd.append(str(c['id']))
            cmd.append(str(c['value']))

        bool_params = self.data(index, ProcessingScriptsModel.BoolParamsRole)
        cmd.extend(str(c['id']) for c in bool_params if c['value'] == 'yes')

        for c in self.data(index, ProcessingScriptsModel.SelectionParamsRole):
            cmd.append(str(c['id']))
            cmd.append(str(c['value']))
        return cmd

    def data(self, index: QModelIndex, role: int):  # noqa: PLR0911
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        row = index.row()

        if role == self.TitleRole:
            return self.scripts_info[row]['title']
        if role == self.DescriptionRole:
            return self.scripts_info[row]['description']
        if role == self.DependenciesSatisfiedRole:
            return self.is_all_data_valid(row, 'dependencies')
        if role == self.DependenciesRole:
            return self.eval_data_validity(row, 'dependencies')
        if role == self.RealParamsRole:
            return list(self.script_configs[row]['real'].values())
        if role == self.IntParamsRole:
            return list(self.script_configs[row]['int'].values())
        if role == self.BoolParamsRole:
            return list(self.script_configs[row]['bool'].values())
        if role == self.SelectionParamsRole:
            return list(self.script_configs[row]['selection'].values())
        if role == self.TextParamsRole:
            return list(self.script_configs[row]['string'].values())
        if role == self.IsRunningRole:
            return self.is_running[row]
        if role == self.OutputRole:
            return self.eval_data_validity(row, 'output')
        if role == self.ScriptTargetRole:
            return self.scripts_info[row]['script_target']
        if role == self.ScriptDirRole:
            return self.scripts_info[row]['script_dir']
        return None

    @pyqtSlot(int)
    def toggle_running(self, row: int) -> bool:
        index = self.createIndex(row, 0)
        self.is_running[row] = not self.is_running[row]
        self.dataChanged.emit(index, index, [self.IsRunningRole])

    @pyqtSlot(int, bool)
    def set_running(self, row: int, is_running:bool) -> bool:
        index = self.createIndex(row, 0)
        if self.is_running[row] != is_running:
            self.is_running[row] = is_running
            self.dataChanged.emit(index, index, [self.IsRunningRole])


class ProcessManager(QObject):
    completed = pyqtSignal(int)
    started = pyqtSignal()
    stdOutLine = pyqtSignal(str)  # noqa: N815
    stdErrLine = pyqtSignal(str)  # noqa: N815

    def __init__(self, parent: object = None) -> None:
        super().__init__(parent)
        self.process = None

    def start_process(self, cmd: list, cwd: str) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            return

        self.process = QProcess(self)
        self.process.setWorkingDirectory(cwd)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.started.connect(self.started)
        self.process.finished.connect(self.completed)
        self.process.start(cmd[0], cmd[1:])

    def _on_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        for line in data.strip().split('\n'):
            self.stdOutLine.emit(line)

    def _on_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        for line in data.strip().split('\n'):
            self.stdErrLine.emit(line)

    def is_running(self) -> bool:
        return self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning

    def cleanup(self) -> None:
        if self.is_running():
            print('is running')
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
        else:
            print('is not running')


class PreprocessingPipeline(QObject):
    stdOutLine = pyqtSignal(str)  # noqa: N815
    stdErrLine = pyqtSignal(str)  # noqa: N815
    runningStatusChanged = pyqtSignal()  # noqa: N815

    def __init__(self, manifest: Manifest.Manifest, meta_file: Path, root_dir: Path, parent: object = None) -> None:
        super().__init__(parent)

        self.meta_file = str(meta_file)
        self.root_dir = root_dir

        self.process_manager = ProcessManager()
        self.process_manager.stdOutLine.connect(self.stdOutLine)
        self.process_manager.stdErrLine.connect(self.stdErrLine)

        self.process_manager.started.connect(self.runningStatusChanged)
        self.process_manager.completed.connect(self.runningStatusChanged)

        self.scripts_info = get_merged_scripts_info(['video', 'transcript', 'gaze',
                                                     'notes', 'segmentation'])
        self.scripts_model = ProcessingScriptsModel(self.scripts_info, manifest)

        # TODO @moe: This works for now but doing a full reset
        # every time a property changes is overkill
        manifest.manifestChanged.connect(self.scripts_model.reset)

    @pyqtSlot(result=ProcessingScriptsModel)
    def get_scripts_model(self) -> ProcessingScriptsModel:
        return self.scripts_model

    @pyqtSlot()
    def terminate_current_process(self) -> None:
        self.process_manager.cleanup()

    @pyqtSlot(int)
    def run_script(self, script_idx: int) -> None:
        script_info = self.scripts_info[script_idx]

        cmd = [
            'uv', 'run', 'python',
            script_info['script_name'],
            '--manifest', str(self.meta_file),
            '--root_dir', str(self.root_dir),
        ]

        cmd.extend(self.scripts_model.get_cmd_args(script_idx))
        print(' '.join(cmd))

        script_dir = scripts_root / script_info['script_dir']
        set_running_false = partial(self.scripts_model.set_running, script_idx, False)

        self.process_manager.completed.disconnect()
        self.process_manager.completed.connect(self.runningStatusChanged)
        self.process_manager.completed.connect(set_running_false)

        self.scripts_model.set_running(script_idx, True)
        self.process_manager.start_process(cmd, str(script_dir))


    @pyqtProperty(bool, notify=runningStatusChanged)
    def pipeline_running(self) -> bool:
        return self.process_manager.is_running()

    @pyqtProperty('QVariantMap', notify=runningStatusChanged)
    def current_process_info(self) -> dict[str, str]:
        if self.process_manager.is_running():
            pid = self.process_manager.process.processId()
            args = ' '.join(self.process_manager.process.arguments())
            program = self.process_manager.process.program()
        else:
            pid = -1
            program = ''
            args = ''

        return {'pid': pid, 'program': program, 'args': args}


