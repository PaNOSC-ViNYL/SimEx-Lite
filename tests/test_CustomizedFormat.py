"""Test CustomizedFormat"""

import h5py
from SimExLite.DiffractionData import DiffractionData, CustomizedFormat


def test_print_format_keys(capsys):
    DiffractionData.list_formats()
    captured = capsys.readouterr()
    assert "customized" in captured.out


def test_read():
    h5_file = "./testFiles/customized.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CustomizedFormat, key="test_Customized"
    )
    assert isinstance(dd, DiffractionData) is True


def test_get_data():
    h5_file = "./testFiles/customized.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CustomizedFormat, key="test_Customized"
    )
    data_dict = dd.get_data()
    assert len(data_dict["img_array"]) == 5


def test_write_data(tmpdir):
    h5_file = "./testFiles/customized.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CustomizedFormat, key="test_Customized"
    )
    data_dict = dd.get_data()
    dd_dict = DiffractionData.from_dict(data_dict, "dd_dict")
    out_fn = str(tmpdir / "test_Customized.h5")
    dd_dict.write(out_fn, CustomizedFormat, "test_file")
    with h5py.File(out_fn, "r") as h5:
        assert h5["patterns"].shape == (5, 513, 513)


def test_write_in_emc(tmpdir):
    h5_file = "./testFiles/customized.h5"
    dd = DiffractionData.from_file(
        h5_file, format_class=CustomizedFormat, key="test_Customized"
    )
    data_dict = dd.get_data()
    dd_dict = DiffractionData.from_dict(data_dict, "dd_dict")
    out_fn = str(tmpdir / "test_Customized.h5")
    dd_dict.write(out_fn, CustomizedFormat, "test_file")
    with h5py.File(out_fn, "r") as h5:
        assert h5["patterns"].shape == (5, 513, 513)


def test_write_emc_geom(tmpdir):
    h5_file = "./testFiles/customized.h5"
    out_fn = str(tmpdir / "customized_to_emc_geom.h5")
    CustomizedFormat.to_emc_geom(h5_file, out_fn, 10)
    with h5py.File(out_fn, "r") as h5:
        assert set(["qx", "qy", "qz"]) <= set(list(h5))
