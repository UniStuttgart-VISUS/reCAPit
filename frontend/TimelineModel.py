import pandas as pd
from PyQt6.QtCore import QObject, pyqtSlot
from pathlib import Path

pd.options.mode.chained_assignment = None  # default='warn'


def merge_speech(df, time_delta_threshold=.5):
    merged_rows = []

    for _, row in df.iterrows():
        if len(merged_rows) > 1:
            time_delta = row['start timestamp [sec]'] - merged_rows[-1]['end timestamp [sec]']

            if time_delta < time_delta_threshold:
                merged_rows[-1]['end timestamp [sec]'] = row['end timestamp [sec]']
                merged_rows[-1]['event data'] = merged_rows[-1]['event data'] + " " + row['event data']
            else:
                merged_rows.append(row)
        else:
            merged_rows.append(row)

    return pd.DataFrame(merged_rows, columns=['start timestamp [sec]', 'end timestamp [sec]', 'event type', 'event data', 'event subtype', 'category'])

class SubjectData(QObject):
    pass

class SubjectMultimodalData(QObject):
    pass

class SubjectMultimodalData(QObject):
    def __init__(self, speech_lines, aoi_lines, parent=None):
        super().__init__(parent)
        self.speech_lines = speech_lines
        self.aoi_lines = aoi_lines

        for s in self.speech_lines:
            s.parent = self

        for s in self.aoi_lines:
            s.parent = self

        self.out = {}

    @classmethod
    def from_recordings(cls, rec_root, meta, min_timestamp, max_timestamp):
        speech_lines = []
        aoi_lines = []

        for rec in meta['recordings']:
            data_table = pd.read_csv(Path(rec_root / rec['dir']) / 'data.csv')
            data_table = data_table[(data_table['start timestamp [sec]'] >= min_timestamp) & (data_table['end timestamp [sec]'] <= max_timestamp)]
            
            speech_data = data_table[data_table['event type'] == 'Speech']
            speech_data['category'] = rec['role']

            aoi_data = data_table[data_table['event type'] == 'Surface hit']
            aoi_data['category'] = aoi_data['event data']
            
            spl_speech = SubjectData(speech_data, rec['id'])
            spl_speech.max_timestamp = max_timestamp
            spl_speech.min_timestamp = min_timestamp
            speech_lines.append(spl_speech)

            spl_aoi = SubjectData(aoi_data, rec['id'])
            spl_aoi.max_timestamp = max_timestamp
            spl_aoi.min_timestamp = min_timestamp
            aoi_lines.append(spl_aoi)

        return cls(speech_lines, aoi_lines)


    @pyqtSlot(float, float, result=SubjectMultimodalData)
    def slice(self, start_ts, end_ts):
        slices_speech = [s.slice(start_ts, end_ts) for s in self.speech_lines]
        slices_aoi = [s.slice(start_ts, end_ts) for s in self.aoi_lines]
        return SubjectMultimodalData(slices_speech, slices_aoi, self)


    @pyqtSlot(result='QVariantMap')
    def SpeakerTimeTotal(self):
        role_dur = {}

        for s in self.speech_lines:
            for _, row in s.table.iterrows():
                duration = row['end timestamp [sec]'] - row['start timestamp [sec]']
                role_dur[s.sid] = role_dur.get(s.sid, 0) + duration

        return {k: float(v) for k, v in role_dur.items()}

    @pyqtSlot(result='QVariantMap')
    def SpeakerTimeDistribution(self):
        role_dur = {}

        for s in self.speech_lines:
            for _, row in s.table.iterrows():
                duration = row['end timestamp [sec]'] - row['start timestamp [sec]']
                role_dur[s.sid] = role_dur.get(s.sid, 0) + duration

        total_dur = self.MaxTimestamp() - self.MinTimestamp()
        return {k: float(v / total_dur) for k, v in role_dur.items()}

    @pyqtSlot(result='QVariantMap')
    def SpeakerRoleTimeDistribution(self):
        role_dur = {}

        for s in self.speech_lines:
            #durations = s.table['end timestamp [sec]'] - s.table['start timestamp [sec]']
            #role_dur[s.role] = role_dur.get(s.role, 0) + durations.sum()
            
            for _, row in s.table.iterrows():
                duration = row['end timestamp [sec]'] - row['start timestamp [sec]']
                role_dur[row['category']] = role_dur.get(row['category'], 0) + duration

        total_dur = self.MaxTimestamp() - self.MinTimestamp()
        return {k: float(v / total_dur) for k, v in role_dur.items()}
        #return {k: float(v.item() / total_dur) for k, v in role_dur.items()}

    def toString(self):
        snippets = []
        for sl in self.speech_lines:
            sn = sl.table['event data'].tolist()
            snippets.extend(sn)
        return ' '.join(snippets)


    @pyqtSlot(result=list)
    def FullDialogue(self):
        merged_table = []

        for sl in self.speech_lines:
            table = sl.table.copy()
            table['source'] = sl.sid
            if not table.empty:
                merged_table.append(table)

        if len(merged_table) == 0:
            return [{'text': '', 'src': ''}]

        merged_table = pd.concat(merged_table)
        merged_table = merged_table.sort_values(by='start timestamp [sec]')
        
        sources = merged_table['source'].tolist()
        snippets = merged_table['event data'].tolist()

        out = [{'text': snip, 'src': src} for src, snip in zip(sources, snippets)]
        return out

        
    @pyqtSlot(result=float)
    def MaxTimestamp(self):
        return self.speech_lines[0].max_timestamp

    @pyqtSlot(result=float)
    def MinTimestamp(self):
        return self.speech_lines[0].min_timestamp

    @pyqtSlot(int, result=SubjectData)
    def SpeechLine(self, index):
        return self.speech_lines[index]

    @pyqtSlot(int, result=SubjectData)
    def AoiLine(self, index):
        return self.aoi_lines[index]

    @pyqtSlot(result=int)
    def SpeechLineCount(self):
        return len(self.speech_lines)


class SubjectData(QObject):
    def __init__(self, table, sid, parent=None):
        super().__init__(parent)
        self.table = table
        self.sid = sid
        self.start_ts = table['start timestamp [sec]'].tolist()
        self.end_ts = table['end timestamp [sec]'].tolist()
        self.event_data = table['event data'].tolist()
        self.category = table['category'].tolist()
        self.max_timestamp = 0
        self.min_timestamp = 0
        

    @pyqtSlot(float, float, result=SubjectData)
    def slice(self, start_ts, end_ts):
        mask = (self.table['start timestamp [sec]'] >= start_ts) & (self.table['end timestamp [sec]'] < end_ts)

        speech_data = merge_speech(self.table[mask], time_delta_threshold=1.0)
        tm = SubjectData(speech_data, self.sid, parent=self)

        tm.min_timestamp = start_ts
        tm.max_timestamp = end_ts
        return tm
        
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
