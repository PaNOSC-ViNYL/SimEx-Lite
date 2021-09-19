# Copyright (C) 2021 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Utils analysis module"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import h5py


def gaussian(x, mu, sig):
    """Gaussian function definded as in :func:`numpy.random.normal`"""
    return 1. / (np.sqrt(2. * np.pi) * sig) * np.exp(
        -np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


def linear(x: np.array, a: float, b: float):
    """Linear function y = ax + b

    :param a: slope
    :type a: float
    :param b: intercept
    :type b: float

    :return: y
    :rtype: `numpy.array`
    """
    return a * x + b


class curve_fitting:
    def __init__(self, func, xdata, ydata):
        self.__func = func
        self.__xdata = xdata
        self.__ydata = ydata
        self.__update()

    def __update(self):
        self.__popt, self.__pcov = curve_fit(self.func, self.xdata, self.ydata)
        self.__residuals = self.ydata - self.func(self.xdata, *self.popt)
        ss_res = np.sum(self.__residuals**2)
        ss_tot = np.sum((self.ydata - np.mean(self.ydata))**2)
        self.__r_squared = 1 - (ss_res / ss_tot)

    @property
    def popt(self):
        return self.__popt

    @property
    def residuals(self):
        return self.__residuals

    @property
    def r_squared(self):
        return self.__r_squared

    @property
    def func(self):
        return self.__func

    @func.setter
    def func(self, val):
        self.__func = val
        self.__update()

    @property
    def xdata(self):
        return self.__xdata

    @xdata.setter
    def xdata(self, val):
        self.__xdata = val
        self.__update()

    @property
    def ydata(self):
        return self.__ydata

    @ydata.setter
    def ydata(self, val):
        self.__ydata = val
        self.__update()

    def plotResults(self, xlabel=None, ylabel=None, fn='fitting.png'):
        xdata = self.xdata
        ydata = self.ydata
        popt = self.popt
        print('Coefficient of determination:', self.r_squared)
        for i, item in enumerate(self.popt):
            print('param {}'.format(i + 1), item)

        plt.figure()
        plt.plot(xdata, ydata, 'bo', label='data')
        plt.plot(xdata, self.func(xdata, *popt), 'g--', label='fitting')
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
        plt.legend()
        plt.savefig(fn, dpi=300)

    def predict(self, xdata):
        return self.func(xdata, *self.popt)

    def plotPredict(self, xdata, fn='predict.png'):
        ydata = self.func(xdata, *self.popt)
        plt.figure()
        plt.plot(xdata, ydata)
        plt.savefig(fn, dpi=300)




def saveSimpleH5(arr: np.array, fn: str):
    """Save a simple HDF5 file"""
    with h5py.File(fn, 'w') as h5:
        h5.create_dataset('data', data=arr, chunks=True)


def loadSimpleH5(fn: str) -> np.array:
    """Load a simple HDF5 file"""
    with h5py.File(fn, 'r') as h5:
        return h5['data'][...]
