"""Test DetectorCalculators"""

import pytest
import numpy as np
import h5py
from SimExLite.DiffractionData import histogramParams
from SimExLite.DetectorCalculators import gaussianNoiseCalculator, gaussianNoisePrameters


def getGNC():
    h5_file = './testFiles/singfel-multi.h5'
    xcs = np.array([-1.845, 56.825, 114.623])
    fwhms = np.array([20.687, 26.771, 29.232])
    hist_params = histogramParams(xcs, fwhms)
    params = gaussianNoisePrameters(hist_params.mu, hist_params.sigs_popt)
    gnc = gaussianNoiseCalculator(h5_file, params)
    gnc.backengine()
    gnc_data = gnc.data
    if __name__ == "__main__":
        gnc_data.plotPattern(0, logscale=True)
    return gnc


@pytest.fixture()
def gnc():
    return getGNC()


def test_gaussianNoiseCalculator_save_error(gnc):
    with pytest.raises(TypeError) as excinfo:
        gnc.saveH5()
    assert "Unrecognized output_path" in str(excinfo.value)


def test_gaussianNoiseCalculator_save(gnc, tmp_path):
    data_fn = str(tmp_path / "photons.h5")
    gnc.output_path = data_fn
    gnc.saveH5()
    assert h5py.is_hdf5(data_fn) is True


def test_gaussianNoiseCalculator_save_EMC(gnc, tmp_path):
    data_fn = str(tmp_path / "photons.emc")
    gnc.output_path = data_fn
    gnc.saveEMC()


if __name__ == "__main__":
    getGNC()
