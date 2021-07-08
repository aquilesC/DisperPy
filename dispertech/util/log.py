# ##############################################################################
#  Copyright (c) 2021 Aquiles Carattino, Dispertech B.V.                       #
#  log.py is part of DisperPy                                                  #
#  This file is released under an MIT license.                                 #
#  See LICENSE.MD for more information.                                        #
# ##############################################################################

"""
    Logger
    ======
    Adding log capacities to Dispertech
"""

import logging, multiprocessing


DEFAULT_FMT = "[%(levelname)8s] %(asctime)s %(name)s: %(message)s"


def get_logger(name='dispertech', level=logging.INFO):
    logger = multiprocessing.get_logger()
    logger.setLevel(level)
    return logger


DISPER_LOGGER = get_logger()

def log_to_screen(level=logging.INFO, fmt=None):
    fmt = fmt or DEFAULT_FMT
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    DISPER_LOGGER.addHandler(handler)
    return handler


def log_to_file(filename, level=logging.INFO, fmt=None):
    fmt = fmt or DEFAULT_FMT
    handler = logging.FileHandler(filename)
    handler.setLevel(level)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    DISPER_LOGGER.addHandler(handler)
    return handler
