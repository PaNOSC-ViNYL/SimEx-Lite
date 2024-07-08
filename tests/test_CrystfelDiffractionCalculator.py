"""Test CrystfelDiffractionCalculator"""

import pytest
import os
import shutil

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
pytestmark = pytest.mark.skipif(
    ("TRAVIS" in os.environ or IN_GITHUB_ACTIONS),
    reason="Test skipped on Travis CI or GITHUB_ACTIONS",
)

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
    diffraction.parameters["geometry_fn"] = "./testFiles/simple_crystfel.geom"
    diffraction.parameters["point_group"] = "422"
    diffraction.parameters["intensities_fn"] = "./testFiles/3WUL.pdb.hkl"
    print(diffraction.parameters)
    diffraction.backengine()


def test_geometry_override(tmpdir):
    geom_fn_src = "./testFiles/simple_crystfel.geom"
    geom_fn_tmp = str(tmpdir / "tmp.geom")
    shutil.copy(geom_fn_src, geom_fn_tmp)

    diffraction = CrystfelDiffractionCalculator(
        name="CrystfelCalculator",
        input=sample_data,
        instrument_base_dir=str(tmpdir),
    )

    diffraction.parameters["geometry_fn"].value = geom_fn_tmp
    diffraction.parameters["photon_energy"].value = 13000
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
