import numpy as np
import cv2
import pandas as pd

from math import sqrt
from bisect import bisect_left
from sklearn.metrics.pairwise import cosine_similarity

def remove_time_offset(surface_fixations: pd.DataFrame, rec_offset: float) -> None:
    surface_fixations['start timestamp [sec]'] = surface_fixations['start timestamp [sec]'] - rec_offset
    surface_fixations['end timestamp [sec]'] = surface_fixations['end timestamp [sec]'] - rec_offset


def trim(surface_fixations: pd.DataFrame, duration_sec: float) -> pd.DataFrame:
    mask = (surface_fixations['start timestamp [sec]'] >= 0) & (surface_fixations['end timestamp [sec]'] <= duration_sec)
    return surface_fixations[mask]

def enlarge_bbox(bbox, scale_factor_horizontal:float=2.0, scale_factor_vertical:float=2.0):
    xmin, ymin, xmax, ymax = bbox

    w = xmax - xmin
    h = ymax - ymin

    cx = xmin + w*0.5
    cy = ymin + h*0.5

    wd = w * scale_factor_horizontal * 0.5
    hd = h * scale_factor_vertical * 0.5

    return int(cx - wd), int(cy - hd), int(cx + wd), int(cy + hd)

def draw_bbox_on_video(frame, bbox, label, looked_at):
    bbox_color = (0, 0, 255) if looked_at else (0, 255, 0)
    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), bbox_color, 2)

    cv2.putText(
        frame,
        label,
        (bbox[0], bbox[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (36, 255, 12),
        2,
    )


def draw_gaze_pointer(frame:np.ndarray, gaze_x:int, gaze_y:int, radius:float):
    cv2.circle(frame, (gaze_x, gaze_y), max(radius // 3, 1), (0, 255, 255), -1)
    cv2.circle(frame, (gaze_x, gaze_y), radius, (0, 0, 255), 3)


def intersect_face_bbox_gaze(
        bbox: list[int], gaze_x: int, gaze_y: int, gaze_radius: float
):
    distance = distance_face_bbox_gaze(bbox, gaze_x, gaze_y)
    # Check if the distance is less than or equal to the circle's radius
    return distance <= gaze_radius


def distance_face_bbox_gaze(
        bbox: list[int], gaze_x: int, gaze_y: int
):
    # Find the closest point on the rectangle to the circle's center
    closest_x = max(bbox[0], min(gaze_x, bbox[2]))
    closest_y = max(bbox[1], min(gaze_y, bbox[3]))

    # Calculate the distance from the circle's center to this closest point
    distance_x = gaze_x - closest_x
    distance_y = gaze_y - closest_y
    distance = sqrt(distance_x**2 + distance_y**2)
    return distance


def take_closest_timestamp(df, timestamp_value):
    """
    Assumes the DataFrame is sorted by 'timestamp [ns]'. Returns the row with the closest 'timestamp [ns]' to timestamp_value.

    If two timestamps are equally close, return the row with the smaller timestamp.
    """
    # Get the sorted 'timestamp [ns]' column as a numpy array
    timestamps = df["start timestamp [sec]"].values

    # Use bisect_left to find the position where timestamp_value would fit
    pos = bisect_left(timestamps, timestamp_value)

    # If the timestamp is smaller than the first element, return the first row
    if pos == 0:
        return df.iloc[0]

    # If the timestamp is greater than the last element, return the last row
    if pos == len(timestamps):
        return df.iloc[-1]

    return df.iloc[pos]


def calculate_similarity(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]


def calculate_gaze_coordinates(gaze_data, offset_ts):
    """
    Returns the gaze coordinates (x, y) for the given timestamp.
    """
    gaze_row = take_closest_timestamp(gaze_data, offset_ts)
    if gaze_row.empty:
        return None, None

    fix_id = int(gaze_row.iloc[0])
    gaze_x = int(gaze_row.iloc[4])
    gaze_y = int(gaze_row.iloc[5])
    return fix_id, gaze_x, gaze_y

def draw_tags(frame: np.ndarray, tags: list) -> None:
    for tag in tags:
        for i in range(4):
            pt1 = tuple(tag.corners[i].astype(int))
            pt2 = tuple(tag.corners[(i+1) % 4].astype(int))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        cx, cy = int(tag.center[0]), int(tag.center[1])

        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(frame, str(tag.tag_id), (cx - 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

def draw_gaze(frame: np.ndarray, pos_x: float, pos_y:float) -> None:
    cv2.circle(
        frame,
        (int(pos_x), int(pos_y)),
        radius=25,
        color=(0, 0, 255),
        thickness=-1,
    )

    cv2.circle(
        frame,
        (int(pos_x), int(pos_y)),
        radius=15,
        color=(0, 255, 255),
        thickness=-1,
    )

def draw_coord_label(frame: np.ndarray, label: str, x: float, y: float) -> None:
    cv2.putText(frame, f'{label} ({int(x)}, {int(y)})', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

def draw_progress_bar(frame: np.ndarray, progress: float) -> None:
    cv2.rectangle(frame, (10, 50), (210, 65), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, 50), (10 + int(200 * progress), 65), (0, 255, 0), -1)
    cv2.putText(frame, f'{int(progress * 100)}%', (220, 63), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
