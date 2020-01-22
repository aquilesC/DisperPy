from multiprocessing.spawn import freeze_support

import logging
import os
from time import sleep

from dispertech.models.experiment.fiber_end_qc.fiber_end_qc import FiberEndQualityControl
from experimentor.lib.log import get_logger, log_to_screen

freeze_support()

logger = get_logger(level=logging.DEBUG)
handler = log_to_screen(level=logging.DEBUG)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
experiment = FiberEndQualityControl(filename=os.path.join(BASE_DIR, 'fiber_end_qc.yml'))
experiment.initialize_camera()
experiment.load_electronics()
while experiment.initializing:
    sleep(.1)
    print('Waiting for initializing...')
experiment.servo_off()
experiment.start_free_run()
experiment.electronics.fiber_led = 1
sleep(.1)
experiment.save_camera_image()
experiment.electronics.fiber_led = 0
# experiment.stop_free_run()
# experiment.finalize()
print('I am here! :-)')
