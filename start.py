import os
import sys
from time import sleep


if __name__ == "__main__":
    os.environ.setdefault("EXPERIMENTOR_SETTINGS_MODULE", "calibration_settings")

    this_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(this_dir)

    from experimentor.core.app import ExperimentApp

    app = ExperimentApp(gui=False)
    while app.gui_thread.is_alive():
        sleep(1)
