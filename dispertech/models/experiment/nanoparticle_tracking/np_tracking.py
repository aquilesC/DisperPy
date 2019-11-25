import importlib
import json
import os
from datetime import datetime

import h5py
import numpy as np
import time
from multiprocessing import Queue, Event, Process

from dispertech.models.electronics.arduino import ArduinoModel
from dispertech.models.experiment.nanoparticle_tracking import NO_CORRECTION
from dispertech.models.experiment.nanoparticle_tracking.decorators import make_async_thread
from dispertech.models.experiment.nanoparticle_tracking.exceptions import StreamSavingRunning
from dispertech.models.experiment.nanoparticle_tracking.localization import calculate_locations_image
from dispertech.models.experiment.nanoparticle_tracking.saver import VideoSaver
from experimentor import general_stop_event
from experimentor.config.settings import SUBSCRIBER_EXIT_KEYWORD
from experimentor.lib.log import get_logger
from experimentor.models.experiments.base_experiment import BaseExperiment
from experimentor.models.listener import Listener
from experimentor.models.subscriber import Subscriber


class NPTracking(BaseExperiment):
    def __init__(self, filename=None):
        super().__init__(filename)
        self.save_stream_running = False
        self.align_camera_running = False
        self.acquire_camera_running = False
        self.saving_location = None

        self.dropped_frames = 0
        self.keep_acquiring = True
        self.acquiring = False
        self.tracking = False
        self.cameras = [None, None]  # This will hold the models for the two cameras
        self.electronics = None
        self.temp_image = [None, None]
        self.stream_saving_running = False
        self.free_run_running = [False, False]

        self.link_process_running = False
        self.last_index = 0  # Last index used for storing to the movie buffer
        self.stream_saving_running = False
        self.async_threads = []  # List holding all the threads spawn
        self.stream_saving_process = None
        self.link_particles_process = None
        self.calculate_histogram_process = None
        self.do_background_correction = False
        self.background_method = NO_CORRECTION
        self.last_locations = None

        self.waterfall_index = 0

        self.locations_queue = Queue()
        self.tracks_queue = Queue()
        self.size_distribution_queue = Queue()
        self.saver_queue = Queue()
        self.keep_locating = True
        self._threads = []
        self._processes = []
        self._stop_free_run = [Event(), Event()]

        self.temp_locations = None

        self.fps = 0  # Calculates frames per second based on the number of frames received in a period of time
        self.saver = None

    def configure_database(self):
        pass

    def load_latest_options(self):
        pass

    def load_camera(self, camera: str):
        """ Imports the appropriate model for a camera. It looks first on experimentor and then on dispertech.

        Parameters
        ----------
        camera : str
            The name of the model to be imported. It has to be found either on ``experimentor.models.cameras`` or
            on ``dispertech.models.cameras``.

        Returns
        -------
        camera : CameraModule
            The module where the ``Camera`` model is found. This is done in this way to avoid name clashes.

        .. todo::  We are forcing the importing from either experimentor or dispertech. It should be more flexible to
            allow fine tuning the importing path.
        """
        self.logger.info('Importing camera model {}'.format(camera))
        try:
            self.logger.debug('dispertech.models.cameras.' + camera)
            camera_model_to_import = 'dispertech.models.cameras.' + camera
            cam_module = importlib.import_module(camera_model_to_import)
        except ModuleNotFoundError:
            try:
                self.logger.debug('dispertech.models.cameras.' + camera)
                camera_model_to_import = 'dispertech.models.cameras.' + camera
                cam_module = importlib.import_module(camera_model_to_import)
            except ModuleNotFoundError:
                self.logger.error('The model {} for the camera was not found'.format(camera))
                raise
        return cam_module

    def initialize_camera(self, cam_module, config: dict):
        """ Initializes the camera to be used to acquire data. The information on the camera should be provided in the
            configuration file and loaded with :meth:`~self.load_configuration`.

            Returns
            -------
            Camera :
                An instance of a Camera Model, found within the ``cam_module``. It is also initialized using the
                internal method ``initialize``.
        """

        cam_init_arguments = config['init']

        if 'extra_args' in config:
            self.logger.info('Initializing camera with extra arguments')
            self.logger.debug(
                'cam_module.Camera({}, {})'.format(cam_init_arguments, config['extra_args']))
            camera = cam_module.Camera(cam_init_arguments, *config['extra_args'])
        else:
            self.logger.info('Initializing camera without extra arguments')
            self.logger.debug('cam_module.camera({})'.format(cam_init_arguments))
            camera = cam_module.Camera(cam_init_arguments)

        camera.initialize()
        camera.set_auto_exposure('Off')
        return camera

    def load_cameras(self):
        """ Loads the cameras based on the configuration file and initializes them. Cameras are stored in a list in
        which cameras[0] is the camera to look at the end of the fiber and cameras[1] is the camera used in the
        microscope.
        """
        camera_fiber = self.load_camera(self.config['camera_fiber']['model'])
        camera_microscope = self.load_camera(self.config['camera_microscope']['model'])
        self.cameras[0] = self.initialize_camera(camera_fiber, self.config['camera_fiber'])
        self.cameras[1] = self.initialize_camera(camera_microscope, self.config['camera_microscope'])
        self.cameras[0].set_pixel_format('Mono12')
        self.cameras[1].set_pixel_format('Mono12')

    def load_electronics(self):
        """ Loads the electronics controller. It is an Arduino microcontroller with extra build-in electronics to
        control the movement of a mirror mounted on Piezos.
        """
        self.electronics = ArduinoModel()
        self.electronics.initialize()

    def set_config(self, config_values: dict):
        self.config.update(config_values)

    def move_mirror(self, speed: int, direction: int, axis: int):
        self.electronics.move_mirror(direction, speed, axis)

    def home_mirror(self):
        """ Routine to find the center position of the mirror. In principle should run only once in a while, one
        the user things the mirror may be completly off-range.
        """
        pass

    def acquire_image(self):
        pass

    def set_ROI(self):
        pass

    def free_run(self):
        pass

    def acquire_data(self):
        pass

    def save_data(self, cam: int):
        """ Saves the last acquired image. The file to which it is going to be saved is defined in the config.
        """
        if self.temp_image[cam]:
            self.logger.info(f'Saving last acquired image of Camera {cam}')
            # Data will be appended to existing file
            file_name = self.config['saving']['filename_photo'] + '.hdf5'
            file_dir = self.config['saving']['directory']
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.logger.debug('Created directory {}'.format(file_dir))

            with h5py.File(os.path.join(file_dir, file_name), "a") as f:
                now = str(datetime.now())
                g = f.create_group(now)
                g.create_dataset('image', data=self.temp_image)
                g.create_dataset('metadata', data=json.dumps(self.config))
                f.flush()
            self.logger.debug('Saved image to {}'.format(os.path.join(file_dir, file_name)))
        else:
            self.logger.warning('Tried to save an image, but no image was acquired yet.')

    def save_image(self):
        pass

    def measure_sample_temperature(self):
        pass

    def measure_electronics_temperature(self):
        pass

    @make_async_thread
    def snap(self, cam: int):
        """ Snap a single frame.
        """
        self.logger.info(f'Snapping a picture with camera {int}')
        camera = self.cameras[cam]
        if cam == 0:
            config = self.config['camera_fiber']
        else:
            config = self.config['camera_microscope']
        camera.configure(config)
        camera.set_acquisition_mode(self.camera.MODE_SINGLE_SHOT)
        camera.trigger_camera()
        data = camera.read_camera()[-1]
        self.publisher.publish('snap', data)
        self.temp_image[cam] = data
        self.logger.debug('Got an image of {}x{} pixels'.format(data.shape[0], data.shape[1]))

    def start_free_run(self, cam: int):
        """ Starts continuous acquisition from the camera, but it is not being saved. This method is the workhorse
        of the program. While this method runs on its own thread, it will broadcast the images to be consumed by other
        methods. In this way it is possible to continuously save to hard drive, track particles, etc.
        """
        self.logger.info(f'Starting a free run acquisition of camera {cam}')
        i = 0  # Used to keep track of the number of frames
        camera = self.cameras[cam]
        if cam == 0:
            config = self.config['camera_fiber']
        else:
            config = self.config['camera_microscope']
        camera.configure(config)
        camera._stop_free_run.set()
        camera.start_free_run()
        self.logger.debug(f'Started free run of camera {camera}')

    def camera_high_sensitivity(self):
        """ Configures the camera looking at the fiber end to work in a pre-defined high-sensitivity mode. See the config
        file to see the parameters used.
        """
        camera = self.cameras[0]
        config = self.config['laser_focusing']['high']
        camera.configure(config)
        camera._stop_free_run.set()
        camera.start_free_run()
        self.logger.debug(f"Set laser-camera to high-sensitivity mode. "
                          f"Exposure: {config['exposure_time']}, Gain: {config['gain']}")

    def camera_low_sensitivity(self):
        """ Configures the camera looking at the fiber end to work in a pre-defined low-sensitivity mode. See the config
        file to see the parameters used.
        """
        camera = self.cameras[0]
        config = self.config['laser_focusing']['low']
        camera.configure(config)
        camera._stop_free_run.set()
        camera.start_free_run()
        self.logger.debug(f"Set laser-camera to low-sensitivity mode. "
                          f"Exposure: {config['exposure_time']}, Gain: {config['gain']}")

    def stop_free_run(self, cam: int):
        self.logger.info(f'Setting the stop_event of camera {cam}')
        self.cameras[cam].stop_free_run()

    def save_stream(self):
        """ Saves the queue to a file continuously. This is an async function, that can be triggered before starting
        the stream. It relies on the multiprocess library. It uses a queue in order to get the data to be saved.
        In normal operation, it should be used together with ``add_to_stream_queue``.
        """
        if self.save_stream_running:
            self.logger.warning('Tried to start a new instance of save stream')
            raise StreamSavingRunning('You tried to start a new process for stream saving')

        self.logger.info('Starting to save the stream')
        file_name = self.config['saving']['filename_video'] + '.hdf5'
        file_dir = self.config['saving']['directory']
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            self.logger.debug('Created directory {}'.format(file_dir))
        file_path = os.path.join(file_dir, file_name)
        max_memory = self.config['saving']['max_memory']

        self.stream_saving_process = Process(target=worker_listener,
                                             args=(file_path, json.dumps(self.config), 'free_run'),
                                             kwargs={'max_memory': max_memory})
        self.stream_saving_process.start()
        self.logger.debug('Started the stream saving process')

    def stop_save_stream(self):
        """ Stops saving the stream.
        """
        if self.save_stream_running:
            self.logger.info('Stopping the saving stream process')
            self.saver_queue.put('Exit')
            self.publisher.publish('free_run', 'stop')
            return
        self.logger.info('The saving stream is not running. Nothing will be done.')

    def start_tracking(self):
        """ Starts the tracking of the particles
        """
        if self.tracking:
            self.logger.warning("Tracking already running")
            self.stop_tracking()
            return
        self.tracking = True
        id = self.cameras[1].id
        self.logger.debug('Calculating positions with trackpy')
        self.localize = Subscriber(calculate_locations_image, f"{id}_free_run", "locations", [], {'diameter': 11})
        self.localize.start()
        self.connect(self.update_locations, 'locations')

    def update_locations(self, locations):
        self.temp_locations = locations

    @make_async_thread
    def stop_tracking(self):
        id = self.cameras[1].id
        self.listener.publish(SUBSCRIBER_EXIT_KEYWORD, f"{id}_free_run")
        while self.localize.is_alive():
            time.sleep(0.02)
        self.logger.info('Tracking Stopped')
        self.tracking = False
        self.temp_locations = None

    def start_saving_location(self):
        self.saving_location = True
        file_name = self.config['saving']['filename_tracks'] + '.hdf5'
        file_dir = self.config['saving']['directory']
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            self.logger.debug('Created directory {}'.format(file_dir))
        file_path = os.path.join(file_dir, file_name)
        self.location.start_saving(file_path, json.dumps(self.config))

    def stop_saving_location(self):
        self.saving_location = False
        self.location.stop_saving()

    def empty_saver_queue(self):
        """ Empties the queue where the data from the movie is being stored.
        """
        if not self.saver_queue.empty():
            self.logger.info('Clearing the saver queue')
            self.logger.debug('Current saver queue length: {}'.format(self.saver_queue.qsize()))
            while not self.saver_queue.empty() or self.saver_queue.qsize() > 0:
                self.saver_queue.get()
            self.logger.debug('Saver queue cleared')

    def empty_locations_queue(self):
        """ Empties the queue with location data.
        """
        if not self.locations_queue.empty():
            self.logger.info('Location queue not empty. Cleaning.')
            self.logger.debug('Current location queue length: {}'.format(self.locations_queue.qsize()))
            while not self.locations_queue.empty():
                self.locations_queue.get()
            self.logger.debug('Location queue cleared')

    def calculate_waterfall(self, image):
        """ A waterfall is the product of summing together all the vertical values of an image and displaying them
        as lines on a 2D image. It is how spectrometers normally work. A waterfall can be produced either by binning the
        image in the vertical direction directly at the camera, or by doing it in software.
        The first has the advantage of speeding up the readout process. The latter has the advantage of working with any
        camera.
        This method will work either with 1D arrays or with 2D arrays and will generate a stack of lines.
        """

        if self.waterfall_index == self.config['waterfall']['length_waterfall']:
            self.waterfall_data = np.zeros((self.config['waterfall']['length_waterfall'], self.camera.width))
            self.waterfall_index = 0

        center_pixel = np.int(self.camera.height / 2)  # Calculates the center of the image
        vbinhalf = np.int(self.config['waterfall']['vertical_bin'])
        if vbinhalf >= self.current_height / 2 - 1:
            wf = np.array([np.sum(image, 1)])
        else:
            wf = np.array([np.sum(image[:, center_pixel - vbinhalf:center_pixel + vbinhalf], 1)])
        self.waterfall_data[self.waterfall_index, :] = wf
        self.waterfall_index += 1
        self.publisher.publish('waterfall_data', wf)

    def start_saving(self):
        if self.saver and self.saver.is_alive():
            self.logger.warning('Traing to start the saver again')
            return
        file_path = os.path.join(self.config['saving']['directory'], self.config['saving']['filename_video'])
        meta = json.dumps(self.config)
        topic = f'{self.cameras[1].id}_free_run'
        max_memory = self.config['saving']['max_memory']
        self.saver = VideoSaver(file_path, meta, topic, max_memory)
        self.saver.start()

    def stop_saving(self):
        self.listener.publish(SUBSCRIBER_EXIT_KEYWORD, f'{self.cameras[1].id}_free_run')

    def finalize(self):
        general_stop_event.set()
        try:
            self.stop_free_run(cam=0)
        except Exception as e:
            self.logger.error(e)
        try:
            self.stop_free_run(cam=1)
        except Exception as e:
            self.logger.error(e)
        time.sleep(.5)
        self.stop_save_stream()
        self.stop_saving()
        try:
            self.electronics.finalize()
        except Exception as e:
            self.logger.error(e)
        super().finalize()
