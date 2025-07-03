import numpy as np
import logging
import colorcet as cc

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtQuick import QQuickImageProvider


def get_colormap(name, n_colors=256):
    colormap = getattr(cc.cm, name)
    return colormap.resampled(n_colors)


def create_heatmap_img(heatmap, colormap=None):
    if colormap is None:
        colormap = get_colormap('plasma', 9)
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()

    heatmap = np.clip(heatmap, 0, 1)
    heatmap_img = colormap(heatmap)
    heatmap_img[..., 3] = heatmap

    heatmap_img = (255 * heatmap_img).astype(np.uint8)
    return heatmap_img


class HeatmapOverlayProvider(QQuickImageProvider):
    def __init__(self, files, cmap='CET_L8'):
        super(HeatmapOverlayProvider, self).__init__(QQuickImageProvider.ImageType.Image)
        self.files = files
        self.segments_start = []
        self.segments_end = []
        self.colormap = get_colormap(cmap, 9)

    def img_id(self, segment_idx):
        return f'{segment_idx:05d}' 
        
    def compute_overlay(self, start, end):
        mask = (self.files['start timestamp [sec]'] >= start) & (self.files['end timestamp [sec]'] <= end)

        if mask.sum() == 0:
            logging.warning(f'No heatmap found in time span {start} -- {end}!')
            return np.zeros_like(np.load(self.files.iloc[0]['filename']))

        arr = 0
        for _, row in self.files[mask].iterrows():
            arr += np.load(row['filename'])
        return arr / len(mask.index)

    def requestImage(self, img_id, requested_size):
        segment_idx = int(img_id)
        try: 
            self.img = create_heatmap_img(self.compute_overlay(self.segments_start[segment_idx], self.segments_end[segment_idx]), colormap=self.colormap)
            qimg = QImage(self.img.data, self.img.shape[1], self.img.shape[0], self.img.strides[0], QImage.Format.Format_RGBA8888)

            if requested_size.width() > 0 and requested_size.height() > 0:
                qimg = qimg.scaled(requested_size, Qt.KeepAspectRatio)
        except ValueError as err:
            qimg = QImage()
            print(err)

        return qimg, qimg.size()
