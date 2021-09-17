# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Photon Beam data APIs"""

import numpy as np
from numpy import ndarray
from . import setValue


def hcDivide(val):
    """h is the Plank constant and c is the speed of light. keV <-> Angstrom."""
    return 12.398 / val


class BeamBase:
    """The simplest description of a pulse of the beam.

    :param pulse_energy: The energy of the X-ray pulse in Joule.
    :type pulse_energy: float, optional
    :param photons_per_pulse: The number of photons of this pulse.
    :type photons_per_pulse: int, optional
    :param wavelength: The wavelength of this pulse in Angstrom.
    :type wavelength: float, optional
    :param photon_energy: The photon energy of this pulse, in eV.
    :type photon_energy: float, optional
    :param focus_area: The focus area of this pulse, in m**2.
    :type focus_area: float, optional
    """
    def __init__(self, pulse_energy=None, wavelength=None, focus_area=None):

        # Default photon energy unit
        self._attrs = {}

        if wavelength is not None:
            self.set_wavelength(wavelength)
        if pulse_energy:
            self.set_pulse_energy(pulse_energy)
        if focus_area:
            self.set_focus_area(focus_area)

    def set_focus_area(self, val, unit='m**2'):
        focus_area = setValue(val, unit)
        self._attrs['focus_area'] = focus_area.to('m**2')

    def set_pulse_energy(self, val, unit='joule'):
        pulse_energy = setValue(val, unit)
        self._attrs['pulse_energy'] = pulse_energy.to('joule')

    def set_wavelength(self, val, unit='angstrom'):
        wavelength = setValue(val, unit)
        self._attrs['wavelength'] = wavelength.to('angstrom')

    def get_focus_area(self, unit='m**2'):
        return self._attrs['focus_area'].to(unit)

    def get_pulse_energy(self, unit='joule'):
        return self._attrs['pulse_energy'].to(unit)

    @property
    def pulse_energy(self):
        """The pulse_energy property."""
        return self.get_pulse_energy().magnitude

    @pulse_energy.setter
    def pulse_energy(self, value):
        self.set_pulse_energy(value)

    def get_wavelength(self, unit='angstrom'):
        return self._attrs['wavelength'].to(unit)

    # This is to be compatile with the attribute access way.
    @property
    def wavelength(self):
        """The wavelength property."""
        return self.get_wavelength().magnitude

    @wavelength.setter
    def wavelength(self, value):
        self.set_wavelength(value)

    def get_photons_per_pulse(self):
        return self._attrs['pulse_energy'].to(
            'joule') / self.get_photon_energy().to('joule')

    def get_photon_energy(self, unit='eV'):
        photon_energy = setValue(
            hcDivide(self._attrs['wavelength'].to('angstrom').magnitude),
            'keV')
        return photon_energy.to(unit)

    def get_fluence(self, unit='joule/cm**2'):
        fluence = self.get_pulse_energy() / self.get_focus_area()
        return fluence.to(unit)

    def get_flux(self, unit='1/um**2'):
        flux = self.get_photons_per_pulse() / self.get_focus_area()
        return flux.to(unit)

    @property
    def attrs(self):
        my_attrs = {}
        for key in self._attrs.keys():
            try:
                my_attrs[key] = self._attrs[key].magnitude
            except AttributeError:
                my_attrs[key] = self._attrs[key]
        return my_attrs

    def showAttrs(self):
        # for key, value in self._attrs.items():
        #     try:
        #         print('{} = {:.3~P}'.format(key, value))
        #     except ValueError:
        #         print('{} = {}'.format(key, value))
        print(self.__repr__)

    def __repr__(self):
        """
        Returns string with all the parameters
        """
        string = "Beam parameters:\n"
        for key, value in self._attrs.items():
            try:
                string += '{} = {:.3~P}\n'.format(key, value)
            except ValueError:
                string += '{} = {}\n'.format(key, value)
        return string


