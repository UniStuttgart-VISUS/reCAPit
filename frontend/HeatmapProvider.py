import numpy as np
import logging
import colorcet as cc

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtQuick import QQuickImageProvider


def get_colormap(name="CET_L8", n_colors=10):
    # 1. Convert hex to RGB in [0, 1]
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))

    raw_hex = cc.palette[name]
    rgb_array = np.array([hex_to_rgb(h) for h in raw_hex])  # shape (256, 3)

    # 2. Interpolate to exactly `bins` colors
    positions = np.linspace(0, len(rgb_array)-1, n_colors)
    quantized_rgb = np.array([
        np.interp(positions, np.arange(len(rgb_array)), rgb_array[:, i])
        for i in range(3)
    ]).T  # shape (bins, 3)

    quantized_rgba = np.hstack([quantized_rgb, np.full((n_colors, 1), 1.0)])  # shape: (bins, 4)

    # 3. Return a function that maps val in [0, 1] → RGBA tuple

    def cmap(values):
        values_clipped = np.clip(values.flatten(), 0, 1)
        indices = np.floor(values_clipped * n_colors).astype(int)
        indices = np.clip(indices, 0, n_colors - 1)
        colors = quantized_rgba[indices]  # shape: (..., 4)
        return colors.reshape(*values.shape, 4)  # Reshape to original shape with RGB channels
    
    return cmap


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
