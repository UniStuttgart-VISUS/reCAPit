import argparse
import datetime
import json
import logging
import sys
import threading
import pandas as pd

logger = logging.getLogger(__name__)

from pathlib import Path
from AppConfig import AppConfig
from CustomVideoOutput import CustomVideoOutput
from HeatmapProvider import HeatmapOverlayProvider
from NotesModel import NotesModel
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication
from SegmentModel import SegmentModel
from StackedSeries import StackedSeries
from TimelineModel import SubjectMultimodalData


class WorkerThread(threading.Thread):
    def __init__(self, result_queue, model : SegmentModel, daemon=False):
        super().__init__(daemon=daemon)
        self.result_queue = result_queue
        self.model = model
        self.stop = False
        self.target_obj = None
        self.history = []

    def close(self):
        self.stop = True
        self.result_queue.put({'result': '', 'meta': {}})

    def run(self):
        while not self.stop:
            res = self.result_queue.get(block=True)
            self.model.process_query_results(res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--user_config', type=Path, required=True)
    parser.add_argument('--savefile_id', type=str, required=False)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    root_dir = args.user_config.parent
    manifest = json.load(open(args.manifest, encoding='utf-8'))
    user_config = json.load(open(args.user_config, encoding='utf-8'))

    if 'refined' in manifest['artifacts']['segments']:
        topic_segments_file = Path(manifest['artifacts']['segments']['refined']['path'])
    elif 'initial' in manifest['artifacts']['segments']:
        topic_segments_file = Path(manifest['artifacts']['segments']['initial']['path'])
    else:
        logger.error('No registered segments in manifest!')
        sys.exit()

    if 'areas_of_interests' not in manifest['sources']:
        logger.error('No registered areas_of_interests in manifest!')
        sys.exit()

    transcript_file = Path(manifest['artifacts']['transcript']['path'])
    aoi_file = Path(manifest['sources']['areas_of_interests']['path'])

    if not aoi_file.is_file():
        logger.error('Path "%s" does to refer to valid AOIs!', topic_segments_file)
        sys.exit()

    if not topic_segments_file.is_file(): 
        logger.error('Path "%s" does to refer to valid topic segments!', topic_segments_file)
        sys.exit()

    min_timestamp = 0
    max_timestamp = manifest['duration_sec']

    segments = pd.read_csv(topic_segments_file)
    dialogue_line, event_subtypes = SubjectMultimodalData.from_recordings(manifest, min_timestamp, max_timestamp)
    SubjectMultimodalData.fill_missing_datatype(dialogue_line)

    manifest_model = AppConfig(manifest, user_config, event_subtypes)
    segment_model = SegmentModel(segments, dialogue_line, manifest_model, video_src=manifest['sources']['videos'])
    segment_model.AdjustFilter(manifest_model.SegmentMinDurSec(), manifest_model.SegmentDisplayDurSec())

    qf = QSurfaceFormat()
    qf.setSamples(user_config['multisampling'])
    QSurfaceFormat.setDefaultFormat(qf)

    app = QApplication(sys.argv)
    qmlRegisterType(CustomVideoOutput, 'com.kochme.media', 1, 0, 'CustomVideoOutput')

    engine = QQmlApplicationEngine()
    engine.addImageProvider('thumbnails', segment_model.thumbnail_provider)

    for mt, conf in user_config['streamgraph'].items():
        path = Path(manifest['artifacts']['multi_time'][conf['source']]['path'])
        if not path.is_file():
            continue

        logger.info('Processing multi time signal %s ...', path)
        signal = pd.read_csv(path)
        stacks = StackedSeries.from_signals(signal, min_ts=min_timestamp, max_ts=max_timestamp,labels=manifest_model.Labels(), log_transform=user_config['streamgraph'][mt]['log_scale'])
        segment_model.register_multi_time(mt, stacks)

    if 'video_overlay' in manifest['artifacts']:
        for vo in manifest['artifacts']['video_overlay']:
            path = Path(manifest['artifacts']['video_overlay'][vo]['path'])
            if not path.is_file():
                continue

            logger.info('Processing video overlay %s ...', path)
            heatmap_info = pd.read_csv(path)
            heatmap_info['filename'] = heatmap_info['filename'].apply(lambda x: path.parent / x)
            heatmap_overlay_provider = HeatmapOverlayProvider(heatmap_info, cmap=user_config['video_overlay'][vo]['colormap'])
            overlay_root = segment_model.add_video_overlay_provider(vo, heatmap_overlay_provider)
            engine.addImageProvider(overlay_root, heatmap_overlay_provider)

    if transcript_file.is_file():
        logger.info('Registering transcript %s ...', transcript_file)
        transcript = pd.read_csv(transcript_file)
        segment_model.set_transcript(transcript)

    if 'notes' in manifest['artifacts']:
        notes_diffs_file = Path(manifest['artifacts']['notes']['path'])
        logger.info('Registering notes file %s ...', notes_diffs_file)
        notes_model = NotesModel(pd.read_csv(notes_diffs_file))
        segment_model.set_notes(notes_model)

    if args.savefile_id is not None:
        load_dir = root_dir / 'saved_state' / args.savefile_id
        segment_model.import_state(in_dir=Path(load_dir))
        logger.info('Successfully loaded save file: "%s"!', load_dir)

    engine.rootContext().setContextProperty('aoiModel', manifest_model)
    engine.rootContext().setContextProperty('topicSegments', segment_model)
    engine.load('App.qml')

    window = engine.rootObjects()[0]
    window.setProperty('title', str(root_dir))

    def quit_app() -> None:
        engine.deleteLater()
        curr_date = datetime.datetime.now().strftime('%Y-%m-%d')  # noqa: DTZ005
        curr_time = datetime.datetime.now().strftime('%H-%M-%S')  # noqa: DTZ005

        out_dir = root_dir / 'saved_state' / curr_date / curr_time
        out_dir.mkdir(parents=True, exist_ok=True)

        if manifest_model.export_user_config(args.user_config):
            logger.info('Successfully saved user config to: "%s"!', args.user_config)

        if segment_model.export_state(out_dir=out_dir):
            logger.info('Successfully saved current state to: "%s"!', out_dir)

    app.aboutToQuit.connect(quit_app)
    sys.exit(app.exec())
