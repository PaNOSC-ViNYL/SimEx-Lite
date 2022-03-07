"""Test MolecularDynamicsData"""

import h5py
import numpy as np
import pytest
from SimExLite.PMIData import PMIData, XMDYNFormat


def test_create_from_file():
    """Test creating a data from a file"""
    testfile = "/beegfs/desy/user/mstran/simS2E/singl_nowater/pmi/pmi_out_1.h5"
    PD = PMIData.from_file(testfile, XMDYNFormat, key="XMDYN_data")
    data_dict = PD.get_data()
    print(data_dict)
