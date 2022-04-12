"""Test MolecularDynamicsData"""

import numpy as np
import pytest
from SimExLite.SampleData import SampleData, ASEFormat
from ase.io import read, write


@pytest.fixture(scope="session")
def tmp_data():
    data_dict = {}
    # 2 atoms
    positions = np.empty((2, 3))
    positions[0] = np.array([8, 18, -3.54])
    positions[1] = np.array([9, 18.2, -3.1])
    data_dict["positions"] = positions
    data_dict["atomic_numbers"] = np.array([8, 6])
    return data_dict


def test_create_from_dict(tmp_data):
    """Test creating a SampleData from data_dict"""
    SD = SampleData.from_dict(tmp_data, key="tmp_data")
    data_dict = SD.get_data()
    # print(data_dict)
    # print(tmp_data)
    assert data_dict == tmp_data


@pytest.fixture(scope="session")
def SD_pdb(tmp_data, tmp_path_factory):
    """Test writing a pdb file from the data class"""
    SD = SampleData.from_dict(tmp_data, key="tmp_data")
    fn = tmp_path_factory.mktemp("data") / "atoms.pdb"
    SD_pdb = SD.write(str(fn), ASEFormat)
    atoms = read(fn)
    assert (SD_pdb.get_data()["positions"] == atoms.positions).all()
    return SD_pdb


def test_create_from_file(SD_pdb, tmp_data):
    """Test creating a SampleData from a file"""
    filename = SD_pdb.filename
    SD = SampleData.from_file(filename, ASEFormat, key="tmp_data")
    data_dict = SD.get_data()
    assert SD.mapping_type == ASEFormat
    # print(data_dict)
    # print(tmp_data)
    assert np.all(data_dict["positions"] == tmp_data["positions"])
    assert np.all(data_dict["atomic_numbers"] == tmp_data["atomic_numbers"])
