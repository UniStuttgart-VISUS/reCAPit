import numpy as np
import json
import logging
from PyQt6.QtCore import QObject, QPointF, pyqtSlot

COLORMAPS = {
  "Set1": ["#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#ffff33","#a65628","#f781bf","#999999"],
  "Set2": ["#66c2a5","#fc8d62","#8da0cb","#e78ac3","#a6d854","#ffd92f","#e5c494","#b3b3b3"],
  "Set3": ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"],
  "Paired": ["#a6cee3","#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#fdbf6f","#ff7f00","#cab2d6","#6a3d9a","#ffff99","#b15928"],
  "Accent": ["#7fc97f","#beaed4","#fdc086","#ffff99","#386cb0","#f0027f","#bf5b17","#666666"],
  "Tableau10": ["#4e79a7","#f28e2c","#e15759","#76b7b2","#59a14f","#edc949","#af7aa1","#ff9da7","#9c755f","#bab0ab"],
  "Category10": ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"],
  "Observable10": ["#4269d0","#efb118","#ff725c","#6cc5b0","#3ca951","#ff8ab7","#a463f2","#97bbf5","#9c6b4e","#9498a0"],
  "Purple6": ["#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486"]
}

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
        self.init_colormaps(user_config)
        self.event_subtypes = event_subtypes
        self.roles = manifest['roles']
        self.ids = [r['id'] for r in manifest['recordings']]
        self.id2roles = {r['id']: r['role'] for r in manifest['recordings']}
        self.audio_src = manifest['sources']['audio']['path']

    def init_colormaps(self, user_config):
        self.colormaps = {name: COLORMAPS[cm] for name, cm in user_config['colormaps'].items()}
        self.colormap_aoi = COLORMAPS[user_config['colormaps']['areas_of_interests']]

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
            print(user_config_dict)
            self.user_config = user_config_dict
            self.init_colormaps(user_config_dict)
        else:
            raise TypeError("QJSValue does not contain an object that can be converted to a dict.")

    @pyqtSlot(result='QVariant')
    def UserConfig(self):
        return self.user_config

    @pyqtSlot(result=str)
    def AudioSource(self):
        return self.audio_src

    @pyqtSlot(str, result='QVariantMap')
    def GetColormap(self, data_type):
        if data_type == 'transcript':
            colors = self.ColormapRole()
            domain = self.Roles()
        elif data_type == 'mapped_fixations':
            colors = self.ColormapAOI()
            domain = self.Labels()
        else:
            colors = COLORMAPS["CATEGORY10"]

        step = len(colors) // len(domain)

        if step == 0:
            logging.warning("Not enough colors for all domains!");
            fill_colors = ['#000'] * (len(domain) - len(colors)) 
            colors = colors + fill_colors
            step = 1

        mapping = {v: colors[idx*step] for idx, v in enumerate(domain)}
        return mapping

    @pyqtSlot(str, result=str)
    def CategoryOfTimeSeries(self, key):
        return self.manifest['artifacts']['multi_time'][key]['categories']

    @pyqtSlot(result='QVariantMap')
    def ColormapCategories(self):
        return {
            'areas_of_interests': {'colormap': self.colormaps['areas_of_interests'], 'labels': self.Labels()},
            'roles': {'colormap': self.colormaps['roles'], 'labels': self.Roles()}
        }

    @pyqtSlot(result=list)
    def ColormapAOI(self):
        return self.colormap_aoi

    @pyqtSlot(result=list)
    def ColormapRole(self):
        return ["#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486"]

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
