"""Test DetectorCalculators"""

import pytest
import numpy as np
import h5py
from SimExLite.DiffractionData import histogramParams
from SimExLite.DetectorCalculators import GaussianNoiseCalculator, GaussianNoisePrameters
import matplotlib.pyplot as plt
from SimExLite.utils.io import UnknownFileTypeError


def getGNC():
    h5_file = './testFiles/singfel-multi.h5'
    xcs = np.array([-1.845, 56.825, 114.623])
    fwhms = np.array([20.687, 26.771, 29.232])
    hist_params = histogramParams(xcs, fwhms)
    params = GaussianNoisePrameters(hist_params.mu, hist_params.sigs_popt)
    gnc = GaussianNoiseCalculator(h5_file, params)
    gnc.backengine()
    gnc_data = gnc.data
    gnc_data.plotPattern(0, logscale=True)
    return gnc


@pytest.fixture()
def gnc():
    return getGNC()


def test_GaussianNoiseCalculator_save(gnc, tmp_path):
    data_fn = str(tmp_path / "photons.h5")
    gnc.output_path = data_fn
    gnc.data.plotPattern(0)
    gnc.saveH5()
    assert h5py.is_hdf5(data_fn) is True


def test_GaussianNoiseCalculator_save_singfel(gnc, tmp_path):
    data_fn = str(tmp_path / "photons.h5")
    gnc.output_path = data_fn
    gnc.saveH5('singfel')
    assert h5py.is_hdf5(data_fn) is True


def test_GaussianNoiseCalculator_save_unknown(gnc, tmp_path):
    data_fn = str(tmp_path / "photons.h5")
    gnc.output_path = data_fn
    with pytest.raises(UnknownFileTypeError):
        gnc.saveH5('test')


if __name__ == "__main__":
    getGNC()
    plt.show()