class SimpleBeam(BeamBase):
    """The simplest description of a pulse of the beam.

    :param pulse_energy: The energy of the X-ray pulse in Joule.
    :type pulse_energy: float, optional
    :param photons_per_pulse: The number of photons of this pulse.
    :type photons_per_pulse: int, optional
    :param wavelength: The wavelength(s) of this pulse in Angstrom.
        Monchromatic beam: a scalar wavelength.
        Polychromatic beam (shot-to-shot-invariant):
            an array of length **m** of wavelengths.
        Polychromatic beam (shot-to-shot-variant):
            an array of **np** by **m** of wavelengths.
    :type wavelength: float or ndarray, optional
    :param wavelength_weights: The relative weights of the corresponding wavelengths.
        Monchromatic beam: None
        Polychromatic beam (shot-to-shot-invariant):
            an array of length **m** of wavelengths.
        Polychromatic beam (shot-to-shot-variant):
            an array of **np** by **m** of wavelengths.
    :type wavelength_weights: ndarray, optional
    :param photon_energy: The photon energy(s) of this pulse, in eV.
        Monchromatic beam: a scalar.
        Polychromatic beam (shot-to-shot-invariant):
            an array of length **m** of photon energies.
        Polychromatic beam (shot-to-shot-variant):
            an array of **np** by **m** of photon energies.
    :type photon_energy: float of ndarray, optional
    :param photon_energy_weights: The relative weights of the corresponding photon energies.
        Monchromatic beam: None
        Polychromatic beam (shot-to-shot-invariant):
            an array of length **m** of photon energies.
        Polychromatic beam (shot-to-shot-variant):
            an array of **np** by **m** of photon energies.
    :type photon_energy_weights: ndarray, optional
    :param beam_size: Two-element array/list of FWHM (if Gaussian or Airy function) or diameters (if top hat)
        or widths (if rectangular) of the beam in the order x, y. The unit is meter.
    :type beam_size: array-like, optional
    :param profile: The beam profile. It can be one of: gaussian|airy|top-hat|rectangular.
    :type profile: str, optional
    :param focus_area: The focus area of this pulse, in m**2. It will be overridden by beam_size if both are
        provided.
    :type focus_area: float, optional
    """
    def __init__(self,
                 pulse_energy=None,
                 photons_per_pulse=None,
                 wavelength=None,
                 wavelength_weights=None,
                 photon_energy=None,
                 photon_energy_weights=None,
                 beam_size: ndarray = None,
                 profile: str = 'gaussian',
                 focus_area=None):
        super().__init__(pulse_energy, wavelength, focus_area)
        if wavelength is not None and photon_energy is not None:
            raise ValueError(
                'wavelength and photon_energy can not be set at the same time.'
            )
        if pulse_energy and photons_per_pulse:
            raise ValueError(
                'pulse_energy and photons_per_pulse can not be set at the same time.'
            )
        if wavelength_weights is not None and photon_energy_weights is not None:
            raise ValueError(
                'wavelength_weights and photon_energy_weights can not be set at the same time.'
            )
        if wavelength_weights is not None:
            self.set_wavelength_weights(wavelength_weights)
        if photon_energy is not None:
            self.set_photon_energy(photon_energy)
        if photon_energy_weights is not None:
            self.set_photon_energy_weights(photon_energy_weights)
        if photons_per_pulse:
            self.set_photons_per_pulse(photons_per_pulse)
        if profile:
            self.set_profile(profile)
        if beam_size:
            self.set_beam_size(beam_size)

    def set_wavelength_weights(self, val):
        self._attrs['wavelength_weights'] = setValue(val, '')

    def get_wavelength_weights(self):
        return self._attrs['wavelength_weights']

    def set_photon_energy(self, val, unit='eV'):
        photon_energy = setValue(val, unit)
        # Convert to wavelength
        self._attrs['wavelength'] = setValue(
            hcDivide(photon_energy.to('keV').magnitude), 'angstrom')

    def set_photon_energy_weights(self, val):
        # Convert to wavelength
        self._attrs['wavelength_weights'] = setValue(val, '')

    def get_photon_energy_weights(self):
        # Convert to wavelength
        return self.get_wavelength_weights()

    def set_photons_per_pulse(self, val):
        pulse_energy = val * self.get_photon_energy()
        self._attrs['pulse_energy'] = setValue(pulse_energy, 'joule')

    def set_profile(self, val):
        if not isinstance(val, str):
            raise TypeError("profile should be in str type.")
        if val in ['gaussian', 'airy', 'top-hat', 'rectangular']:
            self._attrs['profile'] = val
        else:
            raise ValueError(
                "profile should be one of: gaussian|airy|top-hat|rectangular")

    def get_profile(self):
        return self._attrs['profile']

    def set_beam_size(self, val, unit='m'):
        if not isinstance(val, (list, np.array)):
            raise TypeError(
                "beamsize should be a list or numpy array of [x, y]")
        if len(val) != 2:
            raise TypeError(
                "beamsize should be a list or numpy array of [x, y]")
        beam_size = setValue(val, unit)
        self._attrs['beam_size'] = beam_size.to('m')
        profile = self.get_profile()
        # This will override focus_area
        if profile in ['gaussian', 'airy', 'top-hat']:
            focus = beam_size[0] * beam_size[1] * np.pi / 4
        elif profile == 'rectangular':
            focus = beam_size[0] * beam_size[1]
        self._attrs['focus_area'] = focus.to('m**2')

    def get_beam_size(self, unit='m'):
        return self._attrs['beam_size'].to(unit)


if __name__ == "__main__":
    pass
