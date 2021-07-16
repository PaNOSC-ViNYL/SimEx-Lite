"""Test PhotonBeamData"""

import pytest
from SimExLite.PhotonBeamData import BeamBase

SB = BeamBase(photon_energy=8.05e3,
                pulse_energy=1.04e-3)
SB.set_focus_area(15*15, unit='um**2')


def test_construct():
    assert pytest.approx(SB.get_wavelength().to('angstrom').to_tuple()[0],
                         0.01) == 1.54
    assert pytest.approx(SB.get_photons_per_pulse().to_tuple()[0], 0.01) == 8.1e11
    assert pytest.approx(SB.get_fluence().to('J/cm**2').to_tuple()[0], 0.01) == 4.6e2

if __name__ == "__main__":
    print(SB.attrs)
    SB.showAttrs()
    print('{:.3~P}'.format(SB.get_fluence()))