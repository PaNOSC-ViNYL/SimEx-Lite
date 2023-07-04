"""Test SimpleScatteringPMICalculator"""

import pytest
import os
pytestmark = pytest.mark.skipif('TRAVIS' in os.environ, reason='Test skipped on Travis CI')

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


# @pytest.mark.skip(reason="Waiting for converting simple geom")
# def test_construct_calculator_run_with_simple_geom_fn(tmpdir):
#     """Test to construct the calculator class with simple geometry file."""
#     diffraction = CrystfelDiffractionCalculator(
#         name="CrystfelCalculator",
#         input=sample_data,
#         instrument_base_dir=str(tmpdir),
#     )
#     # Lysozyme
#     diffraction.parameters["point_group"] = "422"
#     diffraction.parameters["intensities_fn"] = "./testFiles/3WUL.pdb.hkl"
#     diffraction.parameters["geometry_fn"] = "./testFiles/simple_crystfel.geom"
#     print(diffraction.parameters)
#     diffraction.backengine()


def test_construct_calculator_run_with_intensities_fn(tmpdir):
    """Test to construct the calculator class with calculated intensities file."""
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


def test_construct_calculator_run_without_intensities_fn(tmpdir):
    """Test to run simulation without intensities files"""
    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=sample_data,
        instrument_base_dir=str(tmpdir),
    )
    # Lysozyme
    diffraction.parameters["point_group"] = "422"
    diffraction.parameters["geometry_fn"] = "./testFiles/simple_crystfel.geom"
    print(diffraction.parameters)
    with pytest.raises(KeyError) as exc_info:
        diffraction.backengine(is_convert_to_cxi=False)
    assert "Intensity information is not provided" in str(exc_info.value)


def test_intensities_space_group_same_time(tmpdir):
    """Test to construct the calculator class."""
    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=sample_data,
        instrument_base_dir=str(tmpdir),
    )
    # Lysozyme
    diffraction.parameters["point_group"] = "422"
    diffraction.parameters["space_group"] = "P43212"
    diffraction.parameters["intensities_fn"] = "./testFiles/3WUL.pdb.hkl"
    diffraction.parameters["geometry_fn"] = "./testFiles/simple_crystfel.geom"
    print(diffraction.parameters)
    with pytest.raises(KeyError) as exc_info:
        diffraction.backengine(is_convert_to_cxi=False)
    assert "intensities_fn" in str(exc_info.value)


def test_intensities_space_group(tmpdir):
    """Test to construct the calculator class."""
    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=sample_data,
        instrument_base_dir=str(tmpdir),
    )
    # Lysozyme
    diffraction.parameters["point_group"] = "422"
    diffraction.parameters["space_group"] = "P43212"
    diffraction.parameters["geometry_fn"] = "./testFiles/simple_crystfel.geom"
    print(diffraction.parameters)
    diffraction.backengine(is_convert_to_cxi=False)


if __name__ == "__main__":
    # test_construct_calculator_run_with_intensities_fn(Path("./"))
    # test_construct_calculator_run_with_simple_geom_fn(Path("./"))
    test_intensities_space_group(Path("./"))
