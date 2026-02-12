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
from TopicCard import TopicCardData
from pathlib import Path
from json.decoder import JSONDecodeError
from TimelineModel import SubjectMultimodalData
from AppConfig import AppConfig
from TimelineSegmentModel import TimelineSegmentModel


from utils import (
    blend_images,
    fill_between,
    fill_gaps,
    filter_segments,
    merge_transcript,
)

import json
import logging
import numpy as np
import pandas as pd
import shapely


class SegmentModel(QObject):
    timelineSegmentModelChanged = pyqtSignal()

    def __init__(
        self, segments: pd.DataFrame, multimodal_recordings: dict[str, SubjectMultimodalData], 
        meta_model: AppConfig, video_src: dict[str, dict], parent: object = None,
    ) -> None:
        super().__init__(parent)
        self.meta_model = meta_model
        self.meta_model.setParent(self)

        self.original_segments = segments.copy()
        self.original_segments['Displayed'] = True

        self.active_labels = self.meta_model.Labels()
        self.multimodal_recordings = multimodal_recordings
        self.multi_time = {}
        self.transcript = pd.DataFrame()
        self.thumbnail_provider = ThumbnailProvider()

        self.video_src = video_src
        self.has_attention = False
        self.has_gaze_heatmaps = False
        self.has_move_heatmaps = False
        self.heatmap_overlay_providers = {}
        self.timeline_segments = None

        for multimodal_data in multimodal_recordings.values():
            multimodal_data.setParent(self)

        self.init_segments(self.original_segments)
        self.set_notes(NotesModel.empty())

    def init_segments(self, segments: pd.DataFrame) -> None:
        self.segments = fill_between(fill_gaps(segments, threshold_sec=5), max_ts=self.MaxTimestamp())
        num_segments = len(self.segments.index)

        self.start_ts = self.segments['start timestamp [sec]'].tolist()
        self.end_ts = self.segments['end timestamp [sec]'].tolist()
        self.titles = self.segments['title'].tolist()
        self.summaries = self.segments['summary'].tolist()
        self.has_card = self.segments['Displayed'].tolist()

        self.quotes_text = [{'original': '', 'formatted': '', 'quotes': []}] * num_segments
        self.quotes_note = [''] * num_segments
        self.thumbnail_info = [ThumbnailModel(self) for _ in range(num_segments)]
        self.marked = [False] * num_segments
        self.labels = [[] for _ in range(num_segments)]
        self.card_sizes = [385] * num_segments

        for provider in self.heatmap_overlay_providers.values():
            provider.segments_start = self.start_ts
            provider.segments_end = self.end_ts

    def set_transcript(self, transcript: pd.DataFrame) -> None:
        self.transcript = merge_transcript(transcript)
        self.transcript = self.transcript[self.transcript['speaker'].notna()]
        self.transcript['role'] = self.transcript['speaker'].map(
            lambda s: self.meta_model.speaker_role(s.replace(' ', '')),
        )
        self.transcript['duration [sec]'] = (
            self.transcript['end timestamp [sec]']
            - self.transcript['start timestamp [sec]']
        )

    def done(self):
        self.timeline_segments = TimelineSegmentModel(titles=self.titles,
                                                      has_card=self.has_card,
                                                      start_ts=self.start_ts,
                                                      end_ts=self.end_ts,
                                                      transcript=self.transcript,
                                                      stacked_data=self.multi_time,
                                                      subject_data=self.multimodal_recordings,
                                                      notes_data=self.notes_model,
                                                      roles=self.meta_model.Roles(),
                                                      quotes_text=self.quotes_text,
                                                      quotes_note=self.quotes_note,
                                                      thumbnail_info=self.thumbnail_info,
                                                      marked=self.marked,
                                                      summaries=self.summaries,
                                                      labels=self.labels,
                                                      parent=self)
        self.timelineSegmentModelChanged.emit()


    def set_notes(self, notes: NotesModel) -> None:
        self.notes_model = notes
        self.notes_model.setParent(self)
        self.has_notes = True

    def register_multi_time(self, name: str, ts: StackedSeries) -> None:
        self.multi_time[name] = ts

    def add_video_overlay_provider(
        self, name: str, heatmap_provider: HeatmapOverlayProvider,
    ) -> None:
        self.heatmap_overlay_providers[name] = heatmap_provider
        self.heatmap_overlay_providers[name].segments_start = self.start_ts
        self.heatmap_overlay_providers[name].segments_end = self.end_ts
        return f'heatmaps_{name}'

    @pyqtProperty(TimelineSegmentModel, notify=timelineSegmentModelChanged)
    def timeline_segment_model(self) -> TimelineSegmentModel:
        return self.timeline_segments

    @pyqtSlot(str, str)
    def UpdateOverlayColormap(self, name: str, cmap_str: str) -> None:
        self.heatmap_overlay_providers[name].set_colormap(cmap_str)

    @pyqtSlot(str, result=bool)
    def import_state(self, in_dir: str | Path) -> None:
        if isinstance(in_dir, str):
            in_dir = Path(in_dir)

        sub_dirs = list(in_dir.iterdir())

        if len(sub_dirs) == 0:
            return False

        for card_dir in sub_dirs:
            if not card_dir.is_dir():
                continue

            idx = int(card_dir.name)
            with open(card_dir / 'card_data.json', encoding='utf-8') as f:
                data = json.load(f)
                try:
                    self.marked[idx] = data['marked']
                    self.titles[idx] = data['title']
                    self.quotes_note[idx] = data['notes']
                    self.quotes_text[idx] = data['dialogues']
                    self.thumbnail_info[idx].thumbnail_data = data['thumbnails']

                    self.labels[idx].extend([ti['label'] for ti in data['thumbnails']])

                    for img_path in (card_dir / 'thumbnails').iterdir():
                        img = QImage(str(img_path))
                        self.thumbnail_provider.thumbnails[img_path.stem] = {
                            'image': img,
                            'segment_idx': idx,
                            'type': 'unknown',
                        }
                except JSONDecodeError as e:
                    logging.error(e)
                    return False
        return True

    @pyqtSlot(str, result=bool)
    def export_bookmarked(self, out_dir : str | Path) -> bool:
        if isinstance(out_dir, str):
            out_dir = Path(out_dir)

        for idx in range(len(self.start_ts)):
            if not self.has_card[idx] or not self.marked[idx]:
                continue

            title = self.titles[idx]
            text_notes = self.quotes_note[idx]
            text_dialogues = self.quotes_text[idx]
            thumbnail_info = []

            for info in self.thumbnail_info[idx].thumbnail_data:
                img, _ = self.thumbnail_provider.requestImage(
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
                            'start_sec': self.PosStartSec(idx),
                            'end_sec': self.PosEndSec(idx),
                        },
                        'summary': self.summaries[idx],
                        'notes': text_notes,
                        'quotes': text_dialogues['quotes'],
                        'thumbnails': thumbnail_info,
                    }
                    json.dump(out_json, f, ensure_ascii=False, indent=4)

            except (OSError, TypeError, ValueError, KeyError, IndexError) as e:
                logging.error(e)
                return False
        return True

    @pyqtSlot(str, result=bool)
    def export_state(self, out_dir : str | Path) -> bool:
        if isinstance(out_dir, str):
            out_dir = Path(out_dir)

        kg_json = self.create_knowledge_graph()
        with open(out_dir / 'kg.json', 'w', encoding='utf-8') as f:
            json.dump(kg_json, f, ensure_ascii=False, indent=2)

        for idx in range(len(self.start_ts)):
            marked = self.marked[idx]
            title = self.titles[idx]
            text_notes = self.quotes_note[idx]
            text_dialogues = self.quotes_text[idx]
            thumbnail_info = self.thumbnail_info[idx].thumbnail_data

            if not self.has_card[idx]:
                continue

            sub_dir = out_dir / f'{idx:05d}'
            sub_dir.mkdir(parents=True, exist_ok=True)

            try:
                with open(sub_dir / 'card_data.json', 'w', encoding='utf-8') as f:
                    marked = self.marked[idx]
                    title = self.titles[idx]
                    text_notes = self.quotes_note[idx]
                    text_dialogues = self.quotes_text[idx]
                    thumbnail_info = self.thumbnail_info[idx].thumbnail_data

                    out_json = {
                        'marked': marked,
                        'title': title,
                        'notes': text_notes,
                        'dialogues': text_dialogues,
                        'thumbnails': thumbnail_info,
                    }

                    json.dump(out_json, f, ensure_ascii=False, indent=4)

                    thumbnail_dir = sub_dir / 'thumbnails'
                    thumbnail_dir.mkdir(parents=True, exist_ok=True)

                    for info in thumbnail_info:
                        img, _ = self.thumbnail_provider.requestImage(
                            info['img_id'] + '#0', QSize(),
                        )
                        success = img.save(str(thumbnail_dir / f"{info['img_id']}.png"))

                        if not success:
                            msg = f"Failed to save {info['img_id']}"
                            raise ValueError(msg)
            except (OSError, TypeError, ValueError, KeyError, IndexError) as e:
                logging.error(e)
                return False
        return True

    def create_knowledge_graph(self) -> dict[str, dict]:
        nodes = []
        edges = []
        prev_root_node = None

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
                            'distributions': dists_stats,
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
                    """
                    edges.append({
                        'id': f'e{root_node_id}-{thumbnail_node_id}',
                        'data': {'label': 'within'},
                        'source': root_node_id,
                        'target': thumbnail_node_id,
                    })
                    """
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



    @pyqtSlot(int, result='QVariantMap')
    def VideoOverlaySources(self, segment_idx: int) -> dict[str, str]:
        return {
            name: f'image://heatmaps_{name}/' + provider.img_id(segment_idx)
            for name, provider in self.heatmap_overlay_providers.items()
        }

    @pyqtSlot(str, int, result=list)
    def FindSimilarSegments(self, text: str, snippet_idx: int) -> list:
        self.service.exec_query(text, top_k=30, meta={'snippet_index': snippet_idx})
        return []


    @pyqtSlot(int, int)
    def deregister_video_crop(self, segment_idx: int, crop_idx: int) -> None:
        del self.labels[segment_idx][crop_idx]
        self.thumbnail_info[segment_idx].removeRow(crop_idx)


    @pyqtSlot(QVideoSink, float, int, float, float, float, float, str)
    def RegisterVideoCrop(
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

        self.labels[segment_idx].append(label)
        self.thumbnail_info[segment_idx].append(img_id, aoi_scores, pos_ms*1e-3, label)


    @pyqtSlot(float, float)
    def AdjustFilter(self, min_dur_sec: float, display_dur_sec: float) -> None:
        segments = self.original_segments.copy()
        segments = filter_segments(segments, min_dur_sec, display_dur_sec)
        self.init_segments(segments)

    @pyqtSlot(result=str)
    def VideoSourceTopDown(self):
        return 'file:///' + self.video_src['workspace']['path']

    @pyqtSlot(result=list)
    def VideoSourcesPeripheral(self):
        return ['file:///' + str(self.video_src['side']['path'])]

    @pyqtSlot(result=int)
    def SpeechLineCount(self):
        return len(self.multimodal_recordings.keys())

    def speaker_time_by_speaker(self, idx: int) -> dict[str, float]:
        start_ts = self.start_ts[idx]
        end_ts = self.end_ts[idx]

        total_dur = end_ts - start_ts

        part = self.transcript[
            (self.transcript['start timestamp [sec]'] >= start_ts)
            & (self.transcript['end timestamp [sec]'] <= end_ts)
        ]
        speaker_durations = part.groupby('speaker')['duration [sec]'].sum()
        return {speakers: float(speaker_durations.get(speakers, 0)) / total_dur for speakers in self.meta_model.Identifiers()}

    @pyqtSlot(int, result=bool)
    def IsMarked(self, index: int):
        return self.marked[index]

    @pyqtSlot(result=list)
    def MarkedIndices(self):
        return [idx for idx in range(len(self.marked)) if self.marked[idx]]

    @pyqtSlot(result=list)
    def IndicesOfCards(self):
        return [idx for idx in range(len(self.has_card)) if self.has_card[idx]]

    @pyqtSlot(list, result=list)
    def KeywordMatches(self, keywords):
        matched_indices = []

        for segment_idx in range(len(self.start_ts)):
            pairs = self.GetUtteranceSpeakerPairs(segment_idx)
            segment_txt = '.'.join([p['text'].lower() for p in pairs])

            for kw in keywords:
                kw = kw.lower()
                if kw in segment_txt:
                    matched_indices.append(segment_idx)
                    break
        return matched_indices

    @pyqtSlot(result=float)
    def MinTimestamp(self):
        k = list(self.multimodal_recordings.keys())
        return self.multimodal_recordings[k[0]].MinTimestamp()

    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        k = list(self.multimodal_recordings.keys())
        return self.multimodal_recordings[k[0]].MaxTimestamp()

    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.start_ts)
