"""Test DiffractionData"""

import matplotlib.pyplot as plt
from SimExLite.DiffractionData.DiffractionData import DiffractionData
import numpy as np
import pytest
import SimExLite.DiffractionData as DD
from SimExLite.utils.io import UnknownFileTypeError
from pprint import pprint
from pathlib import Path


def test_print_format_keys():
    DD.listFormats()


def test_write_emc_h5_single(tmp_path):
    h5_file = './testFiles/singfel.h5'
    out_path = tmp_path / "h5.emc"
    DiffrData = DD.read(h5_file, poissonize=False)
    DiffrData.multiply(1e4)
    assert isinstance(DiffrData, DiffractionData) is True
    DD.write(out_path, DiffrData, 'emc')


def test_read_emc_h5_single():
    h5_file = './testFiles/h5.emc'
    DiffrData = DD.read(h5_file, pattern_shape=[81, 81])
    DiffrData.plotPattern(0)
    with pytest.raises(IndexError):
        DiffrData.plotPattern(1)


def test_write_emc_h5_multi(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    out_path = tmp_path / "h5_multi.emc"
    DiffrData = DD.read(h5_file, poissonize=False)
    DiffrData.multiply(1e9)
    assert isinstance(DiffrData, DiffractionData) is True
    DD.write(out_path, DiffrData, 'emc')


def test_read_emc_h5_multi():
    h5_file = './testFiles/h5_multi.emc'
    DiffrData = DD.read(h5_file, pattern_shape=[81, 81])
    DiffrData.plotPattern(1)
    assert len(DiffrData.array) == 13


def test_filetype_keywords():
    kws = {'poissonize': True}
    format = DD.filetype_keywords(kws)
    assert format == 'singfel'
    kws = {'woo': True}
    format = DD.filetype_keywords(kws)
    assert format == 'UNKNOWN'


def test_filetype():
    h5_file = './testFiles/singfel.h5'
    format = DD.filetype(h5_file)
    assert format == 'singfel'
    try:
        md_file = './testFiles/README.md'
        format = DD.filetype(md_file)
    except UnknownFileTypeError:
        assert True


def test_unexpected_read_argument(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    with pytest.raises(TypeError) as excinfo:
        DD.read(diffr_path, pattern_shape=[81, 81])
        assert "got an unexpected keyword argument" in str(excinfo.value)


def test_read():
    h5_file = './testFiles/singfel.h5'
    DiffrData = DD.read(h5_file)
    assert isinstance(DiffrData, DD.DiffractionData) is True


def test_file_not_exists():
    h5_file = './testFiles/xx.h5'
    with pytest.raises(FileNotFoundError):
        DD.read(h5_file)


def test_readSingFEL():
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    assert len(data.array) == 13


def test_writeSingFEL(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    ofn = tmp_path / 'rewrite_singfel.h5'
    DD.write(str(ofn), data, 'singfel')


def test_readRewriteSingFEL(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    ofn = tmp_path / 'rewrite_singfel.h5'
    DD.write(str(ofn), data, 'singfel')
    DD.read(str(ofn), format='singfel')


def test_readAutoRewriteSingFEL(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    ofn = tmp_path / 'rewrite_singfel.h5'
    DD.write(str(ofn), data, 'singfel')
    DD.read(str(ofn))


def test_listFormats():
    DD.listFormats()


def test_writeUnsupported():
    input_arr = np.random.rand(10, 10)
    data = DiffractionData(arrary=input_arr)
    with pytest.raises(UnknownFileTypeError) as excinfo:
        DD.write("filename", data, format='blabla')
        print(excinfo.value)
    assert "Unsupported format" in str(excinfo.value)


def test_addGaussianNoise(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    xcs = np.array([-1.845, 56.825, 114.623])
    fwhms = np.array([20.687, 26.771, 29.232])
    hist_params = DD.histogramParams(xcs, fwhms)
    data.addGaussianNoise(hist_params.mu, hist_params.sigs_popt)
    out_path = tmp_path / "fitting.png"
    fn = str(out_path)
    hist_params.plotFitting(fn)
    assert out_path.is_file() is True


def test_addBeamStop():
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file)
    data.addBeamStop(3)


def test_plotPattern():
    h5_file = './testFiles/singfel-multi.h5'
    data = DD.read(h5_file, poissonize=False)
    data.plotPattern(idx=0, logscale=True)


def test_savePattern(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file, poissonize=False)
    out_path = tmp_path / "test.png"
    dd.plotPattern(idx=0, logscale=True, fn_png=str(out_path))
    assert out_path.is_file() is True


def test_photon_statistics():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file, poissonize=False)
    pprint(dd.photon_statistics)


def test_plotStatistics():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file, poissonize=False)
    if __name__ == "__main__":
        dd.plotHistogram()


def test_saveHistogram(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file, poissonize=False)
    out_path = tmp_path / "test.png"
    dd.plotHistogram(fn_png=str(out_path))
    assert out_path.is_file() is True


def test_multiply():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file, poissonize=False)
    orig = dd.array
    val_orig = np.max(orig[0])
    dd.multiply(0)
    multi = dd.array
    assert np.max(orig[0]) == val_orig
    assert np.max(multi[0]) == 0
    assert np.max(multi[2]) == 0


def test_pattern_total():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file)
    assert dd.pattern_total == 13


def test_data_simplebeam():
    h5_file = './testFiles/singfel-multi.h5'
    dd = DD.read(h5_file)
    assert pytest.approx(dd.beam.attrs['wavelength'], 0.1) == 2.5
    assert pytest.approx(dd.beam.wavelength, 0.1) == 2.5
    print(dd.beam)


def test_write_EMC_ini(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    out_path = tmp_path / "config.ini"
    # out_path = 'config.ini'
    dd = DD.read(h5_file)
    dd.writeEmcIni(str(out_path))


if __name__ == "__main__":
    # pass
    # test_writeUnsupported()
    # test_print_format_keys()
    # test_write_emc_h5_multi(Path('./'))
    # test_read_emc_h5_multi()
    # plt.show()
    test_data_simplebeam()
    # test_filetype_content()
    # test_getDataType()
    # test_addBeamStop()
    # test_photon_statistics()
    # test_plotPattern()
    # test_plotStatistics()
    # test_multiply()
    # test_iterator()
