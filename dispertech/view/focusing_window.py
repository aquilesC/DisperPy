import os
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow


from experimentor import Q_
from dispertech.view import VIEW_BASE_DIR


class FocusingWindow(QMainWindow):
    def __init__(self, experiment=None):
        super(FocusingWindow, self).__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Focusing_Window.ui'), self)
        self.experiment = experiment
        self.fiber_led = 0
        self.top_led = 0

        self.button_right.clicked.connect(self.move_right)
        self.button_left.clicked.connect(self.move_left)
        self.button_up.clicked.connect(self.move_up)
        self.button_down.clicked.connect(self.move_down)

        self.button_fiber_led.clicked.connect(self.toggle_fiber_led)
        self.button_top_led.clicked.connect(self.toggle_top_led)

        self.power_slider.valueChanged.connect(self.change_power)

        # self.viewport = GraphicsLayoutWidget()
        # self.view = self.viewport.addViewBox(lockAspect=False, enableMenu=True)
        self.img = pg.ImageItem()
        # self.view.addItem(self.img)
        self.imv = pg.ImageView(imageItem=self.img)
        self.img2 = pg.ImageItem()
        self.imv2 = pg.ImageView(imageItem=self.img2)
        layout = self.camera_widget.layout()
        layout.addWidget(self.imv)
        layout.addWidget(self.imv2)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

        self.button_apply.clicked.connect(self.apply_settings)
        self.button_start.clicked.connect(self.start_free_run)
        self.button_stop.clicked.connect(self.stop_free_run)

    def update_image(self):
        image = self.experiment.cameras[0].temp_image
        image2 = self.experiment.cameras[1].temp_image
        if not image2 is None and not image is None:
            self.img.setImage(image.astype(int), autoLevels=False, autoRange=False, autoHistogramRange=True)
            self.img2.setImage(image2.astype(int), autoLevels=False, autoRange=False, autoHistogramRange=True)

    def move_right(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_mirror(speed, 1, 2)

    def move_left(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_mirror(speed, 0, 2)

    def move_up(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_mirror(speed, 1, 1)

    def move_down(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_mirror(speed, 0, 1)

    def change_power(self):
        power = int(self.power_slider.value())
        self.experiment.electronics.laser_power(power)

    def toggle_fiber_led(self):
        self.fiber_led = 0 if self.fiber_led else 1
        self.experiment.electronics.fiber_led = self.fiber_led
        if self.fiber_led:
            self.button_fiber_led.setStyleSheet("background-color: green")
        else:
            self.button_fiber_led.setStyleSheet("background-color: red")

    def toggle_top_led(self):
        self.top_led = 0 if self.top_led else 1
        self.experiment.electronics.top_led = self.top_led
        if self.top_led:
            self.button_top_led.setStyleSheet("background-color: green")
        else:
            self.button_top_led.setStyleSheet("background-color: red")

    def start_free_run(self):
        self.experiment.cameras[0].start_free_run()
        self.experiment.cameras[1].start_free_run()

    def stop_free_run(self):
        self.experiment.cameras[0].stop_free_run()
        self.experiment.cameras[1].stop_free_run()

    def apply_settings(self):
        exposure_0 = float(self.line_fiber_exposure.text()) * Q_('ms')
        exposure_1 = float(self.line_microscope_exposure.text()) * Q_('ms')
        self.stop_free_run()
        exposure_0 = self.experiment.cameras[0].set_exposure(exposure_0)
        exposure_1 = self.experiment.cameras[1].set_exposure(exposure_1)
        self.experiment.cameras[0].start_free_run()
        self.experiment.cameras[1].start_free_run()
        self.line_fiber_exposure.setText(str(exposure_0.m_as('ms')))
        self.line_microscope_exposure.setText(str(exposure_1.m_as('ms')))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = FocusingWindow()
    win.show()
    app.exec()
