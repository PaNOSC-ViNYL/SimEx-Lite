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
    """The simplest description of a pulse of the beam

    :param pulse_energy: The energy of the X-ray pulse in Joule. It will override
    `photons_per_pulse`, if both are provided.
    :type pulse_energy: float
    :param photons_per_pulse: The number of photons of this pulse. It will be
    overrided by `pulse_energy`, if both are porvided.
    :type photons_per_pulse: int
    :param wavelength: The wavelength of this pulse in Angstrom. It will be
    overrided by `photon_energy`, if both are porvided.
    :type wavelength: float
    :param photon_energy: The photon energy of this pulse, in eV. It will
    override `wavelength`, if both are porvided.
    :type photon_energy: float
    :param focus: The focus spot of this pulse, in `focus_unit`. It can be either
    float of a list: [fwhm_x, fwhm_y]
    :type focus: float or list
    :param focus_unit: defaults to 'm'.
    :type focus_unit: str
    :param fluence_unit: defaults to 'joule/cm**2'.
    :type fluence_unit: str
    :param flux_unit: The flux in this pulse, defaults to '1/um**2'.
    :type flux_unit: str
    """
    def __init__(self,
                 pulse_energy=None,
                 photons_per_pulse=None,
                 wavelength=None,
                 photon_energy=None,
                 focus=None,
                 focus_unit='m',
                 fluence_unit='joule/cm**2',
                 flux_unit='1/um**2') -> None:

        self.__focus = focus
        self.__focus_unit = focus_unit
        self.__pulse_energy = pulse_energy
        self.__photons_per_pulse = photons_per_pulse
        self.__wavelength = wavelength
        self.__photon_energy = photon_energy
        self.fluence_unit = fluence_unit
        self.flux_unit = flux_unit

        self.__update()

    def __update(self):
        if self.__photon_energy:
            self.__photon_energy = setValue(self.__photon_energy, 'eV')
        elif self.__wavelength:
            self.__photon_energy = setValue(hcDivide(self.__wavelength), 'keV')
        if self.__pulse_energy:
            self.__pulse_energy = setValue(self.__pulse_energy, 'joule')
        elif self.__photons_per_pulse:
            self.__pulse_energy = self.__photons_per_pulse * self.__photon_energy.to(
                'joule')
        if self.__focus:
            try:
                len(self.__focus)
            except TypeError:
                self.__focus = [self.__focus, self.__focus]
            self.__focus = [
                setValue(self.__focus[0], self.__focus_unit),
                setValue(self.__focus[1], self.__focus_unit)
            ]
            self.area = self.__focus[0] * self.__focus[1]
            self.fluence = self.pulse_energy / self.area
            self.pulse_flux = self.photons_per_pulse / self.area

    @property
    def focus(self):
        return self.__focus

    @focus.setter
    def focus(self, val):
        self.__focus = val
        self.__update()

    @property
    def focus_unit(self):
        return self.__focus_unit

    @focus_unit.setter
    def focus_unit(self, val):
        self.__focus_unit = val
        self.__update()

    @property
    def pulse_energy(self):
        return self.__pulse_energy

    @pulse_energy.setter
    def pulse_energy(self, val):
        self.__pulse_energy = val
        self.__photons_per_pulse = None
        self.__update()

    @property
    def photons_per_pulse(self):
        return self.__pulse_energy / self.__photon_energy.to('joule')

    @photons_per_pulse.setter
    def photons_per_pulse(self, val):
        self.__photons_per_pulse = val
        self.__pulse_energy = None
        self.__update()

    @property
    def wavelength(self):
        return setValue(hcDivide(self.__photon_energy.to('keV').to_tuple()[0]),
                        'angstrom')

    @wavelength.setter
    def wavelength(self, val):
        self.__wavelength = val
        self.__photon_energy = None
        self.__update()

    @property
    def photon_energy(self):
        return self.__photon_energy

    @photon_energy.setter
    def photon_energy(self, val):
        self.__photon_energy = val
        self.__wavelength = None
        self.__update()

    def print(self):
        if self.wavelength:
            print('wavelength = {:.3~P}'.format(
                self.wavelength.to('angstrom')))
        if self.photon_energy:
            print('photon energy = {:.3~P}'.format(
                self.photon_energy.to('eV')))
        if self.photons_per_pulse:
            print('photons per pulse = {:.2~P}'.format(self.photons_per_pulse))
        if self.pulse_energy:
            print('pulse energy = {:.2~P}'.format(self.pulse_energy.to('mJ')))
        if self.focus:
            print('focus = {:~P} x {:~P}'.format(self.focus[0], self.focus[1]))
            if self.pulse_energy:
                print('fluence = {:.2~P}'.format(
                    self.fluence.to(self.fluence_unit)))
            if self.photons_per_pulse:
                print('pulse flux = {:.2~P}'.format(
                    self.pulse_flux.to(self.flux_unit)))


if __name__ == "__main__":
    pass
