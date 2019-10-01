from PyQt5.QtWidgets import QApplication

from dispertech.models.experiment.nanoparticle_tracking.np_tracking import NPTracking
from dispertech.view.focusing_window import FocusingWindow
from experimentor.lib.log import log_to_screen, get_logger


logger = get_logger()
handler = log_to_screen()
experiment = NPTracking('dispertech.yml')
experiment.load_cameras()
experiment.load_electronics()
app = QApplication([])
fw = FocusingWindow(experiment=experiment)
fw.show()
app.exec()
