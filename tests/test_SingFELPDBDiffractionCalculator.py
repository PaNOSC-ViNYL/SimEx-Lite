from SimExLite.DiffractionCalculators import SingFELPDBDiffractionCalculator
from SimExLite.PhotonBeamData import SimpleBeam
from SimExLite import DataCollection


def test_construct_calculator(tmpdir):
    """Test to construct the calculator class."""
    beam_data = SimpleBeam(
        photons_per_pulse=4e12, photon_energy=6000, beam_size=[228e-9, 228e-9]
    )
    diffraction = SingFELPDBDiffractionCalculator(
        name="SingFELPDBDiffractionCalculator",
        input=DataCollection(beam_data),
        sample="testFiles/2nip.pdb",
        instrument_base_dir=str(tmpdir),
    )
    print(diffraction.parameters)


def test_run(tmpdir):
    """Test to construct the calculator class."""
    beam_data = SimpleBeam(
        photons_per_pulse=4e12, photon_energy=6000, beam_size=[228e-9, 228e-9]
    )
    diffraction = SingFELPDBDiffractionCalculator(
        name="SingFELPDBDiffractionCalculator",
        input=DataCollection(beam_data),
        sample="testFiles/2nip.pdb",
        instrument_base_dir=str(tmpdir),
    )
    output = diffraction.backengine()
    assert "img_array" in output.get_data()


if __name__ == "__main__":
    # test_construct_calculator("SingFELPDBDiffractionCalculator_tt")
    test_run("SingFELPDBDiffractionCalculator_tt")
