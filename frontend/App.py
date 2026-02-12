from CustomVideoOutput import CustomVideoOutput

from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtWidgets import QApplication

import argparse
import logging
import sys

from ProjectManager import ProjectManager
logger = logging.getLogger(__name__)

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
