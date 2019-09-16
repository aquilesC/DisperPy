import importlib
import time
from multiprocessing import Queue, Event

from dispertech.models.electronics.arduino import ArduinoModel
from dispertech.models.experiment.nanoparticle_tracking.decorators import make_async_thread
from dispertech.models.experiment.nanoparticle_tracking.localization import LocateParticles
from experimentor.lib.log import get_logger
from experimentor.models.experiments.base_experiment import BaseExperiment


class NPTracking(BaseExperiment):
    def __init__(self, filename=None):
        super().__init__(filename)
        self.align_camera_running = False
        self.acquire_camera_running = False
        self.saving_location = None
        self.logger = get_logger(name=__name__)

        self.dropped_frames = 0
        self.keep_acquiring = True
        self.acquiring = False
        self.tracking = False
        self.cameras = [None, None]  # This will hold the models for the two cameras
        self.daq = None
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
        self.background_method = self.BACKGROUND_SINGLE_SNAP
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

        self.location = LocateParticles(self.publisher, self.config['tracking'])
        self.fps = 0  # Calculates frames per second based on the number of frames received in a period of time
        # sys.excepthook = self.sysexcept  # This is very handy in case there are exceptions that force the program to quit.

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
            self.logger.debug('experimentor.models.cameras.' + camera)
            camera_model_to_import = 'experimentor.models.cameras.' + camera
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

    def load_electronics(self):
        """ Loads the electronics controller. It is an Arduino microcontroller with extra build-in electronics to
        control the movement of a mirror mounted on Piezos.
        """
        self.daq = ArduinoModel(self.config['arduino']['port'])

    def set_config(self, config_values: dict):
        self.config.update(config_values)

    def move_mirror(self, speed: int, direction: int, axis: int):
        self.daq.move_mirror(direction, speed, axis)

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

    def save_data(self):
        pass

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

    @make_async_thread
    def start_free_run(self, cam: int):
        """ Starts continuous acquisition from the camera, but it is not being saved. This method is the workhorse
        of the program. While this method runs on its own thread, it will broadcast the images to be consumed by other
        methods. In this way it is possible to continuously save to hard drive, track particles, etc.
        """
        self.logger.info(f'Starting a free run acquisition of camera {cam}')
        first = True
        i = 0  # Used to keep track of the number of frames
        camera = self.cameras[cam]
        if cam == 0:
            config = self.config['camera_fiber']
        else:
            config = self.config['camera_microscope']
        camera.configure(config)
        self._stop_free_run[cam].clear()
        t0 = time.time()
        self.free_run_running[cam] = True
        self.logger.debug('First frame of a free_run')
        camera.set_acquisition_mode(camera.MODE_CONTINUOUS)
        camera.trigger_camera()  # Triggers the camera only once
        while not self._stop_free_run[cam].is_set():
            data = camera.read_camera()
            if not data:
                continue
            self.logger.debug('Got {} new frames'.format(len(data)))
            for img in data:
                i += 1
                self.logger.debug('Number of frames: {}'.format(i))
                # This will broadcast the data just acquired with the current timestamp
                # The timestamp is very unreliable, especially if the camera has a frame grabber.
                self.publisher.publish('free_run', [time.time(), img])
                self.temp_image = img
            self.fps = round(i / (time.time() - t0))
        self.free_run_running[cam] = False
        camera.stopAcq()

    def stop_free_run(self, cam: int):
        self.logger.info(f'Setting the stop_event of camera {cam}')
        self._stop_free_run[cam].set()


