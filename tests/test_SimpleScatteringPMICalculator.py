"""Test SimpleScatteringPMICalculator"""

import pytest
from SimExLite import DataCollection
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from SimExLite.PMICalculators import SimpleScatteringPMICalculator


sample_file = "./testFiles/2nip.pdb"
sample_data = SampleData.from_file(sample_file, ASEFormat, "sample_data")
wavefront_file = "./testFiles/prop.h5"
wavefront_data = WavefrontData.from_file(wavefront_file, WPGFormat, "wavefront_data")
input_data = DataCollection(sample_data, wavefront_data)


def test_construct_calculator(tmpdir):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    print(pmi.parameters)


def test_run_backengine(tmpdir):
    pmi = SimpleScatteringPMICalculator(
        name="SimpleScatteringPMICalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    pmi.backengine()
    print(pmi.output.get_data())
