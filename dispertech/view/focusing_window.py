import numpy as np
import os
import pyqtgraph as pg

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout

from experimentor import Q_
from dispertech.view import VIEW_BASE_DIR
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget


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

        # self.img = pg.ImageItem()
        # self.imv = pg.ImageView(imageItem=self.img)
        # self.img2 = pg.ImageItem()
        # self.imv2 = pg.ImageView(imageItem=self.img2)
        layout = self.camera_widget.layout()
        self.camera_microscope = CameraViewerWidget()
        self.camera_microscope.setup_cross_cut((self.experiment.cameras[1].max_height))
        self.camera_microscope.setup_mouse_tracking()
        self.camera_fiber = CameraViewerWidget()
        layout.addWidget(self.camera_microscope)
        layout.addWidget(self.camera_fiber)

        plots_layout = QHBoxLayout()
        intensity_plot_widget = pg.PlotWidget()
        self.intensity_plot = intensity_plot_widget.getPlotItem().plot([0,], [0,])
        intensity_history_widget = pg.PlotWidget()
        self.intensity_history_plot = intensity_history_widget.getPlotItem().plot([0,], [0,])
        plots_layout.addWidget(intensity_plot_widget)
        plots_layout.addWidget(intensity_history_widget)
        self.plots_widget.setLayout(plots_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(10)

        self.button_apply.clicked.connect(self.apply_settings)
        self.button_start.clicked.connect(self.start_free_run)
        self.button_stop.clicked.connect(self.stop_free_run)

        self.line_microscope_exposure.setText(f"{self.experiment.cameras[1].exposure.m_as('ms'):02.2f}")
        self.line_fiber_exposure.setText(f"{self.experiment.cameras[0].exposure.m_as('ms'):02.2f}")
        self.line_microscope_gain.setText(f"{self.experiment.cameras[1].gain:02.2f}")
        self.line_fiber_gain.setText(f"{self.experiment.cameras[0].gain:02.2f}")

        self.button_fiber_auto.clicked.connect(self.auto_fiber)
        self.button_microscope_auto.clicked.connect(self.auto_microscope)

        self.intensities = np.zeros(100)

    def auto_fiber(self):
        self.experiment.cameras[0].stop_free_run()
        self.experiment.cameras[0].auto_exposure()
        self.experiment.cameras[0].auto_gain()
        self.line_fiber_exposure.setText(f"{self.experiment.cameras[0].exposure.m_as('ms'):02.2f}")
        self.line_fiber_gain.setText(f"{self.experiment.cameras[0].gain:02.2f}")
        self.experiment.cameras[0].start_free_run()

    def auto_microscope(self):
        self.experiment.cameras[1].stop_free_run()
        self.experiment.cameras[1].auto_exposure()
        self.experiment.cameras[1].auto_gain()
        self.line_microscope_exposure.setText(f"{self.experiment.cameras[1].exposure.m_as('ms'):02.2f}")
        self.line_microscope_gain.setText(f"{self.experiment.cameras[1].gain:02.2f}")
        self.experiment.cameras[1].start_free_run()

    def update_image(self):
        image = self.experiment.cameras[0].temp_image
        if not image is None:
            self.camera_fiber.update_image(image)

        image2 = self.experiment.cameras[1].temp_image
        if not image2 is None:
            self.camera_microscope.update_image(image2)
            if self.camera_microscope.showCrossCut:
                cross_cut = self.camera_microscope.crossCut.value()
                self.intensity_plot.setData(image2[:,cross_cut])
                intensity = np.sum(image2[:, cross_cut-5:cross_cut+5])
                self.intensities = np.roll(self.intensities, -1)
                self.intensities[1] = intensity
                self.intensity_history_plot.setData(self.intensities)

    def move_right(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_piezo(speed, 1, 2)

    def move_left(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_piezo(speed, 0, 2)

    def move_up(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_piezo(speed, 1, 1)

    def move_down(self):
        speed = int(self.speed_slider.value())
        self.experiment.electronics.move_piezo(speed, 0, 1)

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
        self.experiment.cameras[0].clear_ROI()
        self.experiment.cameras[1].clear_ROI()
        self.experiment.cameras[0].start_free_run()
        self.experiment.cameras[1].start_free_run()

    def stop_free_run(self):
        self.experiment.cameras[0].stop_free_run()
        self.experiment.cameras[1].stop_free_run()

    def apply_settings(self):
        exposure_0 = float(self.line_fiber_exposure.text()) * Q_('ms')
        exposure_1 = float(self.line_microscope_exposure.text()) * Q_('ms')
        gain_0 = float(self.line_fiber_gain.text())
        gain_1 = float(self.line_microscope_gain.text())
        self.stop_free_run()
        exposure_0 = self.experiment.cameras[0].set_exposure(exposure_0)
        exposure_1 = self.experiment.cameras[1].set_exposure(exposure_1)
        gain_0 = self.experiment.cameras[0].set_gain(gain_0)
        gain_1 = self.experiment.cameras[1].set_gain(gain_1)
        self.experiment.cameras[0].start_free_run()
        self.experiment.cameras[1].start_free_run()
        self.line_fiber_exposure.setText(f"{exposure_0.m_as('ms'):02.2f}")
        self.line_microscope_exposure.setText(f"{exposure_1.m_as('ms'):02.2f}")
        self.line_fiber_gain.setText(f"{gain_0:02.2f}")
        self.line_microscope_gain.setText(f"{gain_1:02.2f}")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.experiment.cameras[0].stop_free_run()
        self.experiment.cameras[1].stop_free_run()
        super().closeEvent(a0)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    win = FocusingWindow()
    win.show()
    app.exec()
