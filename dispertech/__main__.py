import os
from argparse import ArgumentParser
import logging
from PyQt5.QtWidgets import QApplication

from dispertech.models.experiment.nanoparticle_tracking.np_tracking import NPTracking
from dispertech.util.log import get_logger
from dispertech.view.start_window import StartWindow


def main():
    logger = get_logger()  # 'nanoparticle_tracking.model.experiment.nanoparticle_tracking.saver'
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    parser = ArgumentParser(description='Start the pyNTA software')
    parser.add_argument("-c", dest="config_file", required=False,
                        help="Path to the configuration file")
    args = parser.parse_args()

    if args.config_file is None:
        config_file = os.path.join(BASE_DIR, 'util', 'example_config.yml')
    else:
        config_file = args.config_file
    exp = NPTracking(config_file)
    exp.load_cameras()
    exp.load_electronics()
    exp.electronics.monitor_temperature()
    app = QApplication([])
    window = StartWindow(exp)
    window.show()
    app.exec()
    exp.finalize()


if __name__ == '__main__':
    main()
