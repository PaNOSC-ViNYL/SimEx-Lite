"""Test MolecularDynamicsData"""

import pytest
from SimExLite.PMIData import PMIData, XMDYNFormat


def test_create_from_file():
    """Test creating a data from a file"""
    testfile = "./testFiles/PMI.h5"
    PD = PMIData.from_file(testfile, XMDYNFormat, key="XMDYN_data")
    data_dict = PD.get_data()
    assert "angle", "0" in data_dict.keys()
