from experimentor.models.cameras.basler import BaslerCamera
from experimentor.models.experiments import Experiment


class CameraTest(Experiment):
    def __init__(self, config_file = None):
        super().__init__(config_file)
        self.last_fiber_image = None
        self.last_microscope_image = None

    def initialize(self):
        self.camera_microscope = BaslerCamera(self.config['camera_microscope']['init'])
        self.camera_fiber = BaslerCamera(self.config['camera_fiber']['init'])

        self.camera_microscope.initialize()
        self.camera_fiber.initialize()

    def start_free_run(self):
        self.camera_fiber.set_acquisition_mode(self.camera_fiber.MODE_CONTINUOUS)
        self.camera_microscope.set_acquisition_mode(self.camera_microscope.MODE_CONTINUOUS)
        self.camera_microscope.trigger_camera()
        self.camera_fiber.trigger_camera()

    def update_cameras(self):
        last_frame = self.camera_fiber.read_camera()
        if last_frame is not None: self.last_fiber_image = last_frame[-1]
        last_frame = self.camera_microscope.read_camera()
        if last_frame is not None: self.last_microscope_image = last_frame[-1]

