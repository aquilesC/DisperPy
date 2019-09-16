import importlib
from multiprocessing import Queue, Event

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
        self.temp_acquire_image = None
        self.temp_align_image = None
        self.stream_saving_running = False

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
        self._stop_free_run = Event()

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

    def set_config(self, config_values: dict):
        pass

    def move_mirror(self, direction: int, speed: int):
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
