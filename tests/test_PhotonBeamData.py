"""Test PhotonBeamData"""

import pytest
from SimExLite.PhotonBeamData import BeamBase

SB = BeamBase(photon_energy=8.05e3,
                pulse_energy=1.04e-3,
                focus=15,
                focus_unit='um',
                flux_unit='1/angstrom**2')


def test_construct():
    assert pytest.approx(SB.wavelength.to('angstrom').to_tuple()[0],
                         0.01) == 1.54
    assert pytest.approx(SB.photons_per_pulse.to_tuple()[0], 0.01) == 8.1e11
    assert pytest.approx(SB.fluence.to('J/cm**2').to_tuple()[0], 0.01) == 4.6e2
