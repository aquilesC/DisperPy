import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

from dispertech.view import VIEW_BASE_DIR


class FocusingWindow(QMainWindow):
    def __init__(self, arduino=None):
        super(FocusingWindow, self).__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Focusing_Window.ui'), self)
        self.arduino = arduino
        self.fiber_led = 0

        self.button_right.clicked.connect(self.move_right)
        self.button_left.clicked.connect(self.move_left)
        self.button_up.clicked.connect(self.move_up)
        self.button_down.clicked.connect(self.move_down)

        self.button_fiber_led.clicked.connect(self.toggle_fiber_led)

        self.power_slider.valueChanged.connect(self.change_power)

    def move_right(self):
        speed = int(self.speed_slider.value())
        self.arduino.move_mirror(speed, 1, 2)

    def move_left(self):
        speed = int(self.speed_slider.value())
        self.arduino.move_mirror(speed, 0, 2)

    def move_up(self):
        speed = int(self.speed_slider.value())
        self.arduino.move_mirror(speed, 1, 1)

    def move_down(self):
        speed = int(self.speed_slider.value())
        self.arduino.move_mirror(speed, 0, 1)

    def change_power(self):
        power = int(self.power_slider.value())
        self.arduino.laser_power(power)

    def toggle_fiber_led(self):
        self.fiber_led = 0 if self.fiber_led else 1
        self.arduino.fiber_led = self.fiber_led

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = FocusingWindow()
    win.show()
    app.exec()
