import os
import sys

from PyQt5 import uic, QtGui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QShortcut

from dispertech.view import VIEW_BASE_DIR

import dispertech.view.GUI.resources
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget


class LaserFocusingWindow(QMainWindow):
    def __init__(self, experiment=None):
        super(LaserFocusingWindow, self).__init__()
        self.experiment = experiment
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Fiber_End_Window.ui'), self)

        layout = self.camera_widget.layout()
        self.camera_fiber = CameraViewerWidget()
        layout.addWidget(self.camera_fiber)

        # Setting status of fiber LED
        self.fiber_led = 0
        self.toggle_fiber_led()

        # Setting the speed
        self.fine_speed = 1
        self.coarse_speed = 50
        self.set_fine_movement()
        self.set_camera_low()

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

        self.power_slider.valueChanged.connect(self.change_power)

        self.button_camera_low.clicked.connect(self.set_camera_low)
        self.button_camera_high.clicked.connect(self.set_camera_high)

        self.button_fiber_led.clicked.connect(self.toggle_fiber_led)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(10)

    def set_fine_movement(self):
        self.speed = self.fine_speed
        self.button_fine_movement.setStyleSheet("background-color: green")
        self.button_coarse_movement.setStyleSheet("background-color: red")

    def set_coarse_movement(self):
        self.speed = self.coarse_speed
        self.button_fine_movement.setStyleSheet("background-color: red")
        self.button_coarse_movement.setStyleSheet("background-color: green")

    def move_up(self):
        self.experiment.electronics.move_mirror(self.speed, 1, 1)

    def move_down(self):
        self.experiment.electronics.move_mirror(self.speed, 0, 1)

    def move_right(self):
        self.experiment.electronics.move_mirror(self.speed, 1, 2)

    def move_left(self):
        self.experiment.electronics.move_mirror(self.speed, 0, 2)

    def change_power(self, power):
        power = int(power)
        self.lcd_laser_power.display(power)
        self.experiment.electronics.laser_power(power)

    def set_camera_low(self):
        self.button_camera_low.setStyleSheet("background-color: green")
        self.button_camera_high.setStyleSheet("background-color: red")
        self.experiment.camera_low_sensitivity()

    def set_camera_high(self, *args):
        self.button_camera_low.setStyleSheet("background-color: red")
        self.button_camera_high.setStyleSheet("background-color: green")
        self.experiment.camera_high_sensitivity()

    def update_image(self):
        image = self.experiment.cameras[0].temp_image
        if not image is None:
            self.camera_fiber.update_image(image)

    def toggle_fiber_led(self):
        self.fiber_led = 0 if self.fiber_led else 1
        self.experiment.electronics.fiber_led = self.fiber_led
        if self.fiber_led:
            self.button_fiber_led.setStyleSheet("background-color: green")
        else:
            self.button_fiber_led.setStyleSheet("background-color: red")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.experiment.cameras[0].stop_free_run()
        super().closeEvent(a0)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = LaserFocusingWindow()
    win.show()
    sys.exit(app.exec())
