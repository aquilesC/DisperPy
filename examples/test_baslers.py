import json
import logging

from time import sleep

import numpy as np

from dispertech.models.cameras.basler import Camera
from dispertech.models.experiment.nanoparticle_tracking.saver import VideoSaver
from experimentor import Q_
from experimentor.lib.log import get_logger, log_to_screen
from experimentor.models.experiments.base_experiment import BaseExperiment

logger = get_logger()
handler = log_to_screen(level=logging.DEBUG)

cam1 = Camera('da')
cam2 = Camera('ac')

cam1.initialize()
cam2.initialize()

cam1.camera.ExposureAuto.SetValue("Off")
cam2.camera.ExposureAuto.SetValue("Off")

cam1.set_exposure(Q_('5ms'))
cam2.set_exposure(Q_('5ms'))
cam1.set_gain(0)
cam2.set_gain(0)

exp = BaseExperiment()  # Needed in order to have one publisher at least

meta = {'user': 'aquiles'}
meta = json.dumps(meta)
video_saver = VideoSaver('this.h5', meta, f'{cam1.id}_free_run', 10)
video_saver.start()


cam1.start_free_run()
cam2.start_free_run()


print(f"Exposure cam1: {cam1.get_exposure()}")
print(f"Exposure cam2: {cam2.get_exposure()}")
old_i1 = 0
old_i2 = 0
while True:
    sleep(1)
    new_i = cam1.i
    print('Cam1', 'fps', cam1.fps, 'i', new_i, new_i-old_i1, cam1.listener.i, end=' ')
    old_i1 = new_i
    new_i = cam2.i
    print('Cam2', 'fps', cam2.fps, 'i', new_i, new_i-old_i2, cam1.listener.i)
    old_i2 = new_i
    # ready_buffers = cam1.camera.NumReadyBuffers.Value
    # if ready_buffers>0:
    #     print(ready_buffers)
    #     print(25 * '-')
    # ready_buffers = cam2.camera.NumReadyBuffers.Value
    # if ready_buffers>0:
    #     print(ready_buffers)
    #     print(25 * '-')
