import os

import numpy as np

import dispertech.view.GUI.resources
from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout

from dispertech.view import VIEW_BASE_DIR
from dispertech.view.focusing_window import FocusingWindow
from dispertech.view.tracking_config_window import TrackingConfig
from experimentor import Q_
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget


class MainWindow(QMainWindow):
    def __init__(self, experiment=None):
        super().__init__()
        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'Main_Window.ui'), self)
        self.focus_window = FocusingWindow(experiment)
        self.config_window = TrackingConfig(experiment.config['tracking'], parent=None)

        self.experiment = experiment
        self.fiber_led = 0
        self.light_led = 0

        self.data_layout = QVBoxLayout()
        self.data_widget.setLayout(self.data_layout)
        self.camera_widget = CameraViewerWidget()
        self.data_layout.addWidget(self.camera_widget)
        self.power_slider.valueChanged.connect(self.change_power)

        self.button_led.clicked.connect(self.toggle_fiber_led)
        self.button_light.clicked.connect(self.toggle_light_led)

        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.update_image)
        self.image_timer.start(30)

        self.temperature_timer = QTimer()
        self.temperature_timer.timeout.connect(self.update_temperatures)
        self.temperature_timer.start(5000)

        self.actionAlign_Tool.triggered.connect(self.focus_window.show)
        self.action_set_roi.triggered.connect(self.set_roi)
        self.action_start_tracking.triggered.connect(self.experiment.start_tracking)
        self.action_tracking_config.triggered.connect(self.config_window.show)

        self.camera_widget.setup_roi_lines([
            self.experiment.cameras[1].max_width,
            self.experiment.cameras[1].max_height
        ])

        self.line_exposure.setText(str(self.experiment.cameras[1].exposure.m_as('ms')))
        self.line_gain.setText(str(self.experiment.cameras[1].gain))
        self.button_camera_apply.clicked.connect(self.update_camera_settings)

    def change_power(self):
        power = int(self.power_slider.value())
        self.lcd_laser_power.display(power)
        self.experiment.electronics.laser_power(power)

    def toggle_fiber_led(self):
        self.fiber_led = 0 if self.fiber_led else 1
        self.experiment.electronics.fiber_led = self.fiber_led
        if self.fiber_led:
            self.button_led.setStyleSheet("background-color: green")
        else:
            self.button_led.setStyleSheet("background-color: red")

    def toggle_light_led(self):
        self.light_led = 0 if self.light_led else 1
        self.experiment.electronics.top_led = self.light_led
        if self.light_led:
            self.button_light.setStyleSheet("background-color: green")
        else:
            self.button_light.setStyleSheet("background-color: red")

    def update_image(self):
        image = self.experiment.cameras[1].temp_image
        if not image is None:
            self.camera_widget.update_image(image)
        if not self.experiment.temp_locations is None:
            self.camera_widget.draw_target_pointer(self.experiment.temp_locations)

    def update_temperatures(self):
        self.sample_temperature.display(self.experiment.electronics.temp_sample)
        self.electronics_temperature.display(self.experiment.electronics.temp_electronics)
        self.lcd_fps.display(self.experiment.cameras[1].fps)

    def set_roi(self):
        X, Y = self.camera_widget.get_roi_values()
        new_values = self.experiment.cameras[1].set_ROI(X, Y)
        self.camera_widget.set_roi_lines(new_values[1], new_values[0])
        self.experiment.cameras[1].start_free_run()

    def update_camera_settings(self):
        exposure = float(self.line_exposure.text()) * Q_('ms')
        self.experiment.cameras[1].stop_free_run()
        new_exposure = self.experiment.cameras[1].set_exposure(exposure)
        gain = float(self.line_gain.text())
        new_gain = self.experiment.cameras[1].set_gain(gain)
        self.line_exposure.setText(str(new_exposure.m_as('ms')))
        self.experiment.cameras[1].start_free_run()

    def toggle_tracking(self):
        self.experiment.config['tracking'] = self.config_window.get_config()
        if self.experiment.tracking:
            self.experiment.stop_tracking()
        else:
            self.experiment.start_tracking()
