"""Test EMCPhoton"""

import pytest
from SimExLite.SourceCalculators import GaussianSourceCalculator

WPG_path = "/home/juncheng/GPFS/exfel/data/user/juncheng/WPG"


def test_run_default_parameters():
    calculator = GaussianSourceCalculator("gaussian_source", WPG_path)
    print(calculator.parameters)
    data_out = calculator.backengine()
    print(type(data_out))


def test_run_default_parameters():
    calculator = GaussianSourceCalculator("gaussian_source", WPG_path)
    print(calculator.parameters)
    data_out = calculator.backengine()
    data_out.get_data()


def test_wrong_WPG_path(tmpdir):
    WPG_path_wrong = str(tmpdir / "xx")
    with pytest.raises(ValueError):
        GaussianSourceCalculator("gaussian_source", WPG_path_wrong)
