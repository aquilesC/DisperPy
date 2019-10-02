import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

from dispertech.view import VIEW_BASE_DIR


class WelcomeWindow(QMainWindow):
    def __init__(self, experiment):
        super().__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Welcome_Window.ui'), self)
        self.experiment = experiment
        sample = experiment.config['sample']
        self.line_sample_name.setText(sample['name'])
        self.line_sample_description.setText(sample['description'])
        self.line_cartridge_number.setText(sample['cartrdige_number'])
        self.line_data_directory.setText(experiment.config['saving']['directory'])

        self.button_continue.clicked.connect(self.next)

    def next(self):
        sample_data = {
            'name': self.line_sample_name.text(),
            'description': self.line_sample_description.text(),
            'cartrdige_number': self.line_data_directory.text(),
        }
        self.experiment.config['sample'].update(sample_data)
        directory = self.line_data_directory.text()
        self.experiment.config['saving']['directory'] = directory

        self.close()
