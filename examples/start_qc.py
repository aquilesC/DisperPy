import sys

from PyQt5.QtWidgets import QApplication
from multiprocessing.spawn import freeze_support

import logging
import os
from time import sleep

from dispertech.models.experiment.fiber_end_qc.fiber_end_qc import FiberEndQualityControl
from dispertech.view.fibre_end_qc import FiberEndWindow
from experimentor.lib.log import get_logger, log_to_screen


if __name__ == "__main__":
    freeze_support()

    logger = get_logger(level=logging.DEBUG)
    handler = log_to_screen(level=logging.DEBUG)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    experiment = FiberEndQualityControl(filename=os.path.join(BASE_DIR, 'fiber_end_qc.yml'))
    experiment.initialize()
    app = QApplication([])
    win = FiberEndWindow(experiment)
    win.show()
    sys.exit(app.exec())

