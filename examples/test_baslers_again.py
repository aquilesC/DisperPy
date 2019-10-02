## This file is meant to fail. This shows the error with basler buffers

import time
from threading import Thread

from time import sleep

from pypylon import pylon

from experimentor import Q_
from dispertech.models.cameras.basler import Camera


cam1 = Camera('ac')
cam1.initialize()
cam1.set_exposure(Q_('1ms'))
cam1.set_acquisition_mode(cam1.MODE_CONTINUOUS)
cam1.trigger_camera()

cam2 = Camera('da')
cam2.initialize()
cam2.set_exposure(Q_('1ms'))
cam2.set_acquisition_mode(cam2.MODE_CONTINUOUS)
cam2.trigger_camera()

t0 = time.time()
def read_camera(cam):
    j = 0
    n = 0
    while True:
        num_buffers = cam.camera.NumReadyBuffers.Value

        if num_buffers:
            img = [None] * num_buffers
            for i in range(num_buffers):
                grab = cam.camera.RetrieveResult(int(cam.exposure.m_as('ms')), pylon.TimeoutHandling_Return)
                if grab and grab.GrabSucceeded():
                    img = grab.GetArray()
                    grab.Release()
                    j += 1
                else:
                    n += 1
            fps = j/(time.time()-t0)
            print(f'{cam} Frames: {j:06}, missed: {n:06}, fps: {fps:3}\n', end='')

t1 = Thread(target=read_camera, args=(cam1, ))
t2 = Thread(target=read_camera, args=(cam2, ))

t1.start()
t2.start()

while t1.is_alive():
    sleep(10)
