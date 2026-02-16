from __future__ import annotations

from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from PyQt6.QtCore import QObject, QSize, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt6.QtGui import QImage
from PyQt6.QtMultimedia import QVideoSink
from StackedSeries import StackedSeries
from ThumbnailProvider import ThumbnailProvider, qimage_to_base64
from pathlib import Path
from TimelineModel import SubjectMultimodalData
from AppConfig import AppConfig
from TimelineSegmentModel import TimelineSegmentModel
from helper.manifest_manager import ManifestManager
from data_io import export_state, import_state

import TranscriptRecord
import TimelineSegment
import pandas as pd
import logging

from utils import (
    fill_between,
    fill_gaps,
    filter_segments,
    merge_transcript,
)

logger = logging.getLogger(__name__)

class Viewer(QObject):
    def __init__(
        self,
        man: ManifestManager,
        user_config: dict,
        export_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.thumbnail_provider = ThumbnailProvider()
        self.heatmap_overlay_providers = {}

        dialogue_line, event_subtypes = SubjectMultimodalData.from_recordings(man.get_recordings(), 
                                                                              0, man.get_duration_sec())
        SubjectMultimodalData.fill_missing_datatype(dialogue_line)

        self.app_config = AppConfig(man, user_config, export_dir, event_subtypes)
        self.segments = self.load_segments(man, user_config)
        self.transcript_records = self.load_transcript(self.segments, man)
        self.multi_time = self.load_multi_time(man, user_config)
        self.notes_model = self.load_notes(man)
        self.heatmap_overlay_providers = self.load_overlay_providers(man, user_config)

        """
        if args.savefile_id is not None:
            load_dir = self.data_dir / 'saved_state' / args.savefile_id
            self.segment_model.import_state(in_dir=Path(load_dir))
            logger.info('Successfully loaded save file: "%s"!', load_dir)
        """

        self.timeline_segments = TimelineSegmentModel(
                                    segments=self.segments,
                                    transcripts_records=self.transcript_records,
                                    stacked_data=self.multi_time,
                                    subject_data=dialogue_line,
                                    thumbnail_provider=self.thumbnail_provider,
                                    overlay_providers=self.heatmap_overlay_providers,
                                    notes_data=self.notes_model,
                                    roles=man.get_roles(),
                                    parent=self)


    def load_segments(self, man: ManifestManager, user_config: dict) -> list[TimelineSegment.TimelineSegment]:
        segments_info = man.get_artifact('segments')

        if 'refined' in segments_info:
            topic_segments_file = Path(segments_info['refined']['path'])
        elif 'initial' in segments_info:
            topic_segments_file = Path(segments_info['initial']['path'])
        else:
            logger.error('No registered segments in manifest!')
            raise ValueError

        min_dur_sec = user_config['segments']['min_dur_sec']
        display_dur_sec = user_config['segments']['display_dur_sec']

        segments = pd.read_csv(topic_segments_file)
        segments = fill_between(fill_gaps(segments, threshold_sec=5),
                                          max_ts=man.get_duration_sec())
        segments = filter_segments(segments, min_dur_sec, display_dur_sec)
        return TimelineSegment.from_dataframe(segments)


    def load_transcript(self, segments: list[TimelineSegment.TimelineSegment],
                        man: ManifestManager) -> list[list[TranscriptRecord.TranscriptRecord]]:

        transcript_file = Path(man.get_transcript()['path'])

        if not transcript_file.is_file():
            logger.error('Path "%s" does to refer to valid transcript file!', transcript_file)
            raise ValueError

        id_to_roles = {r['id']: r['role'] for r in man.get_recordings()}

        transcript = pd.read_csv(transcript_file)
        transcript_merged = merge_transcript(transcript)
        return TranscriptRecord.from_dataframe(transcript_merged,
                                               segments,
                                               id_to_roles.get)

    def load_notes(self, man: ManifestManager) -> NotesModel:
        if man.has_global_artifact('notes'):
            notes_diffs_file = Path(man.get_artifact('notes')['path'])
            logger.info('Registering notes file %s ...', notes_diffs_file)
            notes_model = NotesModel(pd.read_csv(notes_diffs_file))
        else:
            notes_model = NotesModel.empty()
        return notes_model

    def load_multi_time(self, man: ManifestManager, user_config: dict) -> None:
        stacked = {}
        for mt in user_config['streamgraph']:
            path = Path(man.get_artifact('multi_time')[mt]['path'])
            if not path.is_file():
                continue

            logger.info('Processing multi time signal %s ...', path)
            signal = pd.read_csv(path)
            stacks = StackedSeries.from_signals(signal,
                                                min_ts=0,
                                                max_ts=man.get_duration_sec(),
                                                labels=self.app_config.Labels(),
                                                log_transform=user_config['streamgraph'][mt]['log_scale'])
            stacked[mt] = stacks
        return stacked

    def load_overlay_providers(self, man: ManifestManager, user_config: dict) -> None:
        if not man.has_global_artifact('video_overlay'):
            return {}

        overlay_providers = {}

        for vo in man.get_artifact('video_overlay'):
            path = Path(man.get_artifact('video_overlay')[vo]['path'])
            if not path.is_file():
                continue

            logger.info('Processing video overlay %s ...', path)
            heatmap_info = pd.read_csv(path)
            heatmap_info['filename'] = heatmap_info['filename'].apply(lambda x: path.parent / x)
            heatmap_overlay_provider = HeatmapOverlayProvider(heatmap_info,
                                                              cmap=user_config['video_overlay'][vo]['colormap'])

            overlay_providers[vo] = heatmap_overlay_provider
        return overlay_providers

    @pyqtSlot(str, result=bool)
    def import_state(self, in_dir: str | Path) ->  bool:
        pass

    @pyqtSlot(str, result=bool)
    def export_state(self, out_dir: str | Path) -> bool:
        pass

    """
    @pyqtSlot(str, str)
    def UpdateOverlayColormap(self, name: str, cmap_str: str) -> None:
        self.heatmap_overlay_providers[name].set_colormap(cmap_str)


    @pyqtSlot(float, float)
    def AdjustFilter(self, min_dur_sec: float, display_dur_sec: float) -> None:
        segments = self.original_segments.copy()
        segments = filter_segments(segments, min_dur_sec, display_dur_sec)
        self.load_segments(segments)

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
    """
