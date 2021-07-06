# ##############################################################################
#  Copyright (c) 2021 Aquiles Carattino, Dispertech B.V.                       #
#  fluo.py is part of DisperPy                                                 #
#  This file is released under an MIT license.                                 #
#  See LICENSE.md.MD for more information.                                        #
# ##############################################################################

import os
from datetime import datetime
from multiprocessing import Event

import numpy as np
import copy as copy #m required in Code1dot7for_implementation

from calibration.models.movie_saver import MovieSaver
from experimentor.models.experiments.exceptions import ExperimentException

from dispertech.models.electronics.arduino import ArduinoModel
from experimentor import Q_
from experimentor.core.signal import Signal
from experimentor.lib.fitgaussian import fitgaussian
from experimentor.models.action import Action
from experimentor.models.devices.cameras.basler.basler import BaslerCamera as Camera
from experimentor.models.devices.cameras.exceptions import CameraTimeout
from experimentor.models.experiments import Experiment
import time


class Fluorescence(Experiment):
    new_image = Signal()

    def __init__(self, filename=None):
        super(Fluorescence, self).__init__(filename=filename)

        self.background = None
        self.camera_microscope = None
        self.camera_fiber = None

        self.electronics = None
        self.lasers = None  # To hold the communication with the arduino that will control the laser power

        self.fiber_center_position = None
        self.fiber_radius = 0
        self.laser_center = None
        self.saving = False
        self.saving_event = Event()
        self.finalized = False
        self.saving_process = None
        self.remove_background = False

    @Action
    def initialize(self):
        """ Initialize both cameras and the electronics. The devices are set to an initial state that can be configured
        through the configuration file.

        """
        self.initialize_cameras()
        self.initialize_electronics()
        self.logger.debug('Starting free runs and continuous reads')
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()
        self.camera_fiber.start_free_run()
        self.camera_fiber.continuous_reads()

    def initialize_cameras(self):
        """Assume a specific setup working with baslers and initialize both cameras"""
        self.logger.info('Initializing cameras')
        config_mic = self.config['camera_microscope']
        self.camera_microscope = Camera(config_mic['init'], initial_config=config_mic['config'])

        config_fiber = self.config['camera_fiber']
        self.camera_fiber = Camera(config_fiber['init'], initial_config=config_fiber['config'])

        for cam in (self.camera_fiber, self.camera_microscope):
            self.logger.info(f'Initializing {cam}')
            cam.initialize()
            self.logger.debug(f'Configuring {cam}')

    def initialize_electronics(self):
        """ For the time being there are two boards connected to the computer. This method initializes both.

        TODO:: This will change in the future, when electronics are made on a single board.
        """

        self.electronics = ArduinoModel(**self.config['electronics']['piezo'])
        self.logger.info('Initializing electronics arduino')
        self.electronics.initialize()

        self.lasers = ArduinoModel(**self.config['electronics']['laser'])
        self.logger.info('Initializing electronics lasers')
        self.lasers.initialize()

    @Action
    def toggle_top_led(self):
        self.electronics.top_led = 0 if self.electronics.top_led else 1

    @Action
    def toggle_fiber_led(self):
        self.electronics.fiber_led = 0 if self.electronics.fiber_led else 1

    def get_latest_image(self, camera: str):
        """ Reads the camera.

        .. TODO:: This must be changed since it was inherited from the time when both cameras were stored in a dict
        """

        if camera == 'camera_microscope':
            tmp_image = self.camera_microscope.temp_image
            if self.remove_background:
                if self.background is None:
                    self.background = np.empty((tmp_image.shape[0], tmp_image.shape[1], 10), dtype=np.uint16)
                self.background = np.roll(self.background, -1, 2)
                self.background[:, :, -1] = tmp_image
                bkg = np.mean(self.background, 2, dtype=np.uint16)
                # tmp_image = (tmp_image.astype(np.int16) - bkg).clip(0, 2**16-1).astype(np.uint16)
                ttmp_image = tmp_image - bkg
                ttmp_image[bkg>tmp_image] = 0
                tmp_image = ttmp_image
            else:
                self.background = None
            # return (tmp_image/2**4).astype(np.uint8)
            return tmp_image
        else:
            return self.camera_fiber.temp_image

    def stop_free_run(self, camera: str):
        """ Stops the free run of the camera.

        :param camera: must be the same as specified in the config file, for example 'camera_microscope'

        .. todo:: This must change, since it was inherited from the time both cameras were stored in a dict
        """
        self.logger.info(f'Stopping the free run of {camera}')
        if camera == 'camera_microscope':
            self.camera_microscope.stop_free_run()
        elif camera == 'camera_fiber':
            self.camera_fiber.stop_free_run()

    def prepare_folder(self) -> str:
        """Creates the folder with the proper date, using the base directory given in the config file"""
        base_folder = self.config['info']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        folder = os.path.join(base_folder, today_folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        return folder

    def get_filename(self, base_filename: str) -> str:
        """Checks if the given filename exists in the given folder and increments a counter until the first non-used
        filename is available.

        :param base_filename: must have two placeholders {cartridge_number} and {i}
        :returns: full path to the file where to save the data
        """
        folder = self.prepare_folder()
        i = 0
        cartridge_number = self.config['info']['cartridge_number']
        while os.path.isfile(os.path.join(folder, base_filename.format(
                cartridge_number=cartridge_number,
                i=i))):
            i += 1

        return os.path.join(folder, base_filename.format(cartridge_number=cartridge_number, i=i))

    def save_image_fiber_camera(self, filename: str) -> None:
        """ Saves the image being registered by the camera looking at the fiber-end. Does not alter the configuration
        of the camera, therefore what you see is what you get.

        :param filename: it assumes it has a placeholder for {cartridge_number} and {i} in order not to over write
                            files
        """
        self.logger.info('Acquiring image from the fiber')
        self.camera_fiber.stop_free_run()
        self.camera_fiber.config.apply_all()
        self.camera_fiber.trigger_camera()
        time.sleep(.25)
        image = self.camera_fiber.read_camera()[-1]
        self.logger.info(f'Acquired fiber image, max: {np.max(image)}, min: {np.min(image)}')

        filename = self.get_filename(filename)
        np.save(filename, image)
        self.logger.info(f'Saved fiber data to {filename}')
        self.camera_fiber.start_free_run()

    def save_image_microscope_camera(self, filename: str) -> None:
        """Saves the image shown on the microscope camera to the given filename.

        :param str filename: Must be a string containing two placeholders: {cartrdige_number}, {i}
        """
        filename = self.get_filename(filename)
        t0 = time.time()
        temp_image = self.camera_microscope.temp_image
        while temp_image is None:
            temp_image = self.camera_fiber.temp_image
            if time.time() - t0 > 10:
                raise CameraTimeout("It took too long to get a new frame from the microscope")
        np.save(filename, temp_image)
        self.logger.info(f"Saved microscope data to {filename}")

    @Action
    def start_binning(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        self.camera_microscope.binning_y = 4
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    @Action
    def stop_binning(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        self.camera_microscope.binning_y = 1
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    @Action
    def save_fiber_core(self):
        """Saves the image of the fiber core.

        .. TODO:: This method was designed in order to allow extra work to be done, for example, be sure
            the LED is ON, or use different exposure times.
        """
        image = self.camera_fiber.temp_image
        self.logger.info(f'Saving fiber image, max: {np.max(image)}, min: {np.min(image)}')
        filename = self.get_filename(self.config['info']['filename_fiber'])
        np.save(filename, image)
        # self.save_image_fiber_camera(self.config['info']['filename_fiber'])

    @Action
    def save_laser_position(self):
        """ Saves an image of the laser on the camera.

        .. TODO:: Having a separate method just to save the laser position is useful when wanting to automatize
            tasks, for example using several laser powers to check proper centroid extraction.
        """
        self.logger.info('Saving laser position')
        current_laser_power = self.config['laser']['power']
        camera_config = self.config['camera_fiber'].copy()
        self.config['laser']['power'] = self.config['centroid']['laser_power']
        self.config['camera_fiber']['exposure_time'] = Q_(self.config['centroid']['exposure_time'])
        self.config['camera_fiber']['gain'] = self.config['centroid']['gain']
        self.set_laser_power(self.config['centroid']['laser_power'])
        self.save_image_fiber_camera(self.config['info']['filename_laser'])
        self.stop_free_run('camera_fiber')
        self.set_laser_power(current_laser_power)
        self.config['laser']['power'] = current_laser_power
        self.config['camera_fiber'] = camera_config.copy()
        self.camera_fiber.start_free_run()

    @Action
    def save_particles_image(self):
        """ Saves the image shown on the microscope. This is only to keep as a reference. This method wraps the
        actual method `meth:save_iamge_microscope_camera` in case there is a need to set parameters before saving. Or
        if there are going to be different saving options (for example, low and high laser powers, etc.).
        """
        base_filename = self.config['info']['filename_microscope']
        self.save_image_microscope_camera(base_filename)

    def calculate_gaussian_centroid(self, image, x, y, crop_size):
        x = round(x)
        y = round(y)
        cropped_data = np.copy(image[x - crop_size:x + crop_size, y - crop_size:y + crop_size])
        cropped_data[cropped_data < np.mean(cropped_data)] = 0
        try:
            p = fitgaussian(cropped_data)
            extracted_position = p[1] + x - crop_size, p[2] + y - crop_size
            self.logger.info(f'Calculated center: {extracted_position}')
        except:
            extracted_position = None
            self.logger.exception('Exception fitting the gaussian')
        return extracted_position

    def calculate_laser_center(self):
        """ This method calculates the laser position based on the reflection from the fiber tip. It is meant to be
        used as a reference when focusing the laser on the fiber for calibrating.

        .. TODO:: Judge how precise this is. Perhaps it would be possible to use it instead of the laser reflection on
            the mirror?
        """
        image = np.copy(self.camera_fiber.temp_image)
        brightest = np.unravel_index(image.argmax(), image.shape)
        self.laser_center = self.calculate_gaussian_centroid(image, brightest[0], brightest[1], crop_size=25)

    def calculate_fiber_center(self, x, y, crop_size=15):
        """ Calculate the core center based on some initial coordinates x and y.
        It will perform a gaussian fit of a cropped region and store the data.

        Parameters
        ----------
        x: float
            x-coordinate for the initial fit of the image
        y: float
            y-coordinate for the initail fit of the image
        crop_size: int, optional
            Size of the square crop around x, y in order to minimize errors
        """
        self.logger.info(f'Calculating fiber center using ({x}, {y})')
        image = np.copy(self.camera_fiber.temp_image)
        self.fiber_center_position = self.calculate_gaussian_centroid(image, x, y, crop_size)
        return [x,y] #m


    def set_roi(self, y_min, height):
        """ Sets up the ROI of the microscope camera. It assumes the user only crops the vertical direction, since the
        fiber goes all across the image.

        Parameters
        ----------
        y_min : int
            The minimum height in pixels
        height : int
            The total height in pixels
        """
        self.camera_microscope.stop_free_run()
        self.camera_microscope.stop_continuous_reads()
        self.background = None  # This is to prevent shape mismatch between before and after
        current_roi = self.camera_microscope.ROI
        new_roi = (current_roi[0], (y_min, height))
        self.camera_microscope.ROI = new_roi
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    def clear_roi(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        full_roi = (
            (0, self.camera_microscope.ccd_width),
            (0, self.camera_microscope.ccd_height)
        )
        self.camera_microscope.ROI = full_roi
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    def start_saving_images(self):
        if self.saving:
            self.logger.warning('Saving process still running: self.saving is true')
        if self.saving_process is not None and self.saving_process.is_alive():
            self.logger.warning('Saving process is alive, stop the saving process first')
            return

        self.saving = True
        base_filename = self.config['info']['filename_movie']
        file = self.get_filename(base_filename)
        self.saving_event.clear()
        self.saving_process = MovieSaver(
            file,
            self.config['saving']['max_memory'],
            self.camera_microscope.frame_rate,
            self.saving_event,
            self.camera_microscope.new_image.url,
            topic='new_image',
            metadata=self.camera_microscope.config.all(),
        )

    def stop_saving_images(self):
        self.camera_microscope.new_image.emit('stop')
        # self.emit('new_image', 'stop')

        # self.saving_event.set()
        time.sleep(.05)

        if self.saving_process is not None and self.saving_process.is_alive():
            self.logger.warning('Saving process still alive')
            time.sleep(.1)
        self.saving = False

    def finalize(self):
        if self.finalized:
           return
        self.logger.info('Finalizing calibration experiment')
        if self.saving:
            self.logger.debug('Finalizing the saving images')
            self.stop_saving_images()
        self.saving_event.set()
        self.camera_fiber.keep_reading = False
        self.camera_microscope.keep_reading = False
        if self.camera_fiber is not None:
            self.camera_fiber.finalize()
        if self.camera_microscope is not None:
            self.camera_microscope.finalize()
        self.set_laser_power(0)

        super(CalibrationSetup, self).finalize()
        self.finalized = True



    def creating_multiply_array(self,width, height, power=5):
        # function added by Matthijs (function to create multiply array)
        #This function is not used right now, and will most likely not be used in the future, so it will probably be
        #removed.
        '''This function creates the multiply array which is used to find the fiber core. The inputs are
        the width and height of the image (in pixels), depending on the camere used. The power
        determines the relative difference in the values between the middle and the edges of the
        multiply_array. power is set to 5 by default.'''

        'Required imports'
        from numpy import linspace, rot90

        '''Below multiply_array_one is created this is an array with the same dimensions as the
        'image'. This array has high values (approaching 1) towards the vertical middle and low values
        (approaching 0) towards the bottom and top
        '''
        multiply_array_one = (linspace(2, 0, width * height).reshape(height, width) * \
                              linspace(0, 2, width * height).reshape(height, width))

        '''Below multiply_array_two is created, this is an array with the same dimensions as the
        'image' rotated by 90 degrees. This array also has high values (approachin 1) towards the
        vertical middle and low values (approaching 0) towards the upper and lower edge'''
        multiply_array_two = (linspace(2, 0, width * height).reshape(width, height) * \
                              linspace(0, 2, width * height).reshape(width, height))

        '''Below multiply_array_two is rotated by 90 degrees. The new array (multiply_array_rot) has
        the same dimensions as the 'image', and has high values towards the horizontal middle
        (approaching 1) and low values towards the horizontal (left and right) edges (approaching 0) '''
        multiply_array_two_rot = rot90(multiply_array_two)

        '''Below multiply_array_one en multiply_array_two_rot are multiplied to create an array with
        high (approaching 1) values towards both the horizontal and vertical middle, and low
        (approaching 0) values towards all edges'''
        multiply_array = multiply_array_one * multiply_array_two_rot

        '''Below the multiply_array is raised to  a power (see function input), to increase the relative
        difference between the high and low values '''
        multiply_array = multiply_array ** power
        return multiply_array


    def creating_multiply_array_2(self,width, height, power=2.5):
        # Function added by Matthijs, (this is an improved version of 'creating_multiply_array'), this fucntain is
        # destend to be removed, since the function import_or_create_and_save_multiply_array (see below) already
        # contains this function
        '''This function is based on the function 'creating_multiply_array' (see description below).
        Differecne is, that this function produces symmetric multiply_array's, where the function
        creating_multiply_array creates assymetric multiply arrays. The power is set on 2.5 by default,
        although values of 2 and 3 yield the same result (2.5 is chosen because it is halfway between
        2 and 3).

        creating_multiply_array: This function creates the multiply array which is used to find the fiber
        core. The inputs are the width and height of the image (in pixels), depending on the camere
        used. The power determines the relative difference in the values between the middle and the
        edges of the multiply_array. power is set to 5 by default.'''

        'Required imports'
        from numpy import linspace, rot90, flip

        '''Below multiply_array_one is created this is an array with the same dimensions as the
        'image'. This array goes from 2 (upper left corner) to 0 (lower right corner) with equal steps
        '''
        multiply_array_one = (linspace(2, 0, width * height).reshape(height, width))

        '''Below multiply_array_one is redefined as an array with small values towards the vertical
        edges and big values towards the vertical middle (the function is symmetric in the horizontal
        direction)'''
        multiply_array_one = multiply_array_one * flip(multiply_array_one, 1) * \
                             rot90(rot90(multiply_array_one)) * flip(rot90(rot90(multiply_array_one)), 1)

        multiply_array_two = (linspace(2, 0, width * height).reshape(width, height))
        multiply_array_two = multiply_array_two * flip(multiply_array_two, 1) * \
                             rot90(rot90(multiply_array_two)) * flip(rot90(rot90(multiply_array_two)), 1)

        '''Creating an array with big values towards the middle (aaoriachin 1) and small values
        towards the edges (approachin 0)'''
        multiply_array = multiply_array_one * rot90(multiply_array_two)

        '''Below the multiply_array is raised to  a power (see function input), to increase the relative
        difference between the high and low values '''
        multiply_array = multiply_array ** power
        return multiply_array


    def import_or_create_and_save_multiply_array(self, width, height):
        # Function (added by Matthijs) that checks whether the multiply array is stored in a file, and is the prooper
        # size. If not, the multiply array is created, saved and used.
        # This function will be replaced very soon by a function that does not have a function within a function, and
        #is addeded with respect to the notes on page 75.
        """The inputs are the width and the height of the camera.

        This function checks whether the file (file_name in code) containing the multiply array exists
        (in the same folder that contains this function). If it exists and is the proper size (width and
        height), then the multiply array is imported and used. If the file containing the multiply array
        does not exist (in the folder) or is the wrong size, the multiply array is created (with the
        function:  'creating_multiply_array_2'), saved in the folder (under file_name), and used."""

        'Necesarry import'
        from numpy import save, load

        '''Creating File_exist variable as a None. This variable is used to check whether the NumPy
        array exists'''
        File_exist = None

        'Name of the file'
        file_name = 'multiply_array.npy'

        'Function that can create the multiply array if necesarry'

        def creating_multiply_array_2(width, height, power=2.5):
            # Function (added by Matthijs) that will be removed soon, since there are newer versions to create (or
            # import) a multiply array.
            '''This function is based on the function 'creating_multiply_array' (see description below).
            Differecne is, that this function produces symmetric multiply_array's, where the function
            creating_multiply_array creates assymetric multiply arrays. The power is set on 2.5 by default,
            although values of 2 and 3 yield the same result (2.5 is chosen because it is halfway between
            2 and 3).

            creating_multiply_array: This function creates the multiply array which is used to find the fiber
            core. The inputs are the width and height of the image (in pixels), depending on the camere
            used. The power determines the relative difference in the values between the middle and the
            edges of the multiply_array. power is set to 5 by default.'''

            'Required imports'
            from numpy import linspace, rot90, flip

            '''Below multiply_array_one is created this is an array with the same dimensions as the
            'image'. This array goes from 2 (upper left corner) to 0 (lower right corner) with equal steps
            '''
            multiply_array_one = (linspace(2, 0, width * height).reshape(height, width))

            # Below multiply_array_one is redefined as an array with small values towards the vertical
            # edges and big values towards the vertical middle (the function is symmetric in the horizontal
            # direction)
            multiply_array_one = multiply_array_one * flip(multiply_array_one, 1) * \
                                 rot90(rot90(multiply_array_one)) * flip(rot90(rot90(multiply_array_one)), 1)

            multiply_array_two = (linspace(2, 0, width * height).reshape(width, height))
            multiply_array_two = multiply_array_two * flip(multiply_array_two, 1) * \
                                 rot90(rot90(multiply_array_two)) * flip(rot90(rot90(multiply_array_two)), 1)

            '''Creating an array with big values towards the middle (aaoriachin 1) and small values
            towards the edges (approachin 0)'''
            multiply_array = multiply_array_one * rot90(multiply_array_two)

            '''Below the multiply_array is raised to  a power (see function input), to increase the relative
            difference between the high and low values '''
            multiply_array = multiply_array ** power
            return multiply_array

        'Testen of file bestaat, als '
        try:
            multiply_array = load(file_name)
            print('Try if file exists')
        except IOError:
            print("File non existing in folder")
            File_exist = False
        else:
            print('File existing in folder')
            File_exist = True
        finally:
            pass

        'Checking whether the multiply array exist'
        if File_exist is True:
            if len(multiply_array[0]) == width and len(multiply_array) == height:
                print('Good dimension')
            else:
                print('Wrong dimensions')
                print('Create multply array with propper dimensions')
                multiply_array = creating_multiply_array_2(width, height)
                print('Save multiply array')
                save(file_name, multiply_array)

        else:
            print('Create multiply array')
            multiply_array = creating_multiply_array_2(width, height)
            print('Save multiply array')
            save(file_name, multiply_array)

        return multiply_array

    #Function added by Matthijs (to find the core coordinates)
    def Code1dot7for_implementation(self,npy_array, multiply_array, n_value=0.001):
        print(__file__)
        #The function input npy_file is changed to npy_array, multiply_array is now an input instead
        #of being created in the code.
        '''
        The npy_array is the array from the camera data, the multiply_array is the array which is
        multiplied with the array created by the camera. The n_value decides whcih part of the pixels
        will be considerd 'bright' (these are put to 1 in the binary array).

        This code is a modefied version of code 1.7, so it can be implemented to work in the system
        '''

        #Below 'array' is created, which is the product of the multiply_array and the original array
        array = (npy_array * multiply_array).astype(int)

        #Determination of the threshold value
        threshold = round(np.percentile(array, (100 - (100 * n_value)), interpolation='nearest'))

        #Below a binary array is created, pixels above the threshold get assigned the value 1 and
        #pixels below the threshold get assigned the value 0
        np_array_binary = np.where(array > threshold, 1, 0)

        #The lines of code below put the edges of the image to 0
        #Puts the top column to 0
        np_array_binary[0, :] = 0
        #Puts the lowest column to 0
        np_array_binary[-1, :] = 0
        #Puts the left column to zero
        np_array_binary[:, 0] = 0
        #Puts the right column to zero
        np_array_binary[:, -1] = 0

        #Determination of the bright pixel locations
        bright_pixel_locations = np.where(np_array_binary == 1)

        #List containing the bright pixel coordinates
        bright_coords = []

        #Filling the list of bright pixel coordinates
        for i in range(0, len(bright_pixel_locations[0])):
            bright_coords.append([bright_pixel_locations[0][i], bright_pixel_locations[1][i]])

        #Previous_length_bright_coords is a variable required in while loop, so the function does not hang, reason for
        #assigning the value -1, is so, the if statement: if previous_length_bright_coords == len(bright_coords_copy)
        #can never be 'True' during the first itteration in the while loop.
        previous_length_bright_coords = -1

        #Number of bright neighbors required
        bright_negihbors_required = 4

        #In this while loop, the determination of the pixels at the fiber core is done
        while len(bright_coords) >= 1:

            #Copy of the binary array
            binary_copy = copy.copy(np_array_binary)
            bright_coords_copy = copy.copy(bright_coords)

            #In this for loop, for eacht bright pixel the number of bright (direct) neighbors is determined.
            for i in bright_coords:
                bright_neighbors = 0
                if np_array_binary[i[0] - 1][i[1]] == 1:
                    bright_neighbors = bright_neighbors + 1
                if np_array_binary[i[0] + 1][i[1]] == 1:
                    bright_neighbors = bright_neighbors + 1
                if np_array_binary[i[0]][i[1] - 1] == 1:
                    bright_neighbors = bright_neighbors + 1
                if np_array_binary[i[0]][i[1] + 1] == 1:
                    bright_neighbors = bright_neighbors + 1

                #If a pixel has less bright neighbors than required, it is put to 0.
                if bright_neighbors < bright_negihbors_required:
                    binary_copy[i[0]][i[1]] = 0
                    bright_coords_copy.remove(i)
                else:
                    pass

            #If nothing is added to the list bright_coords_copy, the threshold for required bright neighbors is
            # lowered, and both the binary array as the bright coords list are kept the same

            if len(bright_coords_copy) == 0:
                bright_negihbors_required = bright_negihbors_required - 1
            else:
                np_array_binary = binary_copy
                bright_coords = bright_coords_copy

            #When there is no more pixel with any bright neighbors, break
            if bright_negihbors_required == 0:
                break

            if previous_length_bright_coords == len(bright_coords_copy):
                #When pixels are no longer being removed, the itteration is stopped with the break commend
                break

            #Number of bright coordinates during the previous round through the while loop
            previous_length_bright_coords = len(bright_coords)

        #Determening x- and y coordinate core
        x = 0
        y = 0
        for i in bright_coords:
            x = x + i[1]
            y = y + i[0]
        x = round(x / len(bright_coords))
        y = round(y / len(bright_coords))
        self.fiber_center_position = [x,y]
