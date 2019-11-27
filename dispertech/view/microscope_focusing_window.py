from PyQt5 import QtGui

from dispertech.view.general_focusing_window import GeneralFocusingWindow


class MicroscopeFocusingWindow(GeneralFocusingWindow):
    def __init__(self, experiment=None):
        super(MicroscopeFocusingWindow, self).__init__(experiment)

    def set_camera_low(self):
        self.button_camera_low.setStyleSheet("background-color: green")
        self.button_camera_high.setStyleSheet("background-color: red")
        camera = self.experiment.cameras[1]
        config = self.experiment.config['microscope_focusing']['low']
        camera.configure(config)
        # camera._stop_free_run.set()
        camera.start_free_run()
        self.logger.debug(f"Set microscope-camera to low-sensitivity mode. "
                          f"Exposure: {config['exposure_time']}, Gain: {config['gain']}")

    def set_camera_high(self):
        self.button_camera_low.setStyleSheet("background-color: red")
        self.button_camera_high.setStyleSheet("background-color: green")
        camera = self.experiment.cameras[1]
        config = self.experiment.config['microscope_focusing']['high']
        camera.configure(config)
        # camera._stop_free_run.set()
        camera.start_free_run()
        self.logger.debug(f"Set microscope-camera to high-sensitivity mode. "
                          f"Exposure: {config['exposure_time']}, Gain: {config['gain']}")

    def toggle_led(self):
        self.led = 0 if self.led else 1
        self.experiment.electronics.top_led = self.led
        if self.led:
            self.button_fiber_led.setStyleSheet("background-color: green")
        else:
            self.button_fiber_led.setStyleSheet("background-color: red")

    def update_image(self):
        image = self.experiment.cameras[1].temp_image
        if not image is None:
            self.camera_widget.update_image(image)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.experiment.cameras[1].stop_free_run()
        super().closeEvent(a0)
