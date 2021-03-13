#!/usr/bin/env python
"""Tests for `SimExLite` package."""

####################################################################################
#                                                                                  #
# This file is part of SimEx-Lite - The core package of the SIMEX platform         #
# providing the calculator interfaces.                                             #
#                                                                                  #
# Copyright (C) 2021  Juncheng E (juncheng.e@xfel.eu)                              #
#                                                                                  #
# This program is free software: you can redistribute it and/or modify it under    #
# the terms of the GNU Lesser General Public License as published by the Free      #
# Software Foundation, either version 3 of the License, or (at your option) any    #
# later version.                                                                   #
#                                                                                  #
# This program is distributed in the hope that it will be useful, but WITHOUT ANY  #
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A  #
# PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details. #
#                                                                                  #
# You should have received a copy of the GNU Lesser General Public License along   #
# with this program.  If not, see <https://www.gnu.org/licenses/                   #
#                                                                                  #
####################################################################################
import pytest

from SimExLite import SimExLite


@pytest.fixture
def rotationParam():
    """Rotation parameters"""
    return rotation_parameters()

def PMIParam():
    """PMI snapshot parameters"""
    return pmi_snapshot_parameters(
        slice_interval=100,
        number_of_slices=2,
        pmi_start_ID=1,
        pmi_stop_ID=1,
    )

def beamParam():
    """Beam parameters"""

def detectorGeom():
    """Detector geometry parameters"""

def testCalcWithPMIParam(rotationParam, PMIParam):
    """Test the construction of the class with parameters given as a dict."""

    parameters = pysingfelDiffractorParameters(
        calculate_Compton=False,
        number_of_diffraction_patterns=2,
        pmi_snapshot_parameters=PMIParam,
        rotation_parameters=rotationParam,
        beam_parameters=self.beam,
        detector_geometry=self.detector_geometry,
    )

def testCalcWithSimpleParam(rotationParam, PMIParam):
    """Test the construction of the class with parameters given as a dict."""

    parameters = pysingfelDiffractorParameters(
        calculate_Compton=False,
        number_of_diffraction_patterns=2,
        rotation_parameters=rotationParam,
        beam_parameters=self.beam,
        detector_geometry=self.detector_geometry,
    )

# Construct the object.
diffractor = SingFELPhotonDiffractor(parameters=parameters,
                                     input_path=self.input_h5,
                                     output_path='diffr_out.h5')

self.assertIsInstance(diffractor, SingFELPhotonDiffractor)
