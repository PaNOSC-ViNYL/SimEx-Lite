"""Test CondorFormat"""

import h5py
from SimExLite.DiffractionData import DiffractionData, CondorFormat


def test_print_format_keys(capsys):
    DiffractionData.list_formats()
    captured = capsys.readouterr()
    assert "condor" in captured.out


def test_read():
    h5_file = "./testFiles/condor.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CondorFormat, key="test_Condor"
    )
    assert isinstance(dd, DiffractionData) is True


def test_get_data():
    h5_file = "./testFiles/condor.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CondorFormat, key="test_Condor"
    )
    data_dict = dd.get_data()
    assert len(data_dict["img_array"]) == 5


def test_write_data(tmpdir):
    h5_file = "./testFiles/condor.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CondorFormat, key="test_Condor"
    )
    data_dict = dd.get_data()
    dd_dict = DiffractionData.from_dict(data_dict, "dd_dict")
    out_fn = str(tmpdir / "test_Condor.h5")
    dd_dict.write(out_fn, CondorFormat, "test_file")
    with h5py.File(out_fn, "r") as h5:
        assert h5["patterns"].shape == (5, 513, 513)


def test_write_in_emc(tmpdir):
    h5_file = "./testFiles/condor.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CondorFormat, key="test_Condor"
    )
    data_dict = dd.get_data()
    dd_dict = DiffractionData.from_dict(data_dict, "dd_dict")
    out_fn = str(tmpdir / "test_Condor.h5")
    dd_dict.write(out_fn, CondorFormat, "test_file")
    with h5py.File(out_fn, "r") as h5:
        assert h5["patterns"].shape == (5, 513, 513)


def test_write_emc_geom(tmpdir):
    h5_file = "./testFiles/condor.h5"
    out_fn = str(tmpdir / "condor_to_emc_geom.h5")
    CondorFormat.to_emc_geom(h5_file, out_fn, 10)
    with h5py.File(out_fn, "r") as h5:
        assert set(["qx", "qy", "qz"]) <= set(list(h5))
