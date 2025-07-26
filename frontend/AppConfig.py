import numpy as np
import json
from PyQt6.QtCore import QObject, QPointF, pyqtSlot


class AppConfig(QObject):
    def __init__(self, manifest, user_config, event_subtypes, parent=None):
        super().__init__(parent)

        aois = json.load(open(manifest['sources']['areas_of_interests']['path'], 'r'))

        width = aois['imageWidth']
        height = aois['imageHeight']

        self.shapes = {}

        for s in aois['shapes']:
            points = np.array(s['points'])
            norm_x = points[:, 0] / width
            norm_y = points[:, 1] / height
            norm_points = np.stack((norm_x, norm_y), axis=1)

            self.shapes[s['label']] = {'points': norm_points, 'shape_type': s['shape_type']}

        self.user_config = user_config
        self.manifest = manifest
        self.event_subtypes = event_subtypes
        self.roles = manifest['roles']
        self.ids = [r['id'] for r in manifest['recordings']]
        self.id2roles = {r['id']: r['role'] for r in manifest['recordings']}
        self.audio_src = manifest['sources']['audio']['path']

        
    def export_user_config(self, path):
        try:
            with open(path, 'w') as f:
                json.dump(self.user_config, f, indent=4)
                return True
        except Exception:
            return False

    def speaker_role(self, speaker_id):
        return self.id2roles[speaker_id]

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

    @pyqtSlot(result=str)
    def AudioSource(self):
        return self.audio_src

    @pyqtSlot(int, str, result=str)
    def GetRecCategories(self, rec_index, data_type):
        art = self.manifest['recordings'][rec_index]['artifacts']
        if data_type not in art:
            return ""
        x = art[data_type]['categories']
        return x

    @pyqtSlot(str, result=str)
    def CategoryOfTimeSeries(self, key):
        return self.manifest['artifacts']['multi_time'][key]['categories']

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
        self.user_config['colormaps']['areas_of_interests']

    @pyqtSlot(result=str)
    def ColormapRole(self):
        #return ["#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486"]
        self.user_config['colormaps']['roles']

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
