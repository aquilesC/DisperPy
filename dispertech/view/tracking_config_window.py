import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

from dispertech.view import VIEW_BASE_DIR


class TrackingConfig(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Tracking_Config.ui'), self)
        self.config = config
        self.set_config(config)

    def set_config(self, config):
        self.locate_diameter.setText(str(config['locate']['diameter']))
        self.locate_invert.setCurrentIndex(0) if config['locate']['invert'] else self.locate_invert.setCurrentIndex(1)
