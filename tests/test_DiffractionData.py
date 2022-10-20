"""Test DiffractionData"""

from SimExLite.DiffractionData import DiffractionData, SingFELFormat, EMCFormat


def test_print_format_keys():
    DiffractionData.list_formats()


def test_read():
    h5_file = "./testFiles/singfel.h5"
    DiffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    assert isinstance(DiffrData, DiffractionData) is True


def test_readSingFEL():
    h5_file = "./testFiles/singfel-multi.h5"
    DiffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    data_dict = DiffrData.get_data()
    assert len(data_dict["img_array"]) == 13


def test_writeSingFEL(tmp_path):
    h5_file = "./testFiles/singfel-multi.h5"
    DiffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    ofn = str(tmp_path / "rewrite_singfel.h5")
    DiffrData.write(
        ofn,
        SingFELFormat,
    )


def test_readSingFELwriteEMC(tmp_path):
    h5_file = "./testFiles/singfel-multi.h5"
    DiffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    ofn = str(tmp_path / "EMC.h5")
    DiffrData.write(
        ofn,
        EMCFormat,
    )


def test_readEMC(tmp_path):
    h5_file = "./testFiles/singfel-multi.h5"
    DiffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    ofn = str(tmp_path / "EMC.h5")
    DiffrData.write(
        ofn,
        EMCFormat,
    )
    EMCData = DiffractionData.from_file(
        ofn, EMCFormat, pattern_shape=(81, 81), key="test_EMC"
    )
    data_dict = EMCData.get_data()
    assert data_dict["img_array"].shape == (13, 81, 81)
