import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.optimize import curve_fit


def gaussian(x, mu, sig):
    """Gaussian function"""
    return 1. / (np.sqrt(2. * np.pi) * sig) * np.exp(
        -np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


class curve_fitting:
    """Curve fitting wrapper class"""
    def __init__(self, func, xdata, ydata):
        """

        :param func: The function to fit.
        :type func: function
        :param xdata: The x-axis data.
        :type xdata: 1darray_like
        :param ydata: The y-axis data.
        :type ydata: 1darray_like
        """
        self.__func = func
        self.__xdata = xdata
        self.__ydata = ydata
        self.__update()

    def __update(self):
        """Update the parameters when the function or data changed."""

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

    def plotResults(self):
        """Plot the fitting results."""

        xdata = self.xdata
        ydata = self.ydata
        popt = self.popt
        print('Coefficient of determination:', self.r_squared)
        for i, item in enumerate(self.popt):
            print('param {}'.format(i + 1), item)

        plt.figure()
        plt.plot(xdata, ydata, 'bo', label='data')
        plt.plot(xdata, self.func(xdata, *popt), 'g--', label='fitting')
        plt.legend()

    def predict(self, xdata):
        """To predict the ydata based on the fitting model.

        :param xdata: The x-axis data.
        :type xdata: 1darray_like
        ...
        :return: The predicted y-axis data.
        :rtype: 1darray
        """
        return self.func(xdata, *self.popt)

    def plotPredict(self, xdata):
        """To predict and plot the ydata based on the fitting model.

        :param xdata: The x-axis data.
        :type xdata: 1darray_like
        """
        ydata = self.func(xdata, *self.popt)
        plt.figure()
        plt.plot(xdata, ydata)
