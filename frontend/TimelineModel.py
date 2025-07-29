import pandas as pd
import logging

from collections import defaultdict
from itertools import chain
from PyQt6.QtCore import QObject, pyqtSlot


pd.options.mode.chained_assignment = None  # default='warn'


def merge_entries(df, time_delta_threshold=.5):
    merged_rows = []
    for _, row in df.iterrows():
        if len(merged_rows) > 1:
            time_delta = row['start timestamp [sec]'] - merged_rows[-1]['end timestamp [sec]']
            event_subtype_match = row['event subtype'] == merged_rows[-1]['event subtype']

            if time_delta < time_delta_threshold and event_subtype_match:
                merged_rows[-1]['end timestamp [sec]'] = row['end timestamp [sec]']
                merged_rows[-1]['event data'] = merged_rows[-1]['event data'] + " " + row['event data']
            else:
                merged_rows.append(row)
        else:
            merged_rows.append(row)
    return pd.DataFrame(merged_rows)


class SubjectData(QObject):
    pass

class SubjectMultimodalData(QObject):
    pass

class SubjectMultimodalData(QObject):
    REQUIRED_COLUMNS = ['start timestamp [sec]', 'end timestamp [sec]', 'event type', 'event subtype', 'event data']

    def __init__(self, multimodal_data, min_timestamp, max_timestamp, parent=None):
        super().__init__(parent)

        for subject_data in multimodal_data.values():
            subject_data.parent = self

        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp
        self.multimodal_data = multimodal_data

    @classmethod
    def from_recordings(cls, meta, min_timestamp, max_timestamp):
        multimodal_rec = {}
        unique_subtypes = defaultdict(set)

        for rec in meta['recordings']:
            multimodal_data = {}

            for data_type in rec['artifacts']:
                data_table = pd.read_csv(rec['artifacts'][data_type]['path'])
                data_table = merge_entries(data_table)
                data_table = data_table[(data_table['start timestamp [sec]'] >= min_timestamp) & (data_table['end timestamp [sec]'] <= max_timestamp)]

                if not set(cls.REQUIRED_COLUMNS).issubset(data_table.columns):
                    logging.error(f'Artifact "{data_type}" of recording "{rec["id"]}" has missing columns. Required columns are: {cls.REQUIRED_COLUMNS}')
                    continue
                
                subject_data = SubjectData(data_table, rec['id'])
                subject_data.max_timestamp = max_timestamp
                subject_data.min_timestamp = min_timestamp
                multimodal_data[data_type] = subject_data

                unique_subtypes[data_type] = unique_subtypes[data_type].union(subject_data.category)

            multimodal_rec[rec['id']] = cls(multimodal_data, min_timestamp, max_timestamp)

        return multimodal_rec, unique_subtypes

    @classmethod
    def fill_missing_datatype(cls, multimodal_rec):
        all_datatypes = [md.AvailableDataTypes() for md in multimodal_rec.values()]
        available_datatypes = set(chain.from_iterable(all_datatypes))

        for rec_id in multimodal_rec.keys():
            for dt in available_datatypes:
                if dt not in multimodal_rec[rec_id].multimodal_data:
                    multimodal_rec[rec_id].multimodal_data[dt] = SubjectData(pd.DataFrame.from_records(data=[], columns=cls.REQUIRED_COLUMNS), rec_id)
        

    @pyqtSlot(float, float, result=SubjectMultimodalData)
    def slice(self, start_ts, end_ts):
        slices = {data_type : subject_data.slice(start_ts, end_ts) for data_type, subject_data in self.multimodal_data.items()}
        return SubjectMultimodalData(slices, start_ts, end_ts, parent=self)


    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        return self.max_timestamp


    @pyqtSlot(result=float)
    def MinTimestamp(self):
        return self.min_timestamp


    @pyqtSlot(str, result=SubjectData)
    def SubjectData(self, data_type):
        return self.multimodal_data[data_type]


    @pyqtSlot(result=list)
    def AvailableDataTypes(self):
        return list(self.multimodal_data.keys())


class SubjectData(QObject):
    def __init__(self, table, sid, parent=None):
        super().__init__(parent)
        self.table = table.copy()
        self.sid = sid
        self.start_ts = table['start timestamp [sec]'].tolist()
        self.end_ts = table['end timestamp [sec]'].tolist()
        self.event_data = table['event data'].tolist()
        self.category = table['event subtype'].tolist()
        self.max_timestamp = 0
        self.min_timestamp = 0

    
    @pyqtSlot(float, float, result=SubjectData)
    def slice(self, start_ts, end_ts):
        mask = (self.table['start timestamp [sec]'] >= start_ts) & (self.table['end timestamp [sec]'] < end_ts)

        tm = SubjectData(self.table[mask], self.sid, parent=self)
        tm.min_timestamp = start_ts
        tm.max_timestamp = end_ts
        return tm


    @pyqtSlot(result='QVariantMap')
    def SubtypeDistribution(self):
        subtype_dur = {}

        for _, row in self.table.iterrows():
            duration = row['end timestamp [sec]'] - row['start timestamp [sec]']
            subtype_dur[row['event subtype']] = subtype_dur.get(row['event subtype'], 0) + duration

        total_dur = self.max_timestamp - self.min_timestamp
        return {k: float(v / total_dur) for k, v in subtype_dur.items()}

        
    @pyqtSlot(result=str)
    def FullText(self):
        full_text = ' '.join(self.event_data)
        return f'{self.sid} : "{full_text}"'

    @pyqtSlot(result=bool)
    def HasText(self):
        full_text = ''.join(self.event_data)
        return len(full_text) > 0

    @pyqtSlot(int, result=float)
    def PosStartSec(self, index):
        return self.start_ts[index]

    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        return self.max_timestamp

    @pyqtSlot(result=str)
    def Identifier(self):
        return self.sid

    @pyqtSlot(result=str)
    def Role(self):
        return self.role

    @pyqtSlot(int, result=str)
    def Category(self, index):
        return self.category[index]

    @pyqtSlot(result=float)
    def MinTimestamp(self):
        return self.min_timestamp

    """
    @pyqtSlot(int, result=bool)
    def IsInterrogative(self, index):
        return "?" in self.event_data[index]

    @pyqtSlot(int, result=bool)
    def IsEngaging(self, index):
        return "interesting" in self.event_data[index]
    """

    @pyqtSlot(int, result=float)
    def PosEndSec(self, index):
        return self.end_ts[index]

    @pyqtSlot(int, result=str)
    def EventData(self, index):
        return self.event_data[index]
    
    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.start_ts)
