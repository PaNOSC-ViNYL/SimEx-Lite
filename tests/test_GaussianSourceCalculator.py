"""Test EMCPhoton"""

import os
import pytest
from SimExLite.SourceCalculators import GaussianSourceCalculator
from SimExLite.WavefrontData import WavefrontData

import h5py


def test_run_default_parameters():
    calculator = GaussianSourceCalculator("gaussian_source")
    print(calculator.parameters)
    data_out = calculator.backengine()
    print(type(data_out))


def test_run_default_parameters():
    calculator = GaussianSourceCalculator("gaussian_source", WPG_path)
    print(calculator.parameters)
    data_out = calculator.backengine()
    data_out.get_data()

# more detailed testing needed:

# test construction with and without default parameters
def test_do_def_pms():
    calculator = GaussianSourceCalculator(
        name="test_gaussian",
        input=None,
        output_keys="Gaussian_wavefront",
        output_filenames="test_wf.h5",
        instrument_base_dir="./",
        calculator_base_dir="GaussianSourceCalculator",
        parameters=None,
    )

    print(GaussianSourceCalculator.get_divergence_from_beam_diameter(1000, 0.0001))


def test_template():
    gs = GaussianSourceCalculator(
        name="GaussianTestSource",
        input=None,
        output_keys="Gaussian_wavefront",
        output_data_types=WavefrontData,
        output_filenames="wavefront.h5",
        instrument_base_dir="./",
        calculator_base_dir="GaussianSourceCalculator",
        parameters=None,
    )

    gs.parameters


def test_get_data():
    gsc = GaussianSourceCalculator("gaussian_source")
    gsc.backengine()
    d = gsc.output.get_data()
    print(d)


def test_save(gnc, tmp_path):
    gsc = GaussianSourceCalculator("gaussian_source")
    gsc.backengine()
    for f in gsc.output_file_paths:
        assert h5py.is_hdf5(f) is True


def test_dump_and_load(tmp_path='./'):
    tmpf = os.path.join(tmp_path, 'dumptest.dump')
    gsc = GaussianSourceCalculator("gaussian_source")
    gsc.backengine()
    gsc.dump(tmpf)
    gsc2 = GaussianSourceCalculator('fromdump')
    gsc2.from_dump(tmpf)
    for key in gsc.parameters.parameters.keys():
        assert gsc2.parameters['photon_energy'].value == gsc.parameters['photon_energy'].value




# test each method
# test a full construct-setup-run-collect workflow
# test dump/load to/from disk

test_get_data()

# test_wrong_WPG_path()
