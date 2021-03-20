"""Test MolecularDynamicsData"""

from SimExLite.MolecularDynamicsData import MolecularDynamicsData
import h5py


def test_XMDYNData():
    MDD = MolecularDynamicsData("./testFiles/pmi_out_test.h5")
    assert MDD.file_format == "XMDYN"


def test_UnknownData(tmp_path):
    tmp_h5 = str(tmp_path / 'tmp.h5')
    with h5py.File(tmp_h5, 'w') as h5:
        h5.create_group('test_g')
    MDD = MolecularDynamicsData(tmp_h5)
    assert MDD.file_format == "UNKNOWN"
