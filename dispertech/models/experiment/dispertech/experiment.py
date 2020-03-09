from dispertech.models.cameras.basler import Camera
from dispertech.models.electronics.arduino import ArduinoModel
from experimentor.models.decorators import make_async_thread
from experimentor.models.experiments.base_experiment import Experiment


class Dispertech(Experiment):
    def __init__(self, config_file=None):
        super().__init__(filename=config_file)
        self.cameras = dict(camera_microscope=None, camera_fiber=None)
        self.electronics = dict(servo=None, main_electronics=None)

    def initialize_cameras(self):
        """Initializes the cameras, it assumes we are using Basler cameras for both the fiber end and the microscope.
        It also sets some sensible parameters for the purposes of the experiment at hand, for example it disables auto
        exposure and auto gain.
        """
        self.cameras['camera_microscope'] = Camera(self.config['camera_microscope']['init'])
        self.cameras['camera_fiber'] = Camera(self.config['camera_fiber']['init'])

        for cam in self.cameras.values():
            cam.initialize()
            cam.set_auto_exposure('Off')
            cam.set_auto_gain('Off')
            cam.clear_ROI()

    def initialize_electronics(self):
        self.electronics['servo'] = ArduinoModel(**self.config['servo'])
        self.electronics['main_electronics'] = ArduinoModel(**self.config['electronics'])

        for electronics in self.electronics.values():
            electronics.initialize()

    @make_async_thread
    def initialize(self):
        self.initialize_electronics()
        self.initialize_cameras()

