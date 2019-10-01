from time import sleep

from dispertech.models.experiment.nanoparticle_tracking.np_tracking import NPTracking


experiment = NPTracking('dispertech.yml')
experiment.load_cameras()
experiment.load_electronics()

experiment.cameras[0].start_free_run()
experiment.cameras[1].start_free_run()

print(f"Exposure cam1: {experiment.cameras[0].get_exposure()}")
print(f"Exposure cam2: {experiment.cameras[1].get_exposure()}")
old_i1 = 0
old_i2 = 0
while True:
    sleep(1)
    new_i = experiment.cameras[0].i
    print('Cam1', 'fps', experiment.cameras[0].fps, 'i', new_i, new_i-old_i1)
    old_i1 = new_i
    new_i = experiment.cameras[1].i
    print('Cam2', 'fps', experiment.cameras[1].fps, 'i', new_i, new_i-old_i2)
    old_i2 = new_i
