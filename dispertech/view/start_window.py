import os

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

from dispertech.view import VIEW_BASE_DIR
from dispertech.view.focusing_window import FocusingWindow
from dispertech.view.main_window import MainWindow
from dispertech.view.welcome_window import WelcomeWindow


class StartWindow(QMainWindow):
    def __init__(self, experiment):
        super().__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Start_Window.ui'), self)
        self.experiment = experiment
        self.welcome = None
        self.focusing = None
        self.main_window = None
        self.button_new_sample.clicked.connect(self.show_welcome)
        self.button_align.clicked.connect(self.show_focusing)
        self.button_measure.clicked.connect(self.show_main_window)

    def show_welcome(self):
        self.welcome = WelcomeWindow(self.experiment)
        self.welcome.show()

    def show_focusing(self):
        self.focusing = FocusingWindow(self.experiment)
        self.focusing.show()

    def show_main_window(self):
        self.main_window = MainWindow(self.experiment)
        self.main_window.show()



if __name__ == "__main__":
    app = QApplication([])
    win = QMainWindow()
