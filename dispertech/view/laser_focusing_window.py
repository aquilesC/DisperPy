import os
import sys

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QShortcut

from dispertech.view import VIEW_BASE_DIR

import dispertech.view.GUI.resources
from experimentor.views.decorators import try_except_dialog


class LaserFocusingWindow(QMainWindow):
    def __init__(self, experiment=None):
        super(LaserFocusingWindow, self).__init__()
        self.experiment = experiment
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Fiber_End_Window.ui'), self)

        # Setting the speed
        self.fine_speed = 1
        self.coarse_speed = 50
        self.set_fine_movement()



        # Connecting the buttons and actions
        self.button_fine_movement.clicked.connect(self.set_fine_movement)
        self.button_coarse_movement.clicked.connect(self.set_coarse_movement)

        self.button_up.clicked.connect(self.move_up)
        QShortcut(Qt.Key_Up, self, self.move_up)

        self.button_down.clicked.connect(self.move_down)
        QShortcut(Qt.Key_Down, self, self.move_down)

        self.button_left.clicked.connect(self.move_left)
        QShortcut(Qt.Key_Left, self, self.move_left)

        self.button_right.clicked.connect(self.move_right)
        QShortcut(Qt.Key_Right, self, self.move_right)

    def set_fine_movement(self):
        self.speed = self.fine_speed
        self.button_fine_movement.setStyleSheet("background-color: green")
        self.button_coarse_movement.setStyleSheet("background-color: red")

    def set_coarse_movement(self):
        self.speed = self.coarse_speed
        self.button_fine_movement.setStyleSheet("background-color: red")
        self.button_coarse_movement.setStyleSheet("background-color: green")

    @try_except_dialog
    def move_up(self):
        self.experiment.electronics.move_mirror(self.speed, 1, 1)

    @try_except_dialog
    def move_down(self):
        self.experiment.electronics.move_mirror(self.speed, 0, 1)

    @try_except_dialog
    def move_right(self):
        self.experiment.electronics.move_mirror(self.speed, 1, 2)

    @try_except_dialog
    def move_left(self):
        self.experiment.electronics.move_mirror(self.speed, 0, 2)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = LaserFocusingWindow()
    win.show()
    sys.exit(app.exec())
