import cv2 as cv
import numpy as np
import matplotlib.cm as cm


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

