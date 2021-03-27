"""Test DiffractionData"""

from SimExLite.DiffractionData import getDataType, DiffractionData
import numpy as np
import pytest


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


def test_incomplete_construction():
    with pytest.raises(ValueError) as excinfo:
        DiffractionData()
    assert "Need least one `arr` or `input_file`" in str(excinfo.value)


if __name__ == "__main__":
    test_getDataType()
    test_incomplete_construction()
