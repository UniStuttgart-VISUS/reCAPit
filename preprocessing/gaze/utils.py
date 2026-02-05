import pandas as pd
import numpy as np
import cv2

def world_timestamps(rec_dir):
    world_ts = pd.read_csv(rec_dir / 'world.csv')
    world_ts["world_frame_index"] = np.arange(len(world_ts))
    world_ts = world_ts[["world_frame_index", "timestamp [ns]"]]
    return world_ts


def load_fixations(rec_dir):
    # Timestamps of video frames
    world_ts = world_timestamps(rec_dir)

    # Read fixations (no frames column)
    df = pd.read_csv(rec_dir / 'fixations.csv')

    # Assign start frame number to fixations
    df = pd.merge_asof(df, world_ts, left_on="start timestamp [ns]", right_on="timestamp [ns]", direction="nearest")
    df['start frame'] = df['world_frame_index']
    df = df.drop(['world_frame_index'], axis=1)

    # Assign end frame number to fixations
    df = pd.merge_asof(df, world_ts, left_on="end timestamp [ns]", right_on="timestamp [ns]", direction="nearest")
    df['end frame'] = df['world_frame_index']
    df = df.drop(['world_frame_index'], axis=1)

    # Compute center frame
    df['center frame'] = df['start frame'] + (df['end frame'] - df['start frame']) // 2

    return df


def load_gaze(rec_dir):
    # Timestamps of video frames
    world_ts = world_timestamps(rec_dir)

    # Read fixations (no frames column)
    df = pd.read_csv(rec_dir / 'gaze.csv')

    # Assign start frame number to fixations
    df = pd.merge_asof(df, world_ts, left_on="timestamp [ns]", right_on="timestamp [ns]", direction="nearest")

    df['frame'] = df['world_frame_index']
    df = df.drop(['world_frame_index'], axis=1)

    return df

def draw_tags(frame, tags):
    for tag in tags:
        for i in range(4):
            pt1 = tuple(tag.corners[i].astype(int))
            pt2 = tuple(tag.corners[(i+1) % 4].astype(int))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        cX, cY = int(tag.center[0]), int(tag.center[1])

        cv2.circle(frame, (cX, cY), 5, (0, 0, 255), -1)
        cv2.putText(frame, str(tag.tag_id), (cX - 10, cY - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

def draw_gaze(frame: np.ndarray, pos_x: float, pos_y:float) -> None:
    cv2.circle(
        frame,
        (int(pos_x), int(pos_y)),
        radius=30,
        color=(0, 0, 255),
        thickness=15,
    )