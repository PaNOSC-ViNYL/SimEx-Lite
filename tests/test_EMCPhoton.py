# a""Test EMCPhoton"""

import pytest
import SimExLite.DiffractionData.EMCPhoton as EMC
import SimExLite.DiffractionData as DD
from SimExLite.DiffractionData import DiffractionData

# def test_EMC_geometry(tmp_path):
#     diffr_path = './testFiles/singfel-multi.h5'
#     diffr = DiffractionData()
#     diffr.read(diffr_path)
#     diffr.createArray()
#     out_path = tmp_path / "t.bin"
#     diffr.multiply(1e5)
#     data_fn = str(out_path)
#     geom_path = out_path.with_suffix('.geom')
#     diffr.saveAs('emc', data_fn, with_geom=True)
#     assert out_path.is_file() is True
#     assert geom_path.is_file() is True


def test_pattern_shape_miss():
    diffr_path = './testFiles/h5_multi.emc'
    with pytest.raises(TypeError) as excinfo:
        EMC.read(diffr_path)
        assert "missing 'pattern_shape' argument." in excinfo


def test_write_single(tmp_path):
    diffr_path = './testFiles/singfel.h5'
    out_path = tmp_path / "t.emc"
    diffr = DD.read(diffr_path)
    EMC.write(str(out_path), diffr)


def test_write_multi(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    out_path = tmp_path / "t.emc"
    diffr = DD.read(diffr_path)
    EMC.write(str(out_path), diffr)


def test_read_single():
    diffr_path = './testFiles/h5.emc'
    pattern_shape = [81, 81]
    diffr = EMC.read(diffr_path, pattern_shape=pattern_shape)
    assert isinstance(diffr, DiffractionData) is True
    assert len(diffr.array) == 1


def test_read_multi():
    diffr_path = './testFiles/h5_multi.emc'
    pattern_shape = [81, 81]
    diffr = EMC.read(diffr_path, pattern_shape=pattern_shape)
    assert isinstance(diffr, DiffractionData) is True
    assert len(diffr.array) == 13


if __name__ == "__main__":
    pass
