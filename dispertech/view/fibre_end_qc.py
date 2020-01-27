import os

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout

from dispertech.view import VIEW_BASE_DIR
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget


class FiberEndWindow(QMainWindow):
    def __init__(self, experiment=None):
        super(FiberEndWindow, self).__init__(parent=None)
        self.experiment = experiment

        uic.loadUi(os.path.join(VIEW_BASE_DIR, 'GUI', 'fiber_end_qc.ui'), self)

        self.layout = self.centralWidget().layout()
        self.camera_widget = CameraViewerWidget()
        self.layout.addWidget(self.camera_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)

        self.button_acquire.clicked.connect(self.save_image)
        self.button_start.clicked.connect(self.start_free_run)
        self.button_stop.clicked.connect(self.stop_free_run)
        if self.experiment is not None:
            self.line_cartridge.setText(str(self.experiment.config['info']['cartridge_number']))

    def update_image(self):
        self.camera_widget.update_image(self.experiment.camera.temp_image)

    def start_free_run(self):
        self.experiment.start_free_run()
        self.timer.start(100)

    def stop_free_run(self):
        self.timer.stop()
        self.experiment.stop_free_run()

    def save_image(self):
        self.experiment.config['info']['cartridge_number'] = self.line_cartridge.text()
        self.timer.stop()
        self.experiment.save_camera_image()
        self.timer.start(100)


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    win = FiberEndWindow()
    win.show()

    sys.exit(app.exec())

