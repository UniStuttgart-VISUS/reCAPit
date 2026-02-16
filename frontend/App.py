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
    parser.add_argument('--project_name', required=False, type=str)
    parser.add_argument('--action', choices=('manifest', 'viewer', 'manager'), default='manager')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    qmlRegisterType(CustomVideoOutput, 'com.kochme.media', 1, 0, 'CustomVideoOutput')
    engine = QQmlApplicationEngine()

    qf = QSurfaceFormat()
    QSurfaceFormat.setDefaultFormat(qf)
    logging.basicConfig(level=logging.DEBUG)

    pro_manager = ProjectManager(engine, app, qf)
    proj_def = pro_manager.parse_projects()

    if args.action == 'manager':
        pro_manager.open_manager()

    elif args.project_name is not None:
        available_names = [p['name'] for p in proj_def]
        proj_idx = available_names.index(args.project_name)
        if proj_idx == -1:
            logger.error('No project could be loaded with the name: "%s"', args.project_name)
            sys.exit(-1)

        pro_manager.open_project(proj_idx, args.action)

    sys.exit(app.exec())
