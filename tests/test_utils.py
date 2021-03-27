"""Test DiffractionData"""

from SimExLite.utils import isLegacySimExH5
import h5py


def test_isLegacySimExH5(tmp_path):
    tmp_h5 = str(tmp_path / 'tmp.h5')
    with h5py.File(tmp_h5, 'w') as h5:
        h5.create_group('test_g')
    assert isLegacySimExH5(tmp_h5) is False
