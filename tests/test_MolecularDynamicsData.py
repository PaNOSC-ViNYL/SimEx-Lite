"""Test MolecularDynamicsData"""

from SimExLite.MolecularDynamicsData import MolecularDynamicsData


def testXMDYNData():
    MDD = MolecularDynamicsData("./pmi_out_test.h5")
    assert MDD.file_format == "XMDYN"
