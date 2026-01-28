from CustomVideoOutput import CustomVideoOutput

from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication

import argparse
import logging
import sys

from ProjectManager import ProjectManager
logger = logging.getLogger(__name__)


"""
class WorkerThread(threading.Thread):
    def __init__(self, result_queue, model : SegmentModel, daemon=False) -> None:
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
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    app = QApplication(sys.argv)
    qmlRegisterType(CustomVideoOutput, 'com.kochme.media', 1, 0, 'CustomVideoOutput')
    engine = QQmlApplicationEngine()

    qf = QSurfaceFormat()
    QSurfaceFormat.setDefaultFormat(qf)
    logging.basicConfig(level=logging.DEBUG)

    pro_manager = ProjectManager(engine, app, qf)

    pro_manager.parse_projects()
    pro_manager.open_manager()

    sys.exit(app.exec())
