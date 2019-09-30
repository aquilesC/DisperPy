# -*- coding: utf-8 -*-
"""
Localization Routines
=====================
Tracking particles is a relatively easy routine. PyNTA uses trackpy to analyse every frame that is generated. However,
linking localizations in order to build a trace is not trivial, since it implies preserving in memory the previous
locations. The main idea of these routines is that a main object :class:`~LocateParticles` holds the information of
the processes running. Moreover, there is a combination of threads and processes depending on the expected load.

It has to be noted that Windows has a peculiar way of dealing with new processes that prevents us from using methods,
but instead we are forced to use functions. This is very limiting but couldn't find a way around yet.

The core idea is that the localization uses the data broadcasted by :class:`~nanoparticle_tracking.model.experiment.publisher.Publisher`
in order to collect new frames, or save localizations to disk. It uses the
:class:`~nanoparticle_tracking.model.experiment.subscriber.Subscriber` in order to listen for the new data, and in turn publishes it
with the Publisher.

:copyright:  Aquiles Carattino <aquiles@uetke.com>
:license: GPLv3, see LICENSE for more details
"""
import trackpy as tp

from dispertech.models.experiment.nanoparticle_tracking.exceptions import DiameterNotDefined
from experimentor.lib.log import get_logger


def calculate_locations_image(image, **kwargs):
    """ Calculates the positions of the particles on an image. It used the trackpy package, which may not be
    installed by default.
    """
    if not 'diameter' in kwargs:
        raise DiameterNotDefined('A diameter is mandatory for locating particles')

    diameter = kwargs['diameter']
    del kwargs['diameter']
    logger = get_logger(name=__name__)
    locations = tp.locate(image, diameter, **kwargs)
    logger.debug('Got {} locations'.format(len(locations)))
    return locations
