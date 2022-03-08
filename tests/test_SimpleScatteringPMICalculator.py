"""Test SimpleScatteringPMICalculator"""

import pytest
import sys
WPG_path = "/home/juncheng/GPFS/exfel/data/user/juncheng/WPG"
sys.path.insert(0, WPG_path)

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


def test_construct_calculator(tmpdir, input_data):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    print(pmi.parameters)


def test_run_backengine(tmpdir, input_data):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    pmi.backengine()
    print(pmi.output.get_data())
