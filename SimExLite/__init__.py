# Copyright (C)  Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Top-level package for SimEx-Lite."""

__author__ = """Juncheng E"""
__email__ = 'juncheng.e@xfel.eu'
__version__ = '0.3.2'

from libpyvinyl.BaseData import DataCollection
# Using pint in the whole project
# https://pint.readthedocs.io/en/0.10.1/tutorial.html#using-pint-in-your-projects
from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity


# Set pint value
def setValue(val, unit):
    """Set the value with the pint unit"""
    if isinstance(val, ureg.Quantity):
        return val.to(unit)
    else:
        return Q_(val, unit)
