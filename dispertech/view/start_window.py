import os

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

from dispertech.view import VIEW_BASE_DIR
from dispertech.view.focusing_window import FocusingWindow
from dispertech.view.laser_focusing_window import LaserFocusingWindow
from dispertech.view.main_window import MainWindow
from dispertech.view.microscope_focusing_window import MicroscopeFocusingWindow
from dispertech.view.welcome_window import WelcomeWindow


class StartWindow(QMainWindow):
    def __init__(self, experiment):
        super().__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Start_Window.ui'), self)
        self.experiment = experiment
        self.welcome = None
        self.focusing = None
        self.main_window = None
        self.focus_fiber = None
        self.button_new_sample.clicked.connect(self.show_welcome)
        self.button_align.clicked.connect(self.show_focusing)
        self.button_focus_fiber.clicked.connect(self.show_focus_fiber)
        self.button_measure.clicked.connect(self.show_main_window)

    def show_welcome(self):
        self.welcome = WelcomeWindow(self.experiment)
        self.welcome.show()

    def show_focusing(self):
        self.focusing = LaserFocusingWindow(self.experiment)
        self.focusing.show()
        self.focusing.showMaximized()

    def show_focus_fiber(self):
        self.focus_fiber = MicroscopeFocusingWindow(self.experiment)
        self.focus_fiber.show()
        self.focus_fiber.showMaximized()

    def show_main_window(self):
        self.main_window = MainWindow(self.experiment)
        self.main_window.show()
        self.main_window.showMaximized()


if __name__ == "__main__":
    app = QApplication([])
    win = QMainWindow()
