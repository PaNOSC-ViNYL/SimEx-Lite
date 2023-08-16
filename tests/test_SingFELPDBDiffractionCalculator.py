"""Test SingFELPDBDiffractionCalculator"""
import pytest
import os

pytestmark = pytest.mark.skipif(
    "TRAVIS" in os.environ, reason="Test skipped on Travis CI"
)
from SimExLite.DiffractionCalculators import SingFELPDBDiffractionCalculator
from SimExLite.PhotonBeamData import SimpleBeam
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite import DataCollection


def test_construct_calculator(tmpdir):
    """Test to construct the calculator class."""
    beam_data = SimpleBeam(
        photons_per_pulse=4e12, photon_energy=6000, beam_size=[228e-9, 228e-9]
    )
    sample_data = SampleData.from_file("testFiles/2nip.pdb", ASEFormat, "sample")
    diffraction = SingFELPDBDiffractionCalculator(
        name="SingFELPDBDiffractionCalculator",
        input=DataCollection(beam_data, sample_data),
        instrument_base_dir=str(tmpdir),
    )
    print(diffraction.parameters)


def test_run(tmpdir):
    """Test to construct the calculator class."""
    beam_data = SimpleBeam(
        photons_per_pulse=4e12, photon_energy=6000, beam_size=[228e-9, 228e-9]
    )
    sample_data = SampleData.from_file("testFiles/2nip.pdb", ASEFormat, "sample")
    diffraction = SingFELPDBDiffractionCalculator(
        name="SingFELPDBDiffractionCalculator",
        input=DataCollection(beam_data, sample_data),
        instrument_base_dir=str(tmpdir),
    )
    diffraction.parameters["pixels_x"] = 10
    diffraction.parameters["pixels_y"] = 5
    diffraction.parameters["pixel_size"] = 200e-6
    print(diffraction.parameters)
    output = diffraction.backengine()
    assert "img_array" in output.get_data()


def test_run_bin(tmpdir):
    """Test to construct the calculator class."""
    beam_data = SimpleBeam(
        photons_per_pulse=4e12, photon_energy=6000, beam_size=[228e-9, 228e-9]
    )
    sample_data = SampleData.from_file("testFiles/2nip.pdb", ASEFormat, "sample")
    diffraction = SingFELPDBDiffractionCalculator(
        name="SingFELPDBDiffractionCalculator",
        input=DataCollection(beam_data, sample_data),
        instrument_base_dir=str(tmpdir),
    )
    diffraction.parameters["number_of_diffraction_patterns"] = 2
    diffraction.parameters["pixels_x"] = 10
    diffraction.parameters["pixels_y"] = 5
    diffraction.parameters["pixel_size"] = 400e-6
    print(diffraction.parameters)
    output = diffraction.backengine()
    assert "img_array" in output.get_data()


if __name__ == "__main__":
    # test_construct_calculator("SingFELPDBDiffractionCalculator_tt")
    # test_run("SingFELPDBDiffractionCalculator_tt")
    test_run_bin("SingFELPDBDiffractionCalculator_bin2")
