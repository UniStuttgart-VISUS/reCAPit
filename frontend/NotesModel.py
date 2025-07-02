import pandas as pd
from PyQt6.QtCore import QObject, pyqtSlot

class NotesModel(QObject):
    pass

class NotesModel(QObject):
    def __init__(self, diffs, parent=None):
        super().__init__(parent)

        self.diffs = diffs.copy(deep=True)
        self.init_notes()

    @classmethod
    def empty(cls):
        df = pd.DataFrame(data=[], columns=['start timestamp [sec]', 'end timestamp [sec]', 'center timestamp [sec]', 'insertions', 'deletions', 'label', 'source', 'html'])
        return cls(df)

    def init_notes(self):

        self.start_ts = self.diffs['start timestamp [sec]'].tolist()
        self.end_ts = self.diffs['end timestamp [sec]'].tolist()

        self.insertions = self.diffs['insertions'].tolist()
        self.deletions = self.diffs['deletions'].tolist()
        self.labels = self.diffs['label'].tolist()
        self.sources = self.diffs['source'].tolist()

        self.html = self.diffs['html'].tolist()
        self.has_deletions = self.diffs['html'].apply(lambda x: '<del' in x).tolist()
        self.has_insertions = self.diffs['html'].apply(lambda x: '<ins' in x).tolist()


    @pyqtSlot(float, float, result=NotesModel)
    def slice(self, start_ts, end_ts):
        mask = (self.diffs['center timestamp [sec]'] >= start_ts) & (self.diffs['center timestamp [sec]'] <= end_ts)
        return NotesModel(self.diffs[mask], parent=self)

    @pyqtSlot(int, result=float)
    def PosStartSec(self, index):
        return self.start_ts[index]

    @pyqtSlot(int, result=float)
    def PosEndSec(self, index):
        return self.end_ts[index]

    @pyqtSlot(int, result=bool)
    def HasInsertions(self, index):
        return self.has_insertions[index]

    @pyqtSlot(int, result=bool)
    def HasDeletions(self, index):
        return self.has_deletions[index]

    @pyqtSlot(int, result=str)
    def HTML(self, index):
        return self.html[index]

    @pyqtSlot(result=str)
    def allHTML(self):
        return '\n'.join(self.html)

    @pyqtSlot(int, result=str)
    def Label(self, index):
        return self.labels[index]

    @pyqtSlot(int, result=bool)
    def IsOfflineNote(self, index):
        return self.sources[index] == 'offline'

    @pyqtSlot(result=str)
    def FullInsertions(self):
        return ';'.join([x for x in self.insertions if type(x) == str])

    @pyqtSlot(result=str)
    def FullDeletions(self):
        return ';'.join([x for x in self.deletions if type(x) == str])

    @pyqtSlot(float)
    def AddNote(self, ts, text, label):
        new_entry = pd.DataFrame({'center timestamp [sec]': [ts], 
                                  'start timestamp [sec]': [ts], 
                                  'end timestamp [sec]': [ts], 
                                  'insertions': [text], 
                                  'source': ['offline'],
                                  'label': [label],
                                  'insertions positions': [[]],
                                  'deletions': [""], 
                                  'deletions positions': [[]],
                                  'html': [f'<ins style="background:#e6ffe6;">{text}</ins><span>']})

        self.diffs = pd.concat([self.diffs, new_entry], ignore_index=True)
        self.init_notes()


    @pyqtSlot(int, result=str)
    def Insertions(self, index):
        insertions = self.insertions[index]
        return ';'.join(insertions)

    @pyqtSlot(int, result=str)
    def Deletions(self, index):
        deletions = self.deletions[index]
        return ';'.join(deletions)

    @pyqtSlot(result=int)
    def rowCount(self):
        return len(self.start_ts)


