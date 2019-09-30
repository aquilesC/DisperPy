import logging

from PyQt5.QtWidgets import QApplication

from dispertech.models.experiment.nanoparticle_tracking.np_tracking import NPTracking
from dispertech.view.main_window import MainWindow
from experimentor.lib.log import log_to_screen, get_logger


logger = get_logger(level=logging.DEBUG)
handler = log_to_screen()
experiment = NPTracking('dispertech.yml')
experiment.load_cameras()
experiment.load_electronics()
experiment.start_free_run(0)
experiment.start_free_run(1)
experiment.electronics.monitor_temperature()
app = QApplication([])
fw = MainWindow(experiment=experiment)
fw.show()
app.exec()
print('App Closed')
experiment.finalize()
