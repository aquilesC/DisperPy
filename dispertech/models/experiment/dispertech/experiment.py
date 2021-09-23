"""
    Core Dispertech Experiment. It takes care of all the steps needed to acquire data, but not of the analysis itself.
    There is a separate set of classes to perform data analysis.

"""
import os
from typing import List

import numpy as np


from dispertech.models.electronics.arduino import ArduinoModel
from experimentor.lib import fitgaussian
from experimentor.models.action import Action
from experimentor.models.devices.cameras.basler.basler import BaslerCamera as Camera
from experimentor.models.decorators import make_async_thread
from experimentor.models.experiments.base_experiment import Experiment, FormatDict


class Dispertech(Experiment):
    def __init__(self, config_file=None):
        super().__init__(filename=config_file)

        self.camera_microscope = None
        self.camera_fiber = None
        self.electronics = None
        self.initialized = None  # None means has not been initialized, True means is happening, False means it's done

    @Action
    def initialize(self):
        """ Initialize the cameras and the electronics without starting a continuous acquisition.
        """
        self.initialized = False
        self.initialize_cameras()
        self.initialized = True

    def initialize_cameras(self):
        """Initializes the cameras, it assumes we are using Basler cameras for both the fiber end and the microscope.
        It also sets some sensible parameters for the purposes of the experiment at hand, for example it disables auto
        exposure and auto gain.
        """
        self.logger.info('Initializing cameras')
        config_mic = self.config['camera_microscope']
        self.camera_microscope = Camera(config_mic['init'], initial_config=config_mic['config'])

        config_fiber = self.config['camera_fiber']
        self.camera_fiber = Camera(config_fiber['init'], initial_config=config_fiber['config'])

        for cam in (self.camera_fiber, self.camera_microscope):
            self.logger.info(f'Initializing {cam}')
            cam.initialize()

    def initialize_electronics(self):
        """Initializes the electronics, assuming there are two arduinos connected one for the servo and one for the
        rest."""
        self.logger.info('Initializing electronics')
        self.electronics = ArduinoModel(**self.config['electronics']['arduino'])
        self.electronics.initialize()

    def move_mirror(self, direction, axis, speed=1):
        """ Moves the mirror connected to the electronics

        :param direction: 0 or 1, depending on the direction to move the mirror
        :param axis: 1 or 2, axis means top/down or left/right each is addressed by a different controller
        :param int speed: Speed, from 0 to 2^6. A speed of 0 stops the ongoing movement, a speed of 1 is a single step.
        """
        self.electronics.move_piezo(speed, direction, axis)

    @make_async_thread
    def initialize(self):
        self.initialized = True
        self.initialize_electronics()
        self.initialize_cameras()
        self.initialized = False

    @make_async_thread
    def start_fiber_focus(self):
        """Starts a free run of the camera that looks at the fiber end in order to focus the core. This requires to
        switch on the LED and off the Laser. """

        self.camera_microscope.stop_camera()
        self.electronics.fiber_led = 1
        self.electronics.top_led = 0
        self.electronics.laser_power = 0
        self.electronics['servo'].move_servo(0)
        self.config['camera_fiber'].update(self.config['laser_focusing'])
        self.cameras['camera_fiber'].stop_camera()
        self.cameras['camera_fiber'].configure(self.config['camera_fiber'])
        self.cameras['camera_fiber'].start_free_run()

    @make_async_thread
    def start_microscope_focus(self):
        """ Starts the microscope focusing procedure. It switches off the laser, and switches on the LED from the top
        in order to see the fiber core on the microscope camera.
        """
        self.cameras['camera_fiber'].stop_camera()
        self.electronics['main_electronics'].fiber_led = 0
        self.electronics['main_electronics'].top_led = 1
        self.electronics['main_electronics'].laser_power = 0
        self.electronics['servo'].move_servo(0)
        self.config['camera_microscope'].update(self.config['microscope_focus'])
        self.cameras['camera_microscope'].stop_camera()
        self.cameras['camera_microscope'].configure(self.config['camera_microscope'])
        self.cameras['camera_microscope'].start_free_run()

    def crop_microscope_image(self, y: List[float]):
        """Sets the ROI on the microscope camera"""
        y.sort()

        self.config['camera_microscope']['roi_y1'] = int(y[0])
        self.config['camera_microscope']['roi_y2'] = int(y[1])
        self.cameras['camera_microscope'].stop_camera()
        self.cameras['camera_microscope'].configure(self.config['camera_microscope'])
        self.cameras['camera_microscope'].start_free_run()

    def clear_microscope_crop(self):
        self.config['camera_microscope'].stop_camera()
        self.config['camera_microscope'].clear_ROI()

    def done_fiber_focus(self, x: float, y:float):
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
        cropped_image = np.copy(last_image[x-15:x+15, y-15:y+15])
        cropped_image[cropped_image<np.mean(cropped_image)+np.std(cropped_image)] = 0
        params = fitgaussian(cropped_image)




