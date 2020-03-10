import os

import numpy as np

from dispertech.models.cameras.basler import Camera
from dispertech.models.electronics.arduino import ArduinoModel
from dispertech.models.gaussian_fit import fitgaussian
from experimentor.models.decorators import make_async_thread
from experimentor.models.experiments.base_experiment import Experiment, FormatDict


class Dispertech(Experiment):
    def __init__(self, config_file=None):
        super().__init__(filename=config_file)
        self.cameras = dict(camera_microscope=None, camera_fiber=None)
        self.electronics = dict(servo=None, main_electronics=None)
        self.initializing = None  # None means has not been initialized, True means is happening, False means it's done

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
            cam.set_pixel_format('Mono12')

    def initialize_electronics(self):
        """Initializes the electronics, assuming there are two arduinos connected one for the servo and one for the
        rest."""
        self.electronics['servo'] = ArduinoModel(**self.config['servo'])
        self.electronics['main_electronics'] = ArduinoModel(**self.config['electronics'])

        for electronics in self.electronics.values():
            electronics.initialize()

    @make_async_thread
    def initialize(self):
        self.initializing = True
        self.initialize_electronics()
        self.initialize_cameras()

        self.initializing = False

    @make_async_thread
    def start_fiber_focus(self):
        """Starts a free run of the camera that looks at the fiber end in order to focus the core. This requires to
        switch on the LED and off the Laser. """
        self.cameras['camera_microscope'].stop_camera()
        self.electronics['main_electronics'].fiber_led = 1
        self.electronics['main_electronics'].top_led = 0
        self.electronics['main_electronics'].laser_power = 0
        self.electronics['servo'].move_servo(0)
        self.config['camera_fiber'].update(self.config['laser_focusing'])
        self.cameras['camera_fiber'].stop_camera()
        self.cameras['camera_fiber'].configure(self.config['camera_fiber'])
        self.cameras['camera_fiber'].start_free_run()

    def done_fiber_focus(self, X: float, Y:float):
        """ When the focusing is done, the user must click close to the fiber core in order to record it's position.
        This, in turn, will trigger the focusing of the laser on the fiber end. The position of the center clicked by
        the user must be passed as floats to this method, which will then find the closest maximum in intensity.

        .. NOTE:: The use of float is because most mouse interactions with an image give fractional values for pixel
            positions.
        """

        last_image = np.copy(self.cameras['camera_fiber'].temp_image)
        cartridge = self.config['sample']['cartridge']
        #  The following extends is built on this: https://ideone.com/xykV7R to preserve the formatting of anything
        #  else but the cartridge parameter (in this case it would be the {i})
        filename = self.config['core_options']['fiber_end_image_name'].format_map(FormatDict(cartridge=cartridge))

        folder, filename = self.make_filename(self.config['core_options']['data_folder'], filename)
        self.logger.info(f'Saving fiber end data to {os.path.join(folder, filename)}')
        np.save(os.path.join(folder, filename), last_image)

        # Crop a small square around the coordinates supplied
        cropped_image = np.copy(last_image[X-15:X+15, Y-15:Y+15])
        cropped_image[cropped_image<np.mean(cropped_image)+np.std(cropped_image)] = 0
        params = fitgaussian(cropped_image)




