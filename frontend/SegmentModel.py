from __future__ import annotations
from typing import Any
import base64

from ThumbnailModel import ThumbnailModel
from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
from PyQt6.QtMultimedia import QVideoSink
from StackedSeries import StackedSeries
from ThumbnailProvider import ThumbnailProvider, qimage_to_base64
from TopicCard import TopicCardData
from pathlib import Path
from json.decoder import JSONDecodeError
from TimelineModel import SubjectMultimodalData
from AppConfig import AppConfig


from utils import (
    blend_images,
    fill_between,
    filter_segments,
    linear_layout,
    longest_common_substring,
    merge_transcript,
)

import json
import logging
import numpy as np
import pandas as pd
import shapely


class SegmentModel(QObject):
    queryResultsAvailable = pyqtSignal(int, list, list)

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
        self.has_activity = False
        self.has_gaze_heatmaps = False
        self.has_move_heatmaps = False
        self.heatmap_overlay_providers = {}

        for multimodal_data in multimodal_recordings.values():
            multimodal_data.setParent(self)

        self.init_segments(self.original_segments)

        self.set_notes(NotesModel.empty())
        self.set_attention(
            StackedSeries.empty(
                self.start_ts[0], self.end_ts[-1], self.meta_model.Labels(),
            ),
        )
        self.set_activity(
            StackedSeries.empty(
                self.start_ts[0], self.end_ts[-1], self.meta_model.Labels(),
            ),
        )

    def init_segments(self, segments: pd.DataFrame) -> None:
        self.segments = fill_between(segments, max_ts=self.MaxTimestamp())
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

    def set_notes(self, notes: NotesModel) -> None:
        self.notes_model = notes
        self.notes_model.setParent(self)
        self.has_notes = True

    def set_activity(self, activity: StackedSeries) -> None:
        self.activity = activity
        self.activity.setParent(self)
        self.has_activity = True

    def register_multi_time(self, name: str, ts: StackedSeries) -> None:
        ts.setParent(self)
        self.multi_time[name] = ts

    def set_attention(self, attention: StackedSeries) -> None:
        self.attention = attention
        self.attention.setParent(self)
        self.has_attention = True

    def add_video_overlay_provider(
        self, name: str, heatmap_provider: HeatmapOverlayProvider,
    ) -> None:
        self.heatmap_overlay_providers[name] = heatmap_provider
        self.heatmap_overlay_providers[name].segments_start = self.start_ts
        self.heatmap_overlay_providers[name].segments_end = self.end_ts
        return f'heatmaps_{name}'

    @pyqtSlot(str, str)
    def UpdateOverlayColormap(self, name: str, cmap_str: str) -> None:
        self.heatmap_overlay_providers[name].set_colormap(cmap_str)

    """
    @pyqtSlot(int, result=list)
    def FindSimilarSegments(self, segment_idx):
        self.service.exec_query(self.titles[segment_idx], top_k=5, meta={'target_index': segment_idx})
        return list()
    """

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
    def export_state(self, out_dir : str | Path) -> bool:
        if isinstance(out_dir, str):
            out_dir = Path(out_dir)

        kg_json = self.create_knowledge_graph()
        with open(out_dir / 'kg.json', 'w', encoding='utf-8') as f:
            json.dump(kg_json, f, ensure_ascii=False, indent=2)

        for idx in range(len(self.start_ts)):
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
            except Exception as e:
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

            root_node = {
                'id': root_node_id,
                'data':
                    {'title': self.titles[idx],
                      'text': self.summaries[idx],
                      'stats': {
                            'start_sec': self.PosStartSec(idx),
                            'end_sec': self.PosEndSec(idx),
                            'speaker_percentage': self.speaker_time_by_speaker(idx),
                            'movement_percentage': self.GetTimeSeries(
                                'attention', idx,
                            ).LabelDistribution(),
                            'attention_percentage': self.GetTimeSeries(
                                'movement', idx,
                            ).LabelDistribution(),
                        },
                    },
                'type': 'segment',
            }
            nodes.append(root_node)

            if prev_root_node is not None:
                edges.append({
                    'id': f'e{prev_root_node["id"]}-{root_node_id}',
                    'data': {'label': 'before'},
                    'source': prev_root_node['id'],
                    'target': root_node_id,
                })

            prev_root_node = root_node

            if len(self.quotes_note[idx]) > 0:
                nodes.append({
                    'id': note_node_id,
                    'data': { 'text': self.quotes_note[idx] },
                    'type': 'notes',
                    'parentId': root_node_id,
                })

                edges.append({
                    'id': f'e{root_node_id}-{note_node_id}',
                    'data': {'label': 'within'},
                    'source': root_node_id,
                    'target': note_node_id,
                })

            for q in self.quotes_text[idx]['quotes']:
                quote_node_id = f'QUOTE_{segment_id:02d}_{q["label"]}'

                nodes.append({
                    'id': quote_node_id,
                    'data': q,
                    'type': 'quote',
                    'parentId': root_node_id,
                })

                edges.append({
                    'id': f'e{root_node_id}-{quote_node_id}',
                    'data': {'label': 'within'},
                    'source': root_node_id,
                    'target': quote_node_id,
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
                            'aoi_scores': info['aoi_scores'],
                        },
                        'type': 'thumbnail',
                        'parentId': root_node_id,
                    })

                    edges.append({
                        'id': f'e{root_node_id}-{thumbnail_node_id}',
                        'data': {'label': 'within'},
                        'source': root_node_id,
                        'target': thumbnail_node_id,
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


    def process_query_results(self, res: dict[str, Any]) -> None:
        self.queryResultsAvailable.emit(
            res['meta']['snippet_index'],
            res['result']['scores'],
            res['result']['indices'],
        )

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


    @pyqtSlot(int, result=list)
    def ThumbnailInfo(self, segment_idx: int) -> list:
        return []
        #return self.thumbnail_info[segment_idx]

    @pyqtSlot(int, result=list)
    def ThumbnailIndicatorPositions(self, segment_idx: int) -> list[float]:
        return [
            (info['pos_sec'] - self.GetPosStart(segment_idx))
            / (self.GetPosEnd(segment_idx) - self.GetPosStart(segment_idx))
            for info in self.thumbnail_info[segment_idx]
        ]

    @pyqtSlot(int, result=list)
    def ThumbnailIndicatorLabels(self, segment_idx: int) -> list[str]:
        return [info['label'] for info in self.thumbnail_info[segment_idx]]

    @pyqtSlot(int, result=list)
    def VideoCropLabels(self, segment_idx: int) -> list[str]:
        return [info['label'] for info in self.thumbnail_info[segment_idx]]

    def delete_segment(self, target_idx: int) -> None:
        del self.start_ts[target_idx]
        del self.end_ts[target_idx]
        del self.titles[target_idx]
        del self.has_card[target_idx]
        del self.labels[target_idx]

    @pyqtSlot(int)
    def MergeWithLeft(self, target_idx):
        neighbor_idx = target_idx - 1

        if not (0 <= neighbor_idx < len(self.start_ts)):
            return

        self.end_ts[neighbor_idx] = self.end_ts[target_idx]
        self.titles[neighbor_idx] = self.titles[target_idx]
        self.has_card[neighbor_idx] = self.has_card[target_idx]
        self.labels[neighbor_idx] = self.labels[neighbor_idx] + self.labels[target_idx]

        self.delete_segment(target_idx)
        # TODO Merge heatmaps

    @pyqtSlot(int)
    def MergeWithRight(self, target_idx):
        neighbor_idx = target_idx + 1

        if not (0 <= neighbor_idx < len(self.start_ts)):
            return

        self.start_ts[neighbor_idx] = self.start_ts[target_idx]
        self.titles[neighbor_idx] = self.titles[target_idx]
        self.has_card[neighbor_idx] = self.has_card[target_idx]
        self.labels[neighbor_idx] = self.labels[neighbor_idx] + self.labels[target_idx]

        self.delete_segment(target_idx)

        # TODO Merge heatmaps

    @pyqtSlot(result=str)
    def VideoSourceTopDown(self):
        return 'file:///' + self.video_src['workspace']['path']

    @pyqtSlot(result=list)
    def VideoSourcesPeripheral(self):
        return ['file:///' + str(self.video_src['room']['path'])]

    @pyqtSlot(result=int)
    def SpeechLineCount(self):
        return len(self.multimodal_recordings.keys())

    @pyqtSlot(result=bool)
    def HasAttention(self):
        return 'bottom' in self.multi_time

    @pyqtSlot(result=bool)
    def HasActivity(self):
        return 'top' in self.multi_time

    @pyqtSlot(result=bool)
    def HasGazeHeatmap(self):
        return self.has_gaze_heatmaps

    @pyqtSlot(result=bool)
    def HasMoveHeatmap(self):
        return self.has_move_heatmaps

    @pyqtSlot(str)
    def ToggleLabel(self, label: str):
        if label in self.active_labels:
            self.active_labels.remove(label)
        else:
            self.active_labels.append(label)

    @pyqtSlot(int, result=list)
    def GetUtteranceSpeakerPairs(self, index: int):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]

        part = self.transcript[
            (self.transcript['start timestamp [sec]'] >= start_ts)
            & (self.transcript['end timestamp [sec]'] <= end_ts)
        ]

        utterances = part['text'].tolist()
        speakers = part['speaker'].tolist()
        start_times = part['start timestamp [sec]'].tolist()
        end_times = part['end timestamp [sec]'].tolist()

        return [{'text': u, 'speaker': s, 'start_time': st, 'end_time': et} for s, u, st, et in zip(speakers, utterances, start_times, end_times)]

    def speaker_time_by_role(self, idx: int) -> dict[str, float]:
        start_ts = self.start_ts[idx]
        end_ts = self.end_ts[idx]

        roles = self.meta_model.Roles()
        total_dur = end_ts - start_ts

        part = self.transcript[
            (self.transcript['start timestamp [sec]'] >= start_ts)
            & (self.transcript['end timestamp [sec]'] <= end_ts)
        ]
        role_durations = part.groupby('role')['duration [sec]'].sum()
        return {role: float(role_durations.get(role, 0)) / total_dur for role in roles}

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

    @pyqtSlot(int, result=str)
    def Title(self, index: int):
        return self.titles[index]

    @pyqtSlot(int, result=list)
    def Labels(self, index: int):
        return self.labels[index]

    @pyqtSlot(int, result=str)
    def Summary(self, index: int):
        return self.summaries[index]

    @pyqtSlot(int, result=str)
    def TextDialoguesOriginal(self, index: int):
        return self.quotes_text[index]['original']

    @pyqtSlot(int, result=str)
    def TextDialoguesFormatted(self, index: int):
        return self.quotes_text[index]['formatted']

    @pyqtSlot(int, result=str)
    def TextNotes(self, index: int):
        return self.quotes_note[index]

    @pyqtSlot(int, result=ThumbnailModel)
    def ThumbnailCrops(self, index: int):
        return self.thumbnail_info[index]

    @pyqtSlot(int, result=float)
    def PosEndSec(self, index: int):
        return self.end_ts[index]

    @pyqtSlot(int, result=float)
    def PosStartSec(self, index: int):
        return self.start_ts[index]

    @pyqtSlot(int, result=bool)
    def IsMarked(self, index: int):
        return self.marked[index]

    @pyqtSlot(result=list)
    def MarkedIndices(self):
        return [idx for idx in range(len(self.marked)) if self.marked[idx]]

    @pyqtSlot(result=list)
    def AllIndices(self):
        return range(len(self.marked))

    @pyqtSlot(result=list)
    def IndicesOfCards(self):
        return [idx for idx in range(len(self.has_card)) if self.has_card[idx]]

    @pyqtSlot(result=list)
    def Indices(self):
        return range(len(self.marked))

    @pyqtSlot(int, result=TopicCardData)
    def GetTopicCardData(self, index):
        start_ts = self.start_ts
        end_ts = self.end_ts

        tcd = TopicCardData(self)
        tcd.segment_index = index
        tcd.labels = self.labels[index]
        tcd.title = self.titles[index]
        tcd.marked = self.marked[index]
        tcd.summary = self.summaries[index]

        tcd.dists_stats = {}
        tcd.dists_stats['speaker'] = self.speaker_time_by_role(index)

        for key in self.multi_time:
            tcd.dists_stats[key] = self.GetTimeSeries(key, index).LabelDistribution()

        tcd.text_notes = self.quotes_note[index]
        tcd.text_dialogues = self.quotes_text[index]
        tcd.pos_start_sec = start_ts[index]
        tcd.pos_end_sec = end_ts[index]
        tcd.thumbnail_crops = self.thumbnail_info[index]
        #tcd.aoi_activity_distr = {k: 7 * v for k, v in tcd.aoi_activity_distr.items()}
        return tcd

    @pyqtSlot(int, result=bool)
    def ToggleMark(self, segmentIdx):
        self.marked[segmentIdx] = not self.marked[segmentIdx]
        return self.marked[segmentIdx]

    @pyqtSlot(list, list, float, result=list)
    def GetCardLayout(self, target_loc, widths, max_xpos):
        out = linear_layout(
            sorted(target_loc), widths, min_xpos=widths[0] / 2, max_xpos=max_xpos
        )
        return out.tolist() if out is not None else list()

    @pyqtSlot(int, bool)
    def SetHasCard(self, index, flag):
        self.has_card[index] = flag

    @pyqtSlot(int, result=bool)
    def ToggleHasCard(self, index):
        self.has_card[index] = not self.has_card[index]
        return self.has_card[index]

    @pyqtSlot(int, result=bool)
    def HasCard(self, index):
        return self.has_card[index]

    @pyqtSlot(float, str, str)
    def AddNote(self, ts, text, label):
        self.notes_model.AddNote(ts, text, label)

    @pyqtSlot(int, str)
    def SetQuoteNote(self, index, text):
        self.quotes_note[index] = text

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

    @pyqtSlot(int, str)
    def SetQuoteText(self, index, text):
        text_units = text.split('\n\n')
        text_units = [t.replace('\n', ' ').strip() for t in text_units if len(t) > 0]
        formatted = []
        speaker_quotes = []

        for tu in text_units:
            results = []

            for line in self.GetUtteranceSpeakerPairs(index):
                line_text = line['text'].replace('\n', ' ').strip()
                match = longest_common_substring(tu, line_text)

                src = line['speaker']
                cnt = sum(other_src == src for other_src, _, _ in results)
                results.append((src, cnt, match))

            max_idx = np.argmax([res['size'] for _, _, res in results])
            src, idx, res = results[max_idx]

            if (res['size'] / len(tu)) > 0.5:
                quote_label = f'{src.upper()[:2]}{idx + 1}'

                if quote_label not in self.labels[index]:
                    self.labels[index].append(quote_label)

                formatted.append(
                    f'{tu[0 : res["a"]]} <font color="grey"><b>{quote_label}</b></font> <font color="black"><u>{tu[res["a"] : res["a"] + res["size"]]}</u></font>{tu[res["a"] + res["size"] :]}'
                )
                speaker_quotes.append(
                    {'speaker': src, 'label': quote_label ,'text': tu[res['a'] : res['a'] + res['size']]},
                )
            else:
                formatted.append(tu)

        formatted = '<br><br>'.join(formatted)
        self.quotes_text[index] = {'original': text,
                                   'formatted': formatted,
                                   'quotes': speaker_quotes}

    @pyqtSlot(int, result=NotesModel)
    def GetNotes(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return self.notes_model.slice(start_ts, end_ts)

    @pyqtSlot(int, result='QVariantMap')
    def GetMultiRecData(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return {
            rec_id: multimodal_data.slice(start_ts, end_ts)
            for rec_id, multimodal_data in self.multimodal_recordings.items()
        }

    @pyqtSlot(str, int, result=StackedSeries)
    def GetTimeSeries(self, key, index):
        if key not in self.multi_time:
            logging.error(
                f'Cannot access time series "{key}". Currently registered timelines: {self.multi_time.keys()}.',  # noqa: G004
            )

        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]

        self.multi_time[key].recompute(self.active_labels)
        return self.multi_time[key].slice(start_ts, end_ts)

    @pyqtSlot(int, result=list)
    def GetRegisteredTimeSeries(self, index:int):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return [mt.slice(start_ts, end_ts) for mt in self.multi_time.values()]

    @pyqtSlot(int, result=str)
    def GetNotesCard(self, index):
        return self.notes_card[index]

    @pyqtSlot(int, result=str)
    def GetDialogueCard(self, index):
        return self.dialogue_card[index]

    @pyqtSlot(int, result=int)
    def GetCardSize(self, index):
        return self.card_sizes[index]

    @pyqtSlot(int, str)
    def SetLabel(self, index, label):
        self.titles[index] = label
        # self.service.update_corpus_at(label, index)

    @pyqtSlot(int, result=str)
    def GetLabel(self, index):
        return self.titles[index]

    @pyqtSlot(int, result=str)
    def GetSummary(self, index):
        return self.summaries[index]

    @pyqtSlot(int, result=float)
    def GetPosStart(self, index):
        return self.start_ts[index]

    @pyqtSlot(int, result=float)
    def GetPosEnd(self, index):
        return self.end_ts[index]

    @pyqtSlot(result=float)
    def MinTimestamp(self):
        k = list(self.multimodal_recordings.keys())
        return self.multimodal_recordings[k[0]].MinTimestamp()
        # return self.start_ts[0]

    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        k = list(self.multimodal_recordings.keys())
        return self.multimodal_recordings[k[0]].MaxTimestamp()
        # return self.end_ts[-1]

    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.start_ts)
