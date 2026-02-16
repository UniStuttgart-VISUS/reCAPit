import numpy as np
import logging
import cvxpy as cp
import pandas as pd

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage
from PyQt6.QtMultimedia import QVideoSink

import logging
import pandas as pd
import shapely

from TranscriptRecord import TranscriptRecord
from TimelineSegment import QuotesText
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter


def linear_layout(target_loc, elem_width, min_xpos, max_xpos):
    target_loc = np.array(target_loc)
    count = len(target_loc)
    d = target_loc

    # Decision variable
    x = cp.Variable(count)

    # Objective: minimize ||x - target_loc||^2
    objective = cp.Minimize(cp.sum_squares(x - d))

    # Inequality constraints: x[i+1] - x[i] >= elem_width
    constraints = [x[i + 1] - x[i] >= elem_width for i in range(count - 1)]

    # Bounds
    constraints += [x >= min_xpos, x <= max_xpos]

    # Problem definition and solving
    prob = cp.Problem(objective, constraints)
    prob.solve()

    if x.value is None:
        logging.error('No valid layout found. Quadratic program has no solution.')
        return np.zeros_like(target_loc)

    return x.value


def longest_common_substring(s1, s2):
    # Get lengths of both strings
    m, n = len(s1), len(s2)

    # Create a 2D table to store lengths of longest common suffixes
    # Initialize all values to 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Length of the longest common substring
    length = 0

    # Variable to store the end point of the longest common substring in s1
    end_point_1 = 0
    end_point_2 = 0

    # Build the table in bottom-up fashion
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > length:
                    length = dp[i][j]
                    end_point_1 = i
                    end_point_2 = j
            else:
                dp[i][j] = 0

    return {'a': end_point_1 - length, 'b': end_point_2 - length, 'size': length}


def blend_images(image1, image2, opacity=0.5):
    """
    Blends two QImage objects together.

    :param image1: The base QImage.
    :param image2: The QImage to blend on top of the base image.
    :param opacity: The opacity of the second image (0.0 to 1.0).
    :return: A new QImage with the blended result.
    """
    # Ensure both images are the same size
    if image1.size() != image2.size():
        raise ValueError('Images need to be same size!')

    # Create a new QImage to store the result
    result = QImage(image1.size(), QImage.Format.Format_ARGB32)
    #result.fill(QColor("transparent"))
    result.fill(Qt.GlobalColor.transparent)

    # Create a QPainter to blend the images
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

    # Draw the first image
    painter.drawImage(0, 0, image1)

    # Set the opacity for the second image
    painter.setOpacity(opacity)

    # Draw the second image on top of the first
    painter.drawImage(0, 0, image2)

    # Finish painting
    painter.end()

    return result


def merge_transcript(df, time_delta_threshold=1.0):
    merged_rows = []
    for _, row in df.iterrows():
        if len(merged_rows) > 1:
            time_delta = (
                row["start timestamp [sec]"] - merged_rows[-1]["end timestamp [sec]"]
            )
            speaker_match = row["speaker"] == merged_rows[-1]["speaker"]

            if time_delta < time_delta_threshold and speaker_match:
                merged_rows[-1]["end timestamp [sec]"] = row["end timestamp [sec]"]
                merged_rows[-1]["text"] = merged_rows[-1]["text"] + " " + row["text"]
            else:
                merged_rows.append(row)
        else:
            merged_rows.append(row)
    return pd.DataFrame(merged_rows)


def filter_segments(topics, min_dur_1, min_dur_2):
    topics['Displayed'] = True
    topics = topics[topics['duration [sec]'] > min_dur_1]
    topics.loc[topics['duration [sec]'] < min_dur_2, 'Displayed'] = False
    return topics


def fill_gaps(topics, threshold_sec=15):
    merged = []
    for _, row in topics.iterrows():
        if len(merged) > 0 and row['start timestamp [sec]'] - threshold_sec > merged[-1]['start timestamp [sec]']:
            merged[-1]['end timestamp [sec]'] = row['start timestamp [sec]']
        merged.append(row)

    return pd.DataFrame.from_records(merged)



def fill_between(topics, max_ts):
    last_ts = 0
    new_rows = []
    for _, row in topics.iterrows():
        if row['start timestamp [sec]'] - last_ts > 0:
            new_rows.append((last_ts, row['start timestamp [sec]'], row['start timestamp [sec]'] - last_ts, 0, 0, "", "", False))
        last_ts = row['end timestamp [sec]']

    if last_ts < max_ts:
        new_rows.append((last_ts, max_ts, max_ts - last_ts, 0, 0, "", "", False))

    new_rows = pd.DataFrame(data=new_rows, columns=['start timestamp [sec]', 'end timestamp [sec]', 'duration [sec]', 'speech overlap [sec]', 'turn count', 'title', 'summary', 'Displayed'])
    return pd.concat([new_rows, topics]).sort_values(by='start timestamp [sec]')


