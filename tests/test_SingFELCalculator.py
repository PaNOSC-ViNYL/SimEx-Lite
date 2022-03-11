"""Test SimpleScatteringPMICalculator"""

import pytest
from pathlib import Path

from SimExLite import DataCollection
from SimExLite.PMIData import PMIData, XMDYNFormat
from SimExLite.DiffractionCalculators import SingFELCalculator


def test_construct_calculator(tmpdir):
    input_data = PMIData.from_file("./testFiles/PMI.h5", XMDYNFormat, "PMI_data")
    diffraction = SingFELCalculator(
        name="SingFELCalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    print(diffraction.parameters)


def test_run_backengine(tmpdir):
    input_data = PMIData.from_file("./testFiles/PMI.h5", XMDYNFormat, "PMI_data")
    diffraction = SingFELCalculator(
        name="SingFELCalculator",
        input=input_data,
        instrument_base_dir=str(tmpdir),
    )
    diffraction.parameters["mpi_command"] = ""
    output = diffraction.backengine()
    print(output.get_data())


if __name__ == "__main__":
    test_run_backengine(Path("./"))