"""Test DiffractionData"""

import numpy as np
import pytest
import h5py
import SimExLite.DiffractionData as DD
from SimExLite.utils.io import UnknownFileTypeError
from pprint import pprint

def test_filetype_content():
    h5_file = './testFiles/singfel.h5'
    format = DD.filetype_content(h5_file)
    assert format == 'singfel'

    md_file = './testFiles/README.md'
    format = DD.filetype_content(md_file)
    assert format == 'UNKNOWN'

# TODO: test_filetype_h5_emc
# def test_filetype_h5_emc():
#     h5_file = './testFiles/singfel.h5'
#     format = DD.filetype_h5(h5_file)
#     print(format)

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

def test_read():
    h5_file = './testFiles/singfel.h5'
    DD.read(h5_file)

# def testGetIterator():
#     h5_file = './testFiles/singfel.h5'
#     DD = read(h5_file)
#     DD.iter


# def test_getDataType():
#     h5_file = './testFiles/singfel.h5'
#     assert getDataType(h5_file) == '1'


# def test_file_not_exists():
#     h5_file = './testFiles/xx.h5'
#     with pytest.raises(FileNotFoundError):
#         DD = DiffractionData()
#         DD.read(h5_file)


# def test_readSingFEL():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     assert len(dd.array) == 13


# def test_saveAs_unsupported():
#     input_arr = np.random.rand(10, 10)
#     dd = DiffractionData(arr=input_arr)
#     with pytest.raises(TypeError) as excinfo:
#         dd.saveAs(data_format="blahblah", file_name="blabla")
#         print(excinfo.value)
#     assert "Unsupported format" in str(excinfo.value)


# def test_saveAs_emc(tmp_path):
#     input_arr = np.array([np.random.rand(10, 10)])
#     dd = DiffractionData(arr=input_arr)
#     data_fn = str(tmp_path / "photons.emc")
#     dd.saveAs('emc', data_fn)


# def test_simple(tmp_path):
#     input_arr = [np.random.rand(10, 10)]
#     dd = DiffractionData(arr=input_arr)
#     data_fn = str(tmp_path / "photons.h5")
#     dd.saveAs('simple', data_fn)
#     assert h5py.is_hdf5(data_fn) is True


# def test_addGaussianNoise(tmp_path):
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     xcs = np.array([-1.845, 56.825, 114.623])
#     fwhms = np.array([20.687, 26.771, 29.232])
#     hist_params = histogramParams(xcs, fwhms)
#     dd.addGaussianNoise(hist_params.mu, hist_params.sigs_popt)
#     out_path = tmp_path / "fitting.png"
#     fn = str(out_path)
#     hist_params.plotFitting(fn)
#     assert out_path.is_file() is True


# def test_addBeamStop():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     dd.addBeamStop(3)


# def test_plotPattern():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     if __name__ == "__main__":
#         dd.plotPattern(idx=0, logscale=True)


# def test_savePattern(tmp_path):
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     out_path = tmp_path / "test.png"
#     dd.plotPattern(idx=0, logscale=True, fn_png=str(out_path))
#     assert out_path.is_file() is True


# def test_photon_statistics():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     if __name__ == "__main__":
#         pprint(dd.photon_statistics)


# def test_plotStatistics():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     if __name__ == "__main__":
#         dd.plotHistogram()


# def test_saveHistogram(tmp_path):
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     out_path = tmp_path / "test.png"
#     dd.plotHistogram(fn_png=str(out_path))
#     assert out_path.is_file() is True


# def test_multiply():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     orig = dd.array
#     val_orig = np.max(orig[0])
#     dd.multiply(0)
#     multi = dd.array
#     assert np.max(orig[0]) == val_orig
#     assert np.max(multi[0]) == 0
#     assert np.max(multi[2]) == 0


# def test_readEMC_format(tmp_path):
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     dd.createArray()
#     out_path = tmp_path / "test.emc"
#     dd.saveAs("emc", str(out_path))
#     emcdd = DiffractionData()
#     emcdd.read(str(out_path))
#     assert emcdd.input_file_type == "EMC Sparse Photon"
#     emcdd.createArray()
#     assert len(emcdd.array) == 13


# def test_iterator():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     n = 0
#     for ix in dd.iterator:
#         n += 1
#     assert n == 13


# def test_pattern_total():
#     h5_file = './testFiles/singfel-multi.h5'
#     dd = DiffractionData()
#     dd.read(h5_file)
#     assert dd.pattern_total == 13


# def test_pattern_total_no_read():
#     dd = DiffractionData()
#     with pytest.raises(AttributeError):
#         dd.pattern_total


if __name__ == "__main__":
    test_filetype_h5_singfel()
#     test_getDataType()
#     test_addBeamStop()
#     test_photon_statistics()
#     test_plotPattern()
#     test_plotStatistics()
#     test_multiply()
#     test_iterator()
