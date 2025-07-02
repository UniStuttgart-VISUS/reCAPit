import pandas as pd
import numpy as np

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