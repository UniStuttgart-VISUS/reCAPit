import sys
import pandas as pd
import json
import argparse
import threading
import datetime
import logging

from StackedSeries import StackedSeries
from pathlib import Path
from NotesModel import *
from TimelineModel import *
from TopicCard import *
from TopicModel import *
from AppConfig import *
from CustomVideoOutput import CustomVideoOutput
from HeatmapProvider import HeatmapOverlayProvider

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QSurfaceFormat 
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType


class WorkerThread(threading.Thread):
    def __init__(self, result_queue, model : TopicRootModel, daemon=False):
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


def filter_segments(topics, min_dur_1, min_dur_2):
    topics['Displayed'] = True
    topics = topics[topics['duration [sec]'] > min_dur_1]
    topics.loc[topics['duration [sec]'] < min_dur_2, 'Displayed'] = False
    return topics


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


def fix_notes(notes):
    notes['center timestamp [sec]'] = notes['start timestamp [sec]'] + (notes['end timestamp [sec]'] - notes['start timestamp [sec]']) * 0.5
    notes['label'] = ''
    notes['source'] = 'online'
    return notes


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--user_config', type=Path, required=True)
    parser.add_argument('--state_id', type=str, required=False)
    parser.add_argument('--multisampling', type=int, required=False, default=4)
    args = parser.parse_args()

    root_dir = args.manifest.parent
    manifest = json.load(open(args.manifest, 'r'))
    user_config = json.load(open(args.user_config, 'r'))

    transcript_file = Path(manifest['artifacts']['transcript']['path'])
    aoi_file = Path(manifest['sources']['areas_of_interests']['path'])
    topic_segments_file = Path(manifest['artifacts']['segments']['refined']['path'])

    if not topic_segments_file.is_file(): 
        logging.error(f'Path "{topic_segments_file}" does to refer to valid topic segments!')
        exit()
            
    if not aoi_file.is_file():
        logging.error(f'Path "{topic_segments_file}" does to refer to valid AOIs!')
        exit()

    min_timestamp = 0
    max_timestamp = manifest['duration_sec']

    original_topics = pd.read_csv(topic_segments_file)
    topics = filter_segments(original_topics, min_dur_1=user_config['segments']['min_dur_sec'], min_dur_2=user_config['segments']['display_dur_sec'])
    topics = fill_between(topics, max_ts=max_timestamp)

    dialogue_line, event_subtypes = SubjectMultimodalData.from_recordings(manifest, min_timestamp, max_timestamp)
    SubjectMultimodalData.fill_missing_datatype(dialogue_line)

    manifest_model = AppConfig(manifest, user_config, event_subtypes)
    topic_segments = TopicRootModel(topics, dialogue_line, manifest_model, video_src=manifest['sources']['videos'])
    
    qf = QSurfaceFormat()
    qf.setSamples(user_config['multisampling'])
    QSurfaceFormat.setDefaultFormat(qf);

    app = QApplication(sys.argv)
    qmlRegisterType(CustomVideoOutput, 'com.kochme.media', 1, 0, 'CustomVideoOutput')

    engine = QQmlApplicationEngine()
    engine.addImageProvider('thumbnails', topic_segments.thumbnail_provider)

    for mt in manifest['artifacts']['multi_time']:
        path = Path(manifest['artifacts']['multi_time'][mt]['path'])
        if not path.is_file():
            continue

        logging.info(f'Processing multi time signal {path} ...')
        signal = pd.read_csv(path)
        stacks = StackedSeries.from_signals(signal, min_ts=min_timestamp, max_ts=max_timestamp,labels=manifest_model.Labels(), log_transform=user_config['streamgraph'][mt]['log_scale'])
        topic_segments.register_multi_time(mt, stacks)

    for vo in manifest['artifacts']['video_overlay']:
        path = Path(manifest['artifacts']['video_overlay'][vo]['path'])
        if not path.is_file():
            continue

        logging.info(f'Processing video overlay {path} ...')
        heatmap_info = pd.read_csv(path)
        heatmap_info['filename'] = heatmap_info['filename'].apply(lambda x: path.parent / x)
        heatmap_overlay_provider = HeatmapOverlayProvider(heatmap_info, cmap=user_config['video_overlay'][vo]['colormap'])
        overlay_root = topic_segments.add_video_overlay_provider(vo, heatmap_overlay_provider)
        engine.addImageProvider(overlay_root, heatmap_overlay_provider)

    if transcript_file.is_file():
        logging.info(f'Registering transcript {transcript_file} ...')
        transcript = pd.read_csv(transcript_file)
        topic_segments.set_transcript(transcript)

    if 'notes_diff' in manifest['artifacts']:
        notes_diffs_file = Path(manifest['artifacts']['notes_diff']['path'])
        logging.info(f'Registering notes file {notes_diffs_file} ...')
        notes_model = NotesModel(fix_notes(pd.read_csv(notes_diffs_file)))
        topic_segments.set_notes(notes_model)

    if args.state_id is not None:
        load_dir = root_dir / 'states' / args.state_id
        topic_segments.import_state(in_dir=Path(load_dir))
        logging.info(f'Successfully loaded state from: "{load_dir}"!')

    engine.rootContext().setContextProperty('aoiModel', manifest_model)
    engine.rootContext().setContextProperty('topicSegments', topic_segments)
    engine.load('App.qml')

    window = engine.rootObjects()[0]
    window.setProperty("title", str(root_dir))

    def quitApp():
        engine.deleteLater()
        curr_date = datetime.datetime.now().strftime('%Y-%m-%d')
        curr_time = datetime.datetime.now().strftime('%H-%M-%S')

        out_dir = root_dir / 'states' / curr_date / curr_time
        out_dir.mkdir(parents=True, exist_ok=True)

        if topic_segments.export_state(out_dir=out_dir):
            logging.info(f'Successfully saved current state to: "{out_dir}"!')

    app.aboutToQuit.connect(quitApp)
    sys.exit(app.exec())

