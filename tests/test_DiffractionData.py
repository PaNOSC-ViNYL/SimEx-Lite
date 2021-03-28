"""Test DiffractionData"""

import numpy as np
import pytest
import h5py
from SimExLite.DiffractionData import getDataType, DiffractionData, histogramParams


def test_getDataType():
    h5_file = './testFiles/singfel.h5'
    assert getDataType(h5_file) == '1'


def test_file_not_exists():
    h5_file = './testFiles/xx.h5'
    with pytest.raises(FileNotFoundError):
        DiffractionData(h5_file)


def test_readSingFEL():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DiffractionData(h5_file)
    dd.getArray()
    assert len(dd.array) == 13


def test_saveAs_unsupported(tmp_path):
    input_arr = np.random.rand(10, 10)
    dd = DiffractionData('test.h5', arr=input_arr)
    with pytest.raises(TypeError) as excinfo:
        dd.saveAs(data_format="blahblah", file_name="blabla")
        print(excinfo.value)
    assert "Unsupported format" in str(excinfo.value)


def test_saveAs_emc(tmp_path):
    input_arr = [np.random.rand(10, 10)]
    dd = DiffractionData(arr=input_arr)
    data_fn = str(tmp_path / "photons.emc")
    dd.saveAs('emc', data_fn)


def test_simple(tmp_path):
    input_arr = [np.random.rand(10, 10)]
    dd = DiffractionData(arr=input_arr)
    data_fn = str(tmp_path / "photons.h5")
    dd.saveAs('simple', data_fn)
    assert h5py.is_hdf5(data_fn) is True


def test_incomplete_construction():
    with pytest.raises(ValueError) as excinfo:
        DiffractionData()
    assert "Need least one `arr` or `input_file`" in str(excinfo.value)


def test_addGaussianNoise(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    dd = DiffractionData(h5_file)
    dd.getArray()
    xcs = np.array([-1.845, 56.825, 114.623])
    fwhms = np.array([20.687, 26.771, 29.232])
    hist_params = histogramParams(xcs, fwhms)
    dd.addGaussianNoise(hist_params.mu, hist_params.sigs_popt)
    out_path = tmp_path / "fitting.png"
    fn = str(out_path)
    hist_params.plotFitting(fn)
    assert out_path.is_file() is True


def test_addBeamStop():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DiffractionData(h5_file)
    dd.getArray()
    dd.addBeamStop(3)


if __name__ == "__main__":
    test_getDataType()
    test_incomplete_construction()
    test_addBeamStop()
