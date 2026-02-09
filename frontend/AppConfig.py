import numpy as np
import json
from pathlib import Path
from PyQt6.QtCore import QObject, QPointF, pyqtSlot, QUrl


def default_config() -> dict:
    return {
        'colormaps': {
            'areas_of_interests': 'Accent',
            'roles': 'Purples',
        },
        'multisampling': 4,
        'segments': {
            'display_dur_sec': 46.0,
            'min_dur_sec': 31.0,
        },
        'streamgraph': {
            'attention': {
                'label': '\ud83d\udc40 Gaze',
                'log_scale': False,
            },
            'movement': {
                'label': '\ud83d\udc4b Move',
                'log_scale': True,
            }
        },
        'timeline': {
            'mapped_fixations': {
                'merge_threshold_sec': 0.5,
            },
            'transcript': {
                'merge_threshold_sec': 1.0,
            }
        },
        'video_overlay': {
            'attention': {
                'colormap': 'CET_L8'
            },
            'movement': {
                'colormap': 'CET_L16',
            },
        },
    }

def load_aoi_shapes(path: str) -> dict[str, dict]:
    with open(path) as f:
        aoi_data = json.load(f)
        width = aoi_data['imageWidth']
        height = aoi_data['imageHeight']
        shapes = {}

        for s in aoi_data['shapes']:
            points = np.array(s['points'])
            norm_x = points[:, 0] / width
            norm_y = points[:, 1] / height
            norm_points = np.stack((norm_x, norm_y), axis=1)
            shapes[s['label']] = {'points': norm_points, 'shape_type': s['shape_type']}
        return shapes


class AppConfig(QObject):
    def __init__(self, recording_info: dict[str, dict],
                 roles: list[str],
                 aoi_path: str,
                 user_config: dict[str, dict],
                 export_dir: Path,
                 event_subtypes: dict[str, set], parent=None):
        super().__init__(parent)

        self.export_dir = export_dir
        self.shapes = load_aoi_shapes(aoi_path)

        self.user_config = user_config
        self.event_subtypes = event_subtypes
        self.roles = roles
        self.ids = [r['id'] for r in recording_info]
        self.id2roles = {r['id']: r['role'] for r in recording_info}

    def export_user_config(self, path: Path) -> bool:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=4)
                return True
        except ValueError:
            return False

    def speaker_role(self, speaker_id: str) -> str:
        return self.id2roles.get(speaker_id, 'na')

    @pyqtSlot(result=list)
    def GetMultiTimeLabels(self) -> list:
        return [val['label'] for val in self.user_config['streamgraph'].values()]

    @pyqtSlot(result=float)
    def SegmentMinDurSec(self):
        return self.user_config['segments']['min_dur_sec']

    @pyqtSlot(result=float)
    def SegmentDisplayDurSec(self):
        return self.user_config['segments']['display_dur_sec']

    @pyqtSlot(str, result=list)
    def AoiPolygonPoints(self, aoi_name):
        return [QPointF(*p) for p in self.shapes[aoi_name]['points']]

    @pyqtSlot('QVariant')
    def SetUserConfig(self, user_config_js):
        user_config_dict = user_config_js.toVariant()
        if isinstance(user_config_dict, dict):
            self.user_config = user_config_dict
            self.user_config['multisampling'] = int(self.user_config['multisampling'])
        else:
            raise TypeError("QJSValue does not contain an object that can be converted to a dict.")

    @pyqtSlot(result='QVariant')
    def UserConfig(self):
        return self.user_config

    @pyqtSlot(result=QUrl)
    def ExportDir(self):
        return QUrl.fromLocalFile(self.export_dir.as_posix())

    @pyqtSlot(str, result=str)
    def ColormapOfOverlay(self, name):
        return self.user_config['video_overlay'][name]["colormap"]

    @pyqtSlot(result='QVariantMap')
    def ColormapCategories(self):
        return {
            'areas_of_interests': {'colormap': self.user_config['colormaps']['areas_of_interests'], 'labels': self.Labels()},
            'roles': {'colormap': self.user_config['colormaps']['roles'], 'labels': self.Roles()}
        }

    @pyqtSlot(result=str)
    def ColormapAOI(self):
        return self.user_config['colormaps']['areas_of_interests']

    @pyqtSlot(result=str)
    def ColormapRole(self):
        #return ["#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486"]
        return self.user_config['colormaps']['roles']

    @pyqtSlot(result=list)
    def Identifiers(self):
        return self.ids

    @pyqtSlot(result=list)
    def Roles(self):
        return self.roles

    @pyqtSlot(int, result=str)
    def Label(self, index):
        return self.shapes[index]['label']

    @pyqtSlot(result=list)
    def Labels(self):
        return list(self.shapes.keys())

    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.shapes)