def speaker_time_by_role(records: list[TranscriptRecord], roles: list[str], total_dur: float) -> dict[str, float]:
    role_durations = dict.fromkeys(roles, 0)

    for row in records:
        dur = row.end_ts - row.start_ts
        role = row.role
        if role not in roles:
            continue

        role_durations[role] += dur
    return {role: float(role_durations[role]) / total_dur for role in roles}

def speaker_time_by_speaker(records: list[TranscriptRecord], speakers: list[str], total_dur: float) -> dict[str, float]:
    speaker_durations = dict.fromkeys(speakers, 0)

    for row in records:
        dur = row.end_ts - row.start_ts
        if row.speaker not in speakers:
            continue
        speaker_durations[row.speaker] += dur

    return {speaker: float(speaker_durations[speaker]) / total_dur for speaker in speakers}


def extract_quotes(text: str, records: list[TranscriptRecord]) -> QuotesText:
    text_units = text.split('\n\n')
    text_units = [t.replace('\n', ' ').strip() for t in text_units if len(t) > 0]
    formatted = []
    speaker_quotes = []

    for tu in text_units:
        results = []

        for rec in records:
            line_text = rec.text.replace('\n', ' ').strip()
            match = longest_common_substring(tu, line_text)

            src = rec.speaker
            cnt = sum(other_src == src for other_src, _, _ in results)
            results.append((src, cnt, match))

        max_idx = np.argmax([res['size'] for _, _, res in results])
        src, idx, res = results[max_idx]

        if (res['size'] / len(tu)) > 0.5:
            quote_label = f'{src.upper()[:2]}{idx + 1}'

            formatted.append(
                f'{tu[0 : res["a"]]} <font color="grey"><b>{quote_label}</b></font> <font color="black"><u>{tu[res["a"] : res["a"] + res["size"]]}</u></font>{tu[res["a"] + res["size"] :]}'
            )
            speaker_quotes.append(
                {'speaker': src, 'label': quote_label ,'text': tu[res['a'] : res['a'] + res['size']]},
            )
        else:
            formatted.append(tu)

    formatted = '<br><br>'.join(formatted)
    return QuotesText(original=text,
                      formatted=formatted,
                      quotes=speaker_quotes)


"""
@pyqtSlot(QVideoSink, float, int, float, float, float, float, str)
def register_video_crop(
    self,
    video_sink: QVideoSink,
    pos_ms: float,
    segment_idx: int,
    norm_x: float,
    norm_y: float,
    norm_width: float,
    norm_height: float,
    overlay_src: str,
) -> None:
    img = video_sink.videoFrame().toImage()
    size = img.size()

    x = int(norm_x * size.width())
    y = int(norm_y * size.height())

    width = int(norm_width * size.width())
    height = int(norm_height * size.height())

    selection_shape = shapely.box(norm_x, norm_y, norm_x + norm_width, norm_y + norm_height)
    aoi_scores = {}

    for label, aoi_data in self.meta_model.shapes.items():
        aoi_shape = shapely.Polygon(aoi_data['points'])
        inter_shape = shapely.intersection(aoi_shape, selection_shape)
        aoi_scores[label] = shapely.area(inter_shape) / shapely.area(aoi_shape)

    crop = img.copy(x, y, width, height)

    if overlay_src in self.heatmap_overlay_providers:
        target_provider = self.heatmap_overlay_providers[overlay_src]
        overlay = target_provider.compute_overlay(
            self.start_ts[segment_idx], self.end_ts[segment_idx],
        )
        overlay_img, _ = target_provider.requestImage(
            target_provider.img_id(segment_idx), QSize(),
        )
        crop_overlay_gaze_img = overlay_img.copy(x, y, width, height)

        score = overlay[y : y + height, x : x + width].sum() / overlay.sum()
        crop = blend_images(crop, crop_overlay_gaze_img)

    else:
        score = 0.0

    img_id, label = self.thumbnail_provider.add_to_collection(
        segment_idx, crop, overlay_src,
    )

    self.timeline_segments.add_label(label)
    self.timeline_segments.add_thumbnail(img_id, aoi_scores, pos_ms*1e-3, label)
"""