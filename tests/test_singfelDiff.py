"""Test singfel format"""

from SimExLite.DiffractionData import DiffractionData, SingFELFormat
from SimExLite.DiffractionData.SingFELFormat import (
    getPatternTotal,
    getPatternShape,
    ireadPattern,
    getParameters,
)
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from pathlib import Path

h5_file = "./testFiles/singfel-multi.h5"


def test_getParameters():
    # DiffrData = DiffractionData.from_file(
    #     h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    # )
    # data_dict = DiffrData.get_data()
    params = getParameters(h5_file)
    if __name__ == "__main__":
        print(params)
    assert params["beam"]["photonEnergy"] == 4960.0


def test_getPatternTotal():
    npattern = getPatternTotal(h5_file)
    if __name__ == "__main__":
        print(npattern)
    assert npattern == 13


def test_write(tmp_path):
    diffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    tmp_h5 = str(tmp_path / "tmp.h5")
    diffrData.write(tmp_h5, SingFELFormat)


def test_read():
    diffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    data_dict = diffrData.get_data()
    diffr_patterns = data_dict["img_array"]
    assert len(diffr_patterns) == 13
    assert np.sum(diffr_patterns) != 0

    if __name__ == "__main__":
        plt.figure()
        plt.imshow(diffr_patterns[0], norm=mpl.colors.LogNorm())
        plt.figure()
        plt.imshow(diffr_patterns[2], norm=mpl.colors.LogNorm())
        plt.colorbar()
        plt.show()


def test_createArray_one():
    diffrData = DiffractionData.from_file(
        h5_file,
        format_class=SingFELFormat,
        index=2,
        key="test_singfel",
        poissonize=False,
    )
    diffrData = DiffractionData.from_file(
        h5_file,
        format_class=SingFELFormat,
        index="2",
        key="test_singfel",
        poissonize=False,
    )
    data_dict = diffrData.get_data()
    diffr_pattern = data_dict["img_array"]

    diffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=False
    )
    data_dict = diffrData.get_data()
    diffr_patterns = data_dict["img_array"]
    assert len(diffr_pattern) == 1
    assert np.array_equal(diffr_patterns[2], diffr_pattern[0]) is True

    if __name__ == "__main__":
        plt.figure()
        plt.imshow(diffr_pattern[0], norm=mpl.colors.LogNorm())
        plt.colorbar()
        plt.show()


def test_createArray_partial():
    diffrData = DiffractionData.from_file(
        h5_file,
        format_class=SingFELFormat,
        index="2:5",
        key="test_singfel",
        poissonize=False,
    )
    data_dict = diffrData.get_data()
    diffr_patterns = data_dict["img_array"]
    diffrData = DiffractionData.from_file(
        h5_file,
        format_class=SingFELFormat,
        index="4",
        key="test_singfel",
        poissonize=False,
    )
    data_dict = diffrData.get_data()
    diffr_pattern = data_dict["img_array"]
    assert len(diffr_patterns) == 3
    assert np.array_equal(diffr_patterns[2], diffr_pattern[0]) is True
    if __name__ == "__main__":
        fig, ax = plt.subplots(1, 2)
        im = ax[0].imshow(
            diffr_patterns[0], norm=mpl.colors.LogNorm(vmin=1e-8, vmax=1e-3)
        )
        divider = make_axes_locatable(ax[0])
        cax = divider.append_axes("right", size="5%", pad=0.1)
        fig.colorbar(im, cax=cax)
        im = ax[1].imshow(
            diffr_patterns[1], norm=mpl.colors.LogNorm(vmin=1e-8, vmax=1e-3)
        )
        divider = make_axes_locatable(ax[1])
        cax = divider.append_axes("right", size="5%", pad=0.1)
        fig.colorbar(im, cax=cax)
        fig.tight_layout()
        plt.show()


def test_Poission():
    diffrData = DiffractionData.from_file(
        h5_file, format_class=SingFELFormat, key="test_singfel", poissonize=True
    )
    data_dict = diffrData.get_data()
    assert np.sum(data_dict["img_array"]) == 0


def test_pattern_shape():
    my_shape = getPatternShape(h5_file)
    my_shape == (81, 81)
    if __name__ == "__main__":
        print(my_shape)


def test_iterator():
    my_iter = ireadPattern(h5_file, poissonize=True)
    n = 0
    for ix, _ in my_iter:
        n += 1
        pattern = ix
    assert n == 13
    assert pattern.shape == (81, 81)


# def test_SolidAngles():
#     diffr_patterns = singfelDiffr(h5_file)
#     diffr_patterns.solid_angles
#     if __name__ == "__main__":
#         diffr_patterns.plotSolidAngles()

# def test_QMap():
#     diffr_patterns = singfelDiffr(h5_file)
#     diffr_patterns.q_map
#     if __name__ == "__main__":
#         diffr_patterns.plotQMap()

if __name__ == "__main__":
    test_iterator()
    test_write(Path("./"))
    # test_getPatternTotal()
    # test_read()
    test_createArray_one()
    # test_createArray_partial()
