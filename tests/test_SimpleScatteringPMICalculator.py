"""Test SimpleScatteringPMICalculator"""

import pytest
import os
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
pytestmark = pytest.mark.skipif('TRAVIS' in os.environ, reason='Test skipped on Travis CI')

from SimExLite import DataCollection
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from SimExLite.PMICalculators import SimpleScatteringPMICalculator
from SimExLite.PropagationCalculators import WPGPropagationCalculator


@pytest.fixture(scope="session")
def input_data(tmp_path_factory):
    """Prepare input data for the calculator"""
    tmp_path = tmp_path_factory.mktemp("data") / "prop.h5"
    sample_file = "./testFiles/2nip.pdb"
    sample_data = SampleData.from_file(sample_file, ASEFormat, "sample_data")
    wavefront_file = "./testFiles/wavefront.h5"
    wavefront_data = WavefrontData.from_file(
        wavefront_file, WPGFormat, "wavefront_data"
    )
    propagation = WPGPropagationCalculator(
        name="WPGCalculator",
        input=wavefront_data,
        instrument_base_dir=str(tmp_path),
        output_filenames="prop.h5",
    )
    prop_data = propagation.backengine().to_list()[0]
    input_data = DataCollection(sample_data, prop_data)
    return input_data


@pytest.mark.skipif('TRAVIS' in os.environ, reason='Test skipped on Travis CI')
def test_construct_calculator(tmpdir, input_data):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    print(pmi.parameters)


@pytest.mark.skipif('TRAVIS' in os.environ, reason='Test skipped on Travis CI')
def test_run_backengine(tmpdir, input_data):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    pmi.backengine()
    print(pmi.output.get_data())
