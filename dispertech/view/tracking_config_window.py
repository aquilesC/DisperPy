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
        self.button_reset.clicked.connect(self.set_config)
        self.button_apply.clicked.connect(self.get_config)

    def set_config(self, config=None):
        if not config:
            config = self.config
        self.locate_diameter.setText(str(config['locate']['diameter']))
        self.locate_invert.setCurrentIndex(0) if config['locate']['invert'] else self.locate_invert.setCurrentIndex(1)
        self.locate_minmass.setText(str(config['locate']['minmass']))
        self.link_memory.setText(str(config['link']['memory']))
        self.link_search_range.setText(str(config['link']['search_range']))
        self.filter_min_length.setText(str(config['filter']['min_length']))
        self.process_compute_drift.setCurrentIndex(0) if config['process']['compute_drift'] else self.process_compute_drift.setCurrentIndex(1)
        self.process_um_pixel.setText(str(config['process']['um_pixel']))
        self.process_min_traj_length.setText(str(config['process']['min_traj_length']))
        self.process_min_mass.setText(str(config['process']['min_mass']))
        self.process_max_size.setText(str(config['process']['max_size']))
        self.process_max_ecc.setText(str(config['process']['max_ecc']))
        self.process_fps.setText(str(config['process']['fps']))

    def get_config(self):
        self.config['locate']['diameter'] = int(self.locate_diameter.text())
        self.config['locate']['invert'] = False if self.locate_invert.currentIndex() == 1 else True
        self.config['locate']['minmass'] = int(self.locate_minmass.text())
        self.config['link']['memory'] = int(self.link_memory.text())
        self.config['link']['search_range'] = int(self.link_search_range.text())
        self.config['filter']['min_length'] = int(self.filter_min_length.text())
        self.config['process']['compute_drift'] = False if self.process_compute_drift.currentIndex() == 1 else True
        self.config['process']['um_pixel'] = float(self.process_um_pixel.text())
        self.config['process']['min_traj_length'] = int(self.process_min_traj_length.text())
        self.config['process']['min_mass'] = float(self.process_min_mass.text())
        self.config['process']['max_size'] = float(self.process_max_size.text())
        self.config['process']['max_ecc'] = float(self.process_max_ecc.text())
        self.config['process']['fps'] = float(self.process_fps.text())
        return self.config

