"""Test WPGPropagationCalculator"""

import pytest
import os

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
pytest.mark.skipif("TRAVIS" in os.environ, reason="Test skipped on Travis CI")


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
