import cv2 as cv
import json
import numpy as np
import shapely

import matplotlib.cm as cm
from tqdm import tqdm
from shapely.ops import unary_union


def gaussian_kernel(l):
    sig = (l - 1) / 8.
    ax = np.linspace(-(l - 1) / 2., (l - 1) / 2., l)
    gauss = np.exp(-0.5 * np.square(ax) / np.square(sig))
    kernel = np.outer(gauss, gauss)
    return kernel / np.sum(kernel)


def gaussian_kernel_1d(l):
    sig = (l - 1) / 8.
    ax = np.linspace(-(l - 1) / 2., (l - 1) / 2., l)
    kernel = np.exp(-0.5 * np.square(ax) / np.square(sig))
    return kernel / np.sum(kernel)
    

def create_heatmap_img(heatmap, colormap=cm.get_cmap('plasma', 9)):
    heatmap = heatmap / heatmap.max()
    heatmap = np.clip(heatmap, 0, 1)

    heatmap_img = colormap(heatmap)
    heatmap_img[..., 3] = heatmap

    heatmap_img = (255 * heatmap_img).astype(np.uint8)
    return heatmap_img


def draw_rect(image, start_point, end_point, color, alpha=0.5):
    overlay = image.copy()
    overlay = cv.rectangle(overlay, start_point, end_point, color=color, thickness=-1, lineType=cv.LINE_AA)
    image_new = cv.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    image_new = cv.rectangle(image_new, start_point, end_point, color=color, thickness=2, lineType=cv.LINE_AA)
    return image_new


def get_aois(aoi_config_path):
    with open(aoi_config_path, 'r') as f:
        aois = json.load(f)
        shapes_geom = {}
        for shape in aois['shapes']:
            shapes_geom[shape['label']] = shapely.Polygon(shape['points'])

        return shapes_geom


# TODO This is rather slow since we iterate over all pixels in polygons bounding box
def get_masks(aois, width, height):
    masks = {}
    for label, shape in tqdm(aois.items()):
        minx, miny, maxx, maxy = shape.bounds
        masks[label] = np.zeros((height, width), dtype=float)

        for x in range(int(minx), int(maxx)):
            for y in range(int(miny), int(maxy)):
                masks[label][y, x] = aois[label].contains(shapely.Point(x, y))
    return masks


def get_merged_aois_masks(aois, width, height):
    mask = np.zeros((height, width), dtype=bool)
    merged_polygon = unary_union(list(aois.values()))
    convex_hull = merged_polygon.convex_hull

    minx, miny, maxx, maxy = convex_hull.bounds

    for x in range(int(minx), int(maxx)):
        for y in range(int(miny), int(maxy)):
            mask[y, x] = convex_hull.contains(shapely.Point(x, y))
    return mask.astype(float)

