import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QWidget

from dispertech.view import VIEW_BASE_DIR
from experimentor.views.widgets import ToggableButton


class ElectronicsWindow(QMainWindow):
    def __init__(self, experiment=None):
        super(ElectronicsWindow, self).__init__()
        self.experiment = experiment
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Electronics_Window.ui'), self)


if __name__ == '__main__':
    app = QApplication([])
    win = ElectronicsWindow()
    win.show()
    app.exec()
