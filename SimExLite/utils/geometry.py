# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

from extra_geom import GenericGeometry
import numpy as np


def getSimpleGeometry(pixel_size: float = 200e-6, npx: int = 128, npy: int = 64):
    """Get simple extra_geom geometry instance

    :param pixel_size: Pixel size in meter.
    :type pixel_size: float
    :param npx: Number of pixels in x direction, defaults to 128
    :type npx: int, optional
    :param npy: Number of pixels in y direction, defaults to 64
    :type npy: int, optional

    :return: Simple extra_geom geometry instance
    :rtype: `extra_geom.GenericGeometry`
    """
    simple_config = {
        "pixel_size": pixel_size,
        # y direction
        "slow_pixels": npy,
        # x direction
        "fast_pixels": npx,
        "corner_coordinates": [
            pixel_size * np.array([-(npx - 1) / 2.0, -(npy - 1) / 2.0, 0.0])
        ],
        # y direction
        "ss_vec": np.array([0, 1, 0]),
        # x direction
        "fs_vec": np.array([1, 0, 0]),
    }
    simple = GenericGeometry.from_simple_description(**simple_config)
    return simple


def writeSimpleGeometry(
    fn: str,
    pixel_size: float = 200e-6,
    npx: int = 128,
    npy: int = 64,
    clen: float = 0.13,
    adu_per_ev: float = 1e-3,
    photon_energy: float = 9300,
):
    """Write a simple geometry in to crstfel geometry format.

    :param fn: Output filename
    :type fn: str
    :param pixel_size: Pixel size in meter, defaults to 200e-6
    :type pixel_size: float, optional
    :param npx: Number of pixels in x direction, defaults to 128
    :type npx: int, optional
    :param npy: Number of pixels in y direction, defaults to 64
    :type npy: int, optional
    :param clen: Sample to detector distance in meter, defaults to 0.13
    :type clen: float, optional
    :param adu_per_ev: Signal intensity per electron voltage, defaults to 1e-3
    :type adu_per_ev: float, optional
    :param photon_energy: Photon energy in eV, defaults to 9300
    :type photon_energy: float, optional
    """
    geom = getSimpleGeometry(pixel_size, npx, npy)
    geom.write_crystfel_geom(
        fn, clen=clen, adu_per_ev=adu_per_ev, photon_energy=photon_energy
    )
