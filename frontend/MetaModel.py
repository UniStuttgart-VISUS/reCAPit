import numpy as np
import json
from PyQt6.QtCore import QObject, QPointF, pyqtSlot


COLORMAPS = {
  "SET1": ["#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#ffff33","#a65628","#f781bf","#999999"],
  "SET2": ["#66c2a5","#fc8d62","#8da0cb","#e78ac3","#a6d854","#ffd92f","#e5c494","#b3b3b3"],
  "SET3": ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"],
  "PAIRED": ["#a6cee3","#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#fdbf6f","#ff7f00","#cab2d6","#6a3d9a","#ffff99","#b15928"],
  "ACCENT": ["#7fc97f","#beaed4","#fdc086","#ffff99","#386cb0","#f0027f","#bf5b17","#666666"],
  "TABLEAU": ["#4e79a7","#f28e2c","#e15759","#76b7b2","#59a14f","#edc949","#af7aa1","#ff9da7","#9c755f","#bab0ab"],
  "CATEGORY10": ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"],
  "OBSERVABLE10": ["#4269d0","#efb118","#ff725c","#6cc5b0","#3ca951","#ff8ab7","#a463f2","#97bbf5","#9c6b4e","#9498a0"]
}

class MetaModel(QObject):
    def __init__(self, root_dir, meta, parent=None):
        super().__init__(parent)

        aois = json.load(open(root_dir / meta['areas_of_interests'], 'r'))

        width = aois['imageWidth']
        height = aois['imageHeight']

        self.shapes = {}

        for s in aois['shapes']:
            points = np.array(s['points'])
            norm_x = points[:, 0] / width
            norm_y = points[:, 1] / height
            norm_points = np.stack((norm_x, norm_y), axis=1)

            self.shapes[s['label']] = {'points': norm_points, 'shape_type': s['shape_type']}

        self.colormap_aoi = COLORMAPS[meta['visualization']['colormap_aoi']]
        self.roles = meta['roles']
        self.ids = [r['id'] for r in meta['recordings']]
        self.audio_src = str(root_dir / meta['audio'])

    @pyqtSlot(str, result=list)
    def AoiPolygonPoints(self, aoi_name):
        return [QPointF(*p) for p in self.shapes[aoi_name]['points']]

    @pyqtSlot(result=str)
    def AudioSource(self):
        return self.audio_src

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
