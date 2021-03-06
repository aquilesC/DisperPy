import os
import time

from datetime import datetime
import numpy as np

from dispertech.models.cameras.basler import Camera
from dispertech.models.electronics.arduino import ArduinoModel
from experimentor import Q_
from experimentor.models.cameras.exceptions import CameraTimeout
from experimentor.models.experiments.base_experiment import Experiment


class FiberEndQualityControl(Experiment):
    """Quality control of the fiber-end while glued to the cartridge"""
    def __init__(self, filename=None):
        super().__init__(filename)
        self.camera = None
        self.electronics = None
        self.servo = None

    def initialize(self):
        """General initialization method. Loads the fiber-end camera, the electronics, switches off the laser. But it
        does not start acquiring yet.
        """
        self.logger.info('Initializing Fiber End Quality Control Experiment')
        self.initialize_camera()
        self.initialize_electronics()
        self.servo_off()

    def start_free_run(self):
        """Start the camera in free-run mode. The camera will run on its own thread. The LED to see the fiber end will
        be switched on.
        """
        self.logger.info('Starting free run of the camera')
        self.electronics.fiber_led = 1
        self.camera.configure(self.config['camera'])
        self.camera.start_free_run()
        self.logger.debug(f'Started free run of camera {self.camera}')

    def stop_free_run(self):
        """Stop the camera if it is currently running"""
        self.camera.stop_free_run()
        self.electronics.fiber_led = 0

    def save_camera_image(self):
        """Saves the current image on the camera to a predefined folder, using the cartridge number and the description.
        """
        base_folder = self.config['info']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        folder = os.path.join(base_folder, today_folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        i = 0
        cartridge_number = self.config['info']['cartridge_number']
        base_filename = self.config['info']['filename']
        while os.path.isfile(os.path.join(folder, base_filename.format(cartridge_number=cartridge_number, i=i))):
            i += 1

        filename = os.path.join(folder, base_filename.format(cartridge_number=cartridge_number, i=i))
        # TODO: Python 3.8 allows a new syntax: while filename := os.path....
        #  update the code above

        # The camera stores only one frame of the temp_image. If it is read, then it is also erased. This loop makes it
        #   wait until the image is ready, and raises an exception if it takes "too long"
        t0 = time.time()
        temp_image = self.camera.temp_image
        while temp_image is None:
            temp_image = self.camera.temp_image
            if time.time()-t0 > 10:  # Wait for 10 seconds before timing out
                raise CameraTimeout("It took too long to get a new frame for saving")

        np.save(filename, temp_image)
        self.logger.info(f'Data saved to {filename}')

    def initialize_camera(self):
        """Initializes the camera. We are assuming a very specific setup, in which a Basler Dart is used.
        """
        self.logger.info('Initializing the camera')
        cam_init_arguments = self.config['camera']['init']
        self.camera = Camera(cam_init_arguments)
        self.camera.initialize()
        self.camera.set_pixel_format('Mono12')
        self.camera.set_auto_exposure('Off')
        self.camera.set_auto_gain('Off')
        self.camera.set_gain(self.config['camera']['gain'])
        self.camera.set_exposure(Q_(self.config['camera']['exposure_time']))

    def initialize_electronics(self):
        """Initializes the electronics"""
        self.electronics = ArduinoModel(**self.config['electronics'])
        self.electronics.initialize()

        # This is a temporary fix in order to control the servo from a different Arduino
        self.servo = ArduinoModel(**self.config['servo'])
        self.servo.initialize()

    def servo_off(self):
        """ Move the servo to block the beam. To avoid problems, first put the laser to 0 power.
        This can generate problems later on, since we can lose track of the power (for ex. on the GUI).
        """
        self.electronics.laser_power(0)
        self.servo.move_servo(0)
