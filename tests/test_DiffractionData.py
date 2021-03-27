"""Test DiffractionData"""

from SimExLite.DiffractionData import getDataType


def test_getDataType():
    h5_file = './testFiles/singfel.h5'
    assert getDataType(h5_file) == '1'


if __name__ == "__main__":
    test_getDataType()
