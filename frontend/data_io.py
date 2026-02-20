from __future__ import annotations
from typing import Any
import base64

from ThumbnailModel import ThumbnailModel
from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt6.QtGui import QImage
from PyQt6.QtMultimedia import QVideoSink
from StackedSeries import StackedSeries
from ThumbnailProvider import ThumbnailProvider, qimage_to_base64
from pathlib import Path
from json.decoder import JSONDecodeError
from TimelineModel import SubjectMultimodalData
from AppConfig import AppConfig
from TimelineSegmentModel import TimelineSegmentModel
from TimelineSegment import TimelineSegment
from utils import extract_quotes
from dataclasses import asdict


import json
import logging
import numpy as np
import pandas as pd
import shapely
from TimelineSegmentModel import TimelineSegmentModel


def import_state(in_dir: str | Path) -> None:
    if isinstance(in_dir, str):
        in_dir = Path(in_dir)

    sub_dirs = list(in_dir.iterdir())

    if len(sub_dirs) == 0:
        return False

    marked = []
    titles = []
    quotes_note = []
    quotes_text = []
    thumbnail_info = []
    thumbnail_data = {}
    labels = []

    for card_dir in sub_dirs:
        if not card_dir.is_dir():
            continue

        idx = int(card_dir.name)
        with open(card_dir / 'card_data.json', encoding='utf-8') as f:
            data = json.load(f)
            try:
                marked[idx] = data['marked']
                titles[idx] = data['title']
                quotes_note[idx] = data['notes']
                quotes_text[idx] = data['dialogues']
                thumbnail_info[idx].thumbnail_data = data['thumbnails']
                labels[idx].extend([ti['label'] for ti in data['thumbnails']])

                for img_path in (card_dir / 'thumbnails').iterdir():
                    img = QImage(str(img_path))
                    thumbnail_data[img_path.stem] = {
                        'image': img,
                        'segment_idx': idx,
                        'type': 'unknown',
                    }
                    """
                    self.thumbnail_provider.thumbnails[img_path.stem] = {
                        'image': img,
                        'segment_idx': idx,
                        'type': 'unknown',
                    }
                    """
            except JSONDecodeError as e:
                logging.exception(e)
    return {
        'marked': marked,
        'titles': titles,
        'quotes_note': quotes_note,
        'quotes_text': quotes_text,
        'thumbnail_info': thumbnail_info,
        'thumbnail_data': thumbnail_data,
    }


def json_export(timeline_segments: TimelineSegmentModel,
                out_dir : str | Path,
                marked_only: bool) -> bool:  # noqa: FBT001

    if isinstance(out_dir, str):
        out_dir = Path(out_dir)

    for idx in range(timeline_segments.rowCount()):

        if not timeline_segments.has_card[idx]:
            continue

        if marked_only and not timeline_segments.marked[idx]:
            continue

        title = timeline_segments.titles[idx]
        text_notes = timeline_segments.quotes_note[idx]
        text_quotes = extract_quotes(timeline_segments.quotes_text[idx],
                                     timeline_segments.transcript_records[idx])
        thumbnail_info = []

        for info in timeline_segments.thumbnail_info[idx].thumbnail_data:
            img, _ = timeline_segments.thumbnail_provider.requestImage(
                info['img_id'] + '#0', QSize(),
            )
            thumbnail_info.append({
                'label': info['label'],
                'imgData': qimage_to_base64(img),
            })

        try:
            with open(out_dir / f'{idx:05d}.json', 'w', encoding='utf-8') as f:
                out_json = {
                    'title': title,
                    'time_range': {
                        'start_sec': timeline_segments.start_ts[idx],
                        'end_sec': timeline_segments.end_ts[idx],
                    },
                    'summary': timeline_segments.summaries[idx],
                    'notes': text_notes,
                    'quotes': asdict(text_quotes),
                    'thumbnails': thumbnail_info,
                }

                if not marked_only:
                    out_json['marked'] = timeline_segments.marked[idx]

                json.dump(out_json, f, ensure_ascii=False, indent=4)

        except (OSError, TypeError, ValueError, KeyError, IndexError) as e:
            return False
    return True


"""
kg_json = self.create_knowledge_graph()
with open(out_dir / 'kg.json', 'w', encoding='utf-8') as f:
    json.dump(kg_json, f, ensure_ascii=False, indent=2)
"""
"""
def create_knowledge_graph() -> dict[str, dict]:
    nodes = []
    edges = []

    for idx in range(len(self.start_ts)):
        if not (self.has_card[idx] and self.marked[idx]):
            continue

        segment_id = idx
        root_node_id = f'ROOT_{segment_id:02d}'
        note_node_id = f'NOTES_{segment_id:02d}'

        dists_stats = {}
        dists_stats['speaker'] = self.speaker_time_by_speaker(idx)
        for key in self.multi_time:
            dists_stats[key] = self.GetTimeSeries(key, idx).LabelDistribution()

        root_node = {
            'id': root_node_id,
            'data':
                {'title': self.titles[idx],
                    'text': self.summaries[idx],
                    'stats': {
                        'start_sec': self.PosStartSec(idx),
                        'end_sec': self.PosEndSec(idx),
                        #'distributions': dists_stats,
                    },
                },
            'type': 'segment',
        }
        nodes.append(root_node)

        if len(self.quotes_note[idx]) > 0:
            nodes.append({
                'id': note_node_id,
                'data': { 'text': self.quotes_note[idx] },
                'type': 'notes',
                'parentId': root_node_id,
            })

        for q in self.quotes_text[idx]['quotes']:
            quote_node_id = f'QUOTE_{segment_id:02d}_{q["label"]}'

            nodes.append({
                'id': quote_node_id,
                'data': q,
                'type': 'quote',
                'parentId': root_node_id,
            })

        thumbnail_info = self.thumbnail_info[idx].thumbnail_data

        for info in thumbnail_info:
            img, _ = self.thumbnail_provider.requestImage(
                info['img_id'] + '#0', QSize(),
            )
            thumbnail_node_id = f'THUMB_{segment_id:02d}_{info["label"]}'

            try:
                img_data = qimage_to_base64(img)

                nodes.append({
                    'id': thumbnail_node_id,
                    'data': {
                        'imgData': img_data,
                        'label': info['label'],
                        'description': '',
                        'aoi_scores': info['aoi_scores'],
                    },
                    'type': 'thumbnail',
                    'parentId': root_node_id,
                })
            except (OSError, ValueError) as e:
                logging.error(e)

    return {
        'nodes': nodes,
        'edges': edges,
        'meta': {
            'speakers': self.meta_model.Identifiers(),
            'aois': self.meta_model.Labels(),
        },
    }
"""
