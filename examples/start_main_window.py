import logging

from PyQt5.QtWidgets import QApplication

from dispertech.models.experiment.nanoparticle_tracking.np_tracking import NPTracking
from dispertech.view.main_window import MainWindow
from experimentor.lib.log import log_to_screen, get_logger


logger = get_logger(level=logging.DEBUG)
handler = log_to_screen(level=logging.DEBUG)
experiment = NPTracking('dispertech.yml')
experiment.load_cameras()
experiment.load_electronics()
experiment.electronics.monitor_temperature()
app = QApplication([])
fw = MainWindow(experiment=experiment)
fw.show()
app.exec()
experiment.finalize()
