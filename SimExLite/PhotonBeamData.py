# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Photon Beam data APIs"""

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
    def __init__(self,
                 pulse_energy=None,
                 photons_per_pulse=None,
                 wavelength=None,
                 photon_energy=None,
                 focus_area=None):


        # Default photon energy unit
        self.__attrs = dict(pulse_energy=pulse_energy,
                            wavelength=wavelength,
                            focus_area=focus_area)

        if wavelength and photon_energy:
            raise ValueError('Wavelength and photon_energy can not be set at the same time.')
        if pulse_energy and photons_per_pulse:
            raise ValueError('pulse_energy and photons_per_pulse can not be set at the same time.')

        if wavelength:
            self.set_wavelength(wavelength)
        if photon_energy:
            self.set_photon_energy(photon_energy)
        if photons_per_pulse:
            self.set_photons_per_pulse(photons_per_pulse)
        if pulse_energy:
            self.set_pulse_energy(pulse_energy)
        if focus_area:
            self.set_focus_area(focus_area)


    def set_focus_area(self, val, unit='m**2'):
        focus_area = setValue(val, unit)
        self.__attrs['focus_area'] = focus_area.to('m**2')

    def get_focus_area(self, unit='m**2'):
        return self.__attrs['focus_area'].to(unit)

    def set_pulse_energy(self, val, unit='joule'):
        pulse_energy = setValue(val, unit)
        self.__attrs['pulse_energy'] = pulse_energy.to('joule')

    def get_pulse_energy(self, unit='joule'):
        return self.__attrs['pulse_energy'].to(unit)

    def set_photons_per_pulse(self, val):
        pulse_energy = val*self.get_photon_energy()
        self.__attrs['pulse_energy'] = setValue(pulse_energy, 'joule')

    def get_photons_per_pulse(self):
        return self.__attrs['pulse_energy'].to('joule') / self.get_photon_energy().to('joule')

    def set_wavelength(self, val, unit='angstrom'):
        wavelength = setValue(val, unit)
        self.__attrs['wavelength'] = wavelength.to('angstrom')

    def get_wavelength(self, unit='angstrom'):
        return self.__attrs['wavelength'].to(unit)

    def set_photon_energy(self, val, unit='eV'):
        photon_energy = setValue(val, unit)
        self.__attrs['wavelength'] = setValue(hcDivide(photon_energy.to('keV').magnitude), 'angstrom')

    def get_photon_energy(self, unit='eV'):
        photon_energy = setValue(hcDivide(self.__attrs['wavelength'].to('angstrom').magnitude), 'keV')
        return photon_energy.to(unit)

    def get_fluence(self, unit='joule/cm**2'):
        fluence = self.get_pulse_energy()/self.get_focus_area()
        return fluence.to(unit)

    def get_flux(self, unit='1/um**2'):
        flux = self.get_photons_per_pulse()/self.get_focus_area()
        return flux.to(unit)

    @property
    def attrs(self):
        my_attrs = {}
        for key in self.__attrs.keys():
            my_attrs[key] = self.__attrs[key].magnitude
        return my_attrs

    def showAttrs(self):
        for key,value in self.__attrs.items():
            print('{} = {:.3~P}'.format(key, value))
        print('{} = {:.3~P}'.format('photon_energy', self.get_photon_energy()))
        print('{} = {:.3~P}'.format('photons_per_pulse', self.get_photons_per_pulse()))
        if self.__attrs['focus_area'] is not None:
            print('{} = {:.3~P}'.format('fluence', self.get_fluence()))
            print('{} = {:.3~P}'.format('flux', self.get_flux()))


if __name__ == "__main__":
    pass
