import pandas as pd
import numpy as np
import cv2

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
