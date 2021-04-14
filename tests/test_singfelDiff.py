"""Test singfelDiff data"""

from SimExLite.DataAPI.singfelDiffr import getParameters, singfelDiffr
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np

h5_file = './testFiles/singfel-multi.h5'


def test_getParameters():
    params = getParameters(h5_file)
    if __name__ == "__main__":
        print(params)
    assert params['beam']['photonEnergy'] == 4960.0


def test_construct():
    diffr_patterns = singfelDiffr(h5_file)
    assert diffr_patterns.pattern_total == 13


def test_createArray():
    diffr_patterns = singfelDiffr(h5_file)
    diffr_patterns.createArray()
    assert len(diffr_patterns.array) == 13
    assert np.sum(diffr_patterns.array) != 0
    if __name__ == "__main__":
        plt.figure()
        plt.imshow(diffr_patterns.array[0], norm=mpl.colors.LogNorm())
        plt.colorbar()
        plt.show()


def test_createArray_one():
    diffr_patterns = singfelDiffr(h5_file, )
    diffr_patterns.createArray(index_range=146)
    assert len(diffr_patterns.array) == 1


def test_createArray_partial():
    diffr_patterns = singfelDiffr(h5_file, )
    diffr_patterns.createArray(index_range=[146, 294])
    assert len(diffr_patterns.array) == 2
    if __name__ == "__main__":
        fig, ax = plt.subplots(1, 2)
        im = ax[0].imshow(diffr_patterns.array[0],
                          norm=mpl.colors.LogNorm(vmin=1e-8, vmax=1e-3))
        divider = make_axes_locatable(ax[0])
        cax = divider.append_axes("right", size="5%", pad=0.1)
        fig.colorbar(im, cax=cax)
        im = ax[1].imshow(diffr_patterns.array[1],
                          norm=mpl.colors.LogNorm(vmin=1e-8, vmax=1e-3))
        divider = make_axes_locatable(ax[1])
        cax = divider.append_axes("right", size="5%", pad=0.1)
        fig.colorbar(im, cax=cax)
        fig.tight_layout()
        plt.show()


def test_Poission():
    diffr_patterns = singfelDiffr(h5_file)
    diffr_patterns.createArray(poissonize=True)
    assert np.sum(diffr_patterns.array) == 0


def test_SolidAngles():
    diffr_patterns = singfelDiffr(h5_file)
    diffr_patterns.solid_angles
    if __name__ == "__main__":
        diffr_patterns.plotSolidAngles()


def test_QMap():
    diffr_patterns = singfelDiffr(h5_file)
    diffr_patterns.q_map
    if __name__ == "__main__":
        diffr_patterns.plotQMap()


def test_pattern_shape():
    diffr_patterns = singfelDiffr(h5_file)
    shape = diffr_patterns.pattern_shape
    if __name__ == "__main__":
        print(shape)


def test_iterator():
    diffr_patterns = singfelDiffr(h5_file)
    n = 0
    for ix in diffr_patterns.iterator:
        n += 1
        pattern = ix
    assert n == 13
    assert pattern.shape == (81, 81)


if __name__ == "__main__":
    test_getParameters()
    test_construct()
    test_createArray()
    test_Poission()
    test_createArray_partial()
    test_SolidAngles()
    test_QMap()
    test_pattern_shape()
