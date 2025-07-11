import pandas as pd
import numpy as np
import shapely
import json
import logging

from PyQt6.QtCore import QObject, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QImage          
from PyQt6.QtMultimedia import QVideoSink


from utils import linear_layout, blend_images, longest_common_substring
from HeatmapProvider import HeatmapOverlayProvider
from ThumbnailProvider import ThumbnailProvider
from TimelineModel import SubjectMultimodalData
from NotesModel import NotesModel
from StackedSeries import StackedSeries
from TopicCard import TopicCardData


class TopicRootModel(QObject):
    queryResultsAvailable = pyqtSignal(int, list, list)

    def __init__(self, segments, subject_data, meta_model, video_src, parent=None):
        super().__init__(parent)
        self.segments = segments
        self.start_ts = self.segments['start timestamp [sec]'].tolist()
        self.end_ts = self.segments['end timestamp [sec]'].tolist()
        self.titles = self.segments['title'].tolist()
        self.summaries = self.segments['summary'].tolist()

        self.has_card = self.segments['Displayed'].tolist()
        self.video_src = video_src
        self.quotes_text = [{"original": "", "formatted": ""}] * len(self.start_ts)
        self.quotes_note = [""] * len(self.start_ts)
        self.thumbnail_provider = ThumbnailProvider()
        self.thumbnail_info = [[] for _ in self.start_ts]
        self.marked = [False] * len(self.start_ts)

        self.labels = [[] for _ in self.start_ts]
        self.card_sizes = [385 for _ in self.start_ts]

        self.dialogue_line = subject_data
        self.dialogue_line.setParent(self)

        self.meta_model = meta_model
        self.meta_model.setParent(self)
        
        self.active_labels = self.meta_model.Labels()

        self.set_notes(NotesModel.empty())
        self.set_attention(StackedSeries.empty(meta_model.Labels(), self.start_ts[0], self.end_ts[-1]))
        self.set_activity(StackedSeries.empty(meta_model.Labels(), self.start_ts[0], self.end_ts[-1]))

        self.has_attention = False
        self.has_activity = False

        self.has_gaze_heatmaps = False
        self.has_move_heatmaps = False

        self.gaze_overlay_data = {}
        self.gaze_overlay_ids = []

    def set_notes(self, notes: NotesModel):
        self.notes_model = notes
        self.notes_model.setParent(self)
        self.has_notes = True

    def set_activity(self, activity: StackedSeries):
        self.activity = activity
        self.activity.setParent(self)
        self.has_activity = True

    def set_attention(self, attention: StackedSeries):
        self.attention = attention
        self.attention.setParent(self)
        self.has_attention = True

    def set_gaze_data(self, gaze_data):
        self.gaze_overlay_ids = list(gaze_data.keys())
        self.gaze_overlay_data = gaze_data

    def set_heatmap_provider_gaze(self, heatmap_provider_gaze: HeatmapOverlayProvider):
        self.heatmap_provider_gaze = heatmap_provider_gaze
        self.heatmap_provider_gaze.segments_start = self.start_ts
        self.heatmap_provider_gaze.segments_end = self.end_ts
        self.has_gaze_heatmaps = True

    def set_heatmap_provider_move(self, heatmap_provider_move: HeatmapOverlayProvider):
        self.heatmap_provider_move = heatmap_provider_move
        self.heatmap_provider_move.segments_start = self.start_ts
        self.heatmap_provider_move.segments_end = self.end_ts
        self.has_move_heatmaps = True

    """
    @pyqtSlot(int, result=list)
    def FindSimilarSegments(self, segment_idx):
        self.service.exec_query(self.titles[segment_idx], top_k=5, meta={'target_index': segment_idx})
        return list()
    """

    def process_query_results(self, res):
        self.queryResultsAvailable.emit(res['meta']['snippet_index'], res['result']['scores'], res['result']['indices'])

    @pyqtSlot(result='QVariantMap')
    def GazeOverlayData(self):
        return self.gaze_overlay_data

    @pyqtSlot(result=list)
    def GazeOverlayIDs(self):
        return self.gaze_overlay_ids

    @pyqtSlot(str, int, result=list)
    def FindSimilarSegments(self, text, snippet_idx):
        self.service.exec_query(text, top_k=30, meta={'snippet_index': snippet_idx})
        return list()

    @pyqtSlot(QVideoSink, float, int, float, float, float, float, str)
    def RegisterVideoCrop(self, videoSink, pos_ms, segmentIdx, norm_x, norm_y, norm_width, norm_height, overlay_src):
        img = videoSink.videoFrame().toImage()
        size = img.size()

        x = int(norm_x * size.width())
        y = int(norm_y * size.height())

        width = int(norm_width * size.width())
        height = int(norm_height * size.height())
        
        selection_shape = shapely.box(x, y, x+width, y+height)
        aoi_scores = {}

        for label, aoi_data in self.meta_model.shapes.items():
            aoi_shape = shapely.Polygon(aoi_data['points'])
            inter_shape = shapely.intersection(aoi_shape, selection_shape)
            aoi_scores[label] = shapely.area(inter_shape) / shapely.area(aoi_shape)

        crop = img.copy(x, y, width, height)

        if overlay_src == "gaze":
            heat_gaze = self.heatmap_provider_gaze.compute_overlay(self.start_ts[segmentIdx], self.end_ts[segmentIdx])
            heat_gaze_img, _ = self.heatmap_provider_gaze.requestImage(self.heatmap_provider_gaze.img_id(segmentIdx), QSize())
            crop_heat_gaze_img = heat_gaze_img.copy(x, y, width, height)

            score = heat_gaze[y: y+height, x: x+width].sum() / heat_gaze.sum()
            crop = blend_images(crop, crop_heat_gaze_img)

        elif overlay_src == "move":
            heat_move = self.heatmap_provider_move.compute_overlay(self.start_ts[segmentIdx], self.end_ts[segmentIdx])
            heat_move_img, _ = self.heatmap_provider_move.requestImage(self.heatmap_provider_move.img_id(segmentIdx), QSize())

            crop_heat_move_img = heat_move_img.copy(x, y, width, height)
            crop = blend_images(crop, crop_heat_move_img)
            score = heat_move[y: y+height, x: x+width].sum() / heat_move.sum()
        
        else:
            score = -1
        
        total_score = sum(aoi_scores.values())
        aoi_scores = {label: score / total_score for label, score in aoi_scores.items()}
        img_id, label = self.thumbnail_provider.add_to_collection(segmentIdx, crop, overlay_src)

        self.labels[segmentIdx].append(label)

        info = {'img_id': img_id, 
                'path': 'image://thumbnails/' + img_id,
                'score': float(score), 
                'within_aois': [label for label, score in aoi_scores.items() if score >= 0.25],
                'pos_ms': float(pos_ms), 
                'label': label}

        self.thumbnail_info[segmentIdx].append(info)

    @pyqtSlot(list, result=list)
    def KeywordMatchesAtTitles(self, keywords):
        matched_indices = []

        for segment_idx in range(len(self.start_ts)):
            s = self.GetDialogueLine(segment_idx).toString().lower()
            for kw in keywords:
                kw = kw.lower()
                if kw in s:
                    matched_indices.append(segment_idx)
                    break

        return matched_indices

    @pyqtSlot(int, result=list)
    def ThumbnailIndicatorPositions(self, segment_idx):
        return [(1e-3*info['pos_ms'] - self.GetPosStart(segment_idx)) / (self.GetPosEnd(segment_idx) - self.GetPosStart(segment_idx)) for info in self.thumbnail_info[segment_idx]]

    @pyqtSlot(int, result=list)
    def ThumbnailIndicatorLabels(self, segment_idx):
        return [info['label'] for info in self.thumbnail_info[segment_idx]]

    @pyqtSlot(int, result=list)
    def VideoCropSources(self, segment_idx):
        return self.thumbnail_info[segment_idx]

    @pyqtSlot(int, result=list)
    def VideoCropLabels(self, segment_idx):
        return [info['label'] for info in self.thumbnail_info[segment_idx]]

    @pyqtSlot(int, result=str)
    def HeatmapGazeSource(self, segment_idx):
        if self.has_gaze_heatmaps:
            return f'image://heatmaps_gaze/' + self.heatmap_provider_gaze.img_id(segment_idx)
        return ""

    @pyqtSlot(int, result=str)
    def HeatmapMoveSource(self, segment_idx):
        if self.has_move_heatmaps:
            return f'image://heatmaps_move/' + self.heatmap_provider_move.img_id(segment_idx)
        return ""

    @pyqtSlot(int, result=list)
    def VideoCropAspectRatios(self, segment_idx):
        img_ids = self.thumbnail_provider.collection_thumbnails(segment_idx)
        aspect_ratios = []

        for img_id in img_ids:
            img = self.thumbnail_provider.thumbnails[img_id]['image']
            aspect_ratios.append(img.width() / img.height() if img.width() > 0 else 0)
        return aspect_ratios

    def delete_segment(self, target_idx):
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

        if self.has_gaze_heatmaps:
            self.heatmap_provider_gaze.segments_start = self.start_ts
            self.heatmap_provider_gaze.segments_end = self.end_ts

        if self.has_move_heatmaps:
            self.heatmap_provider_move.segments_start = self.start_ts
            self.heatmap_provider_move.segments_end = self.end_ts

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

        if self.has_gaze_heatmaps:
            self.heatmap_provider_gaze.segments_start = self.start_ts
            self.heatmap_provider_gaze.segments_end = self.end_ts

        if self.has_move_heatmaps:
            self.heatmap_provider_move.segments_start = self.start_ts
            self.heatmap_provider_move.segments_end = self.end_ts

    @pyqtSlot(result=str)
    def VideoSourceTopDown(self):
        return "file:///" + self.video_src['workspace']['path']

    @pyqtSlot(result=list)
    def VideoSourcesPeripheral(self):
        return ["file:///" + str(self.video_src['room']['path'])]

    @pyqtSlot(result=int)
    def SpeechLineCount(self):
        return self.dialogue_line.SpeechLineCount()

    @pyqtSlot(result=bool)
    def HasAttention(self):
        return self.has_attention

    @pyqtSlot(result=bool)
    def HasActivity(self):
        return self.has_activity

    @pyqtSlot(result=bool)
    def HasGazeHeatmap(self):
        return self.has_gaze_heatmaps

    @pyqtSlot(result=bool)
    def HasMoveHeatmap(self):
        return self.has_move_heatmaps

    @pyqtSlot(str)
    def ToggleLabel(self, label):
        if label in self.active_labels:
            self.active_labels.remove(label)
        else:
            self.active_labels.append(label)

    @pyqtSlot(list, result='QVariantMap')
    def SpeakerTimeDistribution(self, segmentIndices):
        if len(segmentIndices) == 0:
            segmentIndices = range(len(self.start_ts))

        speaker_time = {}
        total_dur = 0

        for idx in segmentIndices:
            s = self.GetDialogueLine(idx)
            for speaker_id, dur in s.SpeakerTimeTotal().items():
                speaker_time[speaker_id] = speaker_time.get(speaker_id, 0) + dur
                total_dur += dur
        
        #total_dur = self.end_ts[max(segmentIndices)] - self.start_ts[min(segmentIndices)]
        out = {k: float(v / total_dur) for k, v in speaker_time.items()}
        return out
        

    @pyqtSlot(int, result=TopicCardData)
    def GetTopicCardData(self, index):
        start_ts = self.start_ts
        end_ts = self.end_ts
        
        dia_line = self.dialogue_line.slice(start_ts[index], end_ts[index])

        tcd = TopicCardData(self)
        tcd.segment_index = index
        tcd.labels = self.labels[index]
        tcd.title = self.titles[index]
        tcd.marked = self.marked[index]
        tcd.summary = self.summaries[index]
        tcd.speaker_role_time_distr = dia_line.SpeakerRoleTimeDistribution()
        tcd.speaker_time_distr = dia_line.SpeakerTimeDistribution()
        tcd.aoi_activity_distr = self.activity.slice(start_ts[index], end_ts[index]).LabelDistribution()
        tcd.aoi_attention_distr = self.attention.slice(start_ts[index], end_ts[index]).LabelDistribution()
        tcd.text_notes = self.quotes_note[index]
        tcd.text_dialogues = self.quotes_text[index]
        tcd.pos_start_sec = start_ts[index]
        tcd.pos_end_sec = end_ts[index]
        tcd.thumbnail_crops = self.thumbnail_info[index]
        tcd.heatmap_gaze_src = self.HeatmapGazeSource(index)
        tcd.heatmap_move_src = self.HeatmapMoveSource(index)

        
        tcd.aoi_activity_distr = {k: 7*v for k, v in tcd.aoi_activity_distr.items()}

        return tcd

        
    def import_state(self, in_dir):
        for card_dir in in_dir.iterdir():
            if not card_dir.is_dir():
                continue

            idx = int(card_dir.name)
            with open(card_dir / 'card_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.marked[idx] = data['marked']
                self.titles[idx] = data['title']
                self.quotes_note[idx] = data['text_notes']
                self.quotes_text[idx] = data['text_dialogues']
                self.thumbnail_info[idx] = data['thumbnail_info']

                for img_path in (card_dir / 'thumbnails').iterdir():
                    img = QImage(str(img_path))
                    self.thumbnail_provider.thumbnails[img_path.stem] = {'image': img, 'segment_idx': idx, 'type': 'unknown'}


    def export_state(self, out_dir):
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
                    thumbnail_info = self.thumbnail_info[idx]
                    
                    out_json = {'marked': marked, 'title': title, 'text_notes': text_notes, 'text_dialogues': text_dialogues, 'thumbnail_info': thumbnail_info}
                    json.dump(out_json, f, ensure_ascii=False, indent=4)

                    thumbnail_dir = sub_dir / 'thumbnails'
                    thumbnail_dir.mkdir(parents=True, exist_ok=True)

                    for info in thumbnail_info:
                        img, _ = self.thumbnail_provider.requestImage(info['img_id'] + '#0', QSize()) 
                        success = img.save(str(thumbnail_dir / f'{info["img_id"]}.png'))

                        if not success:
                            raise ValueError(f"Failed to save {info['img_id']}")
            except Exception as e:
                return False
        return True
                

                    

    @pyqtSlot(int, result=bool)
    def ToggleMark(self, segmentIdx):
        self.marked[segmentIdx] = not self.marked[segmentIdx]
        return self.marked[segmentIdx]

    @pyqtSlot(list, list, float, result=list)
    def GetCardLayout(self, target_loc, widths, max_xpos):
        out = linear_layout(sorted(target_loc), widths, min_xpos=widths[0]/2, max_xpos=max_xpos)
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

    @pyqtSlot(int, str)
    def SetQuoteText(self, index, text):
        text_units = text.split('\n\n')
        text_units = [t.replace('\n', ' ').strip() for t in text_units if len(t) > 0]
        formatted = []
        
        for tu in text_units:
            results = []

            for line in self.GetDialogueLine(index).FullDialogue():
                line_text = line['text'].replace('\n', ' ').strip()
                match = longest_common_substring(tu, line_text)

                src = line['src']
                cnt = sum(other_src == src for other_src, _, _ in results)
                results.append((src, cnt, match))
            
            max_idx = np.argmax([res['size'] for _, _,  res in results])
            src, idx, res = results[max_idx]

            if (res['size'] / len(tu)) > 0.5:
                quote_label = f'{src.upper()[:2]}{idx+1}'

                if quote_label not in self.labels[index]:
                    self.labels[index].append(quote_label)

                formatted.append(f'{tu[0: res["a"]]} <font color="grey"><b>{quote_label}</b></font> <font color="black"><u>{tu[res["a"]: res["a"]+res["size"]]}</u></font>{tu[res["a"]+res["size"]:]}')
            else:
                formatted.append(tu)

        formatted = '<br><br>'.join(formatted)
        self.quotes_text[index] = {'original': text, 'formatted': formatted}

    @pyqtSlot(int, result=SubjectMultimodalData)
    def GetDialogueLine(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return self.dialogue_line.slice(start_ts, end_ts)


    @pyqtSlot(int, result=NotesModel)
    def GetNotes(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        return self.notes_model.slice(start_ts, end_ts)


    @pyqtSlot(int, result=StackedSeries)
    def GetAoiAttention(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]
        self.activity.recompute(self.active_labels)
        return self.attention.slice(start_ts, end_ts)


    @pyqtSlot(int, result=StackedSeries)
    def GetAoiActivity(self, index):
        start_ts = self.start_ts[index]
        end_ts = self.end_ts[index]

        self.activity.recompute(self.active_labels)

        return self.activity.slice(start_ts, end_ts)

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
        #self.service.update_corpus_at(label, index)

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
        return self.dialogue_line.MinTimestamp()

    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        return self.dialogue_line.MaxTimestamp()

    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.start_ts)
    

    
