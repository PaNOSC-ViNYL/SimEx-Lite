"""Test DiffractionData"""

from SimExLite.utils import isLegacySimExH5
import SimExLite.utils as utils
import h5py
import numpy as np


def test_isLegacySimExH5(tmp_path):
    tmp_h5 = str(tmp_path / 'tmp.h5')
    with h5py.File(tmp_h5, 'w') as h5:
        h5.create_group('test_g')
    assert isLegacySimExH5(tmp_h5) is False


def test_IO_SimpleH5(tmp_path):
    tmp_h5 = str(tmp_path / 'tmp.h5')
    tmpdata = np.random.rand(10, 10)
    utils.saveSimpleH5(tmpdata, tmp_h5)
    assert h5py.is_hdf5(tmp_h5) is True
    load_data = utils.loadSimpleH5(tmp_h5)
    assert np.array_equal(tmpdata, load_data) is True
