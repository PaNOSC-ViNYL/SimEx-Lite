"""Test WPGPropagationCalculator"""

import pytest

from SimExLite.PropagationCalculators.WPGPropagationCalculator import (
    create_simple_beamline_file,
    WPGPropagationCalculator,
)
from SimExLite.WavefrontData import WavefrontData, WPGFormat


def test_simple_beamline_file(tmpdir):
    """Test creating a simple beamline config file."""
    create_simple_beamline_file(tmpdir / "test.py")


def test_default_calculator(tmpdir):
    """Test the construct the calculator with default parameters."""
    input_data = WavefrontData.from_file(
        "./testFiles/wavefront.h5", WPGFormat, "input_wavefront"
    )
    WPGPropagationCalculator(
        name="WPGCalculator", input=input_data, instrument_base_dir=str(tmpdir)
    )


def test_calculator_backengine(tmpdir):
    """Test the calculator backengine with default parameters."""
    input_data = WavefrontData.from_file(
        "./testFiles/wavefront.h5", WPGFormat, "input_wavefront"
    )
    propagation = WPGPropagationCalculator(
        name="WPGCalculator", input=input_data, instrument_base_dir=str(tmpdir)
    )
    propagation.backengine()
