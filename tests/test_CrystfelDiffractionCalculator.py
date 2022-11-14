"""Test SimpleScatteringPMICalculator"""

import pytest
from pathlib import Path

from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.DiffractionCalculators import CrystfelDiffractionCalculator

# Lysozyme
sample_data = SampleData.from_file("./testFiles/3WUL.pdb", ASEFormat, "test_sample")


def test_construct_calculator(tmpdir):
    """Test to construct the calculator class."""
    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=None,
        instrument_base_dir=str(tmpdir),
    )


def test_construct_calculator_run_with_intensities_fn(tmpdir):
    """Test to construct the calculator class."""
    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=sample_data,
        instrument_base_dir=str(tmpdir),
    )
    # Lysozyme
    diffraction.parameters["point_group"] = "422"
    diffraction.parameters["intensities_fn"] = "./testFiles/3WUL.pdb.hkl"
    print(diffraction.parameters)
    diffraction.backengine()


if __name__ == "__main__":
    test_construct_calculator_run_with_intensities_fn(Path("./"))
