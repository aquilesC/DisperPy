__version__ = '0.1.5'
import os
from multiprocessing import Event


general_stop_event = Event()  # This event is the last resource to stop threads and processes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
