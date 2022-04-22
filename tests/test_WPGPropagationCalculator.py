"""Test EMCPhoton"""

import sys
import pytest

WPG_path = "/home/juncheng/GPFS/exfel/data/user/juncheng/WPG"
sys.path.insert(0, WPG_path)
from SimExLite.PropagationCalculators.WPGProgagationCalculator import (
    create_simple_beamline_file,
    WPGPropagationCalculator,
)
from SimExLite.WavefrontData import WavefrontData, WPGFormat


def test_simple_beamline_file(tmpdir):
    """Test creating a simple beamline config file"""
    create_simple_beamline_file(tmpdir / "test.py")


def test_default_calculator(tmpdir):
    input_data = WavefrontData.from_file("./wavefront.h5", WPGFormat, "input_wavefront")
    propagation = WPGPropagationCalculator(
        name="WPGCalculator", input=input_data, instrument_base_dir=str(tmpdir)
    )


def test_calculator_backengine(tmpdir):
    input_data = WavefrontData.from_file("./wavefront.h5", WPGFormat, "input_wavefront")
    propagation = WPGPropagationCalculator(
        name="WPGCalculator", input=input_data, instrument_base_dir=str(tmpdir)
    )
    propagation.backengine()
