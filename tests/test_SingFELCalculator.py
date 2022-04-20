"""Test SimpleScatteringPMICalculator"""

import pytest
from pathlib import Path
from extra_geom.base import DetectorGeometryBase

from SimExLite import DataCollection
from SimExLite.PMIData import PMIData, XMDYNFormat
from SimExLite.DiffractionCalculators import SingFELCalculator


def test_construct_calculator(tmpdir):
    """Test to construct the calculator class."""
    input_data = PMIData.from_file("./testFiles/PMI.h5", XMDYNFormat, "PMI_data")
    diffraction = SingFELCalculator(
        name="SingFELCalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    print(diffraction.parameters)


def test_run_backengine(tmpdir):
    """Test to run the calculator backengine"""
    input_data = PMIData.from_file("./testFiles/PMI.h5", XMDYNFormat, "PMI_data")
    diffraction = SingFELCalculator(
        name="SingFELCalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    # Test it in a serial mode
    diffraction.parameters["mpi_command"] = ""
    output = diffraction.backengine()
    assert isinstance(output.get_data()["geom"], DetectorGeometryBase)
    assert "img_array" in output.get_data()


if __name__ == "__main__":
    test_run_backengine(Path("./"))
