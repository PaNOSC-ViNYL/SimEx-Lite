"""Test EMCPhoton"""

import os
import numpy as np
from ocelot import spectrum
import pytest
from SimExLite.SourceCalculators.GaussianSourceCalculator import (
    GaussianSourceCalculator,
    get_divergence_from_beam_diameter,
)
from libpyvinyl import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.WavefrontData import WavefrontData
from matplotlib import pyplot as plt
import h5py
from scipy.constants import hbar, c, electron_volt


def validate_result(gsc):
    """
    Check the following on the output of GaussiannSourceCalculator:
        - the output data is a DataCollection,
        - nothing is none that should not be,
        - limits make sense,
        - the intensity is not zero everywhere and everytime.

    This uses `get_data()`, so logically `test_get_data()` should be called before
    any test using this.

    Todo:
        - More checks could be added.
    """
    d = gsc.output.get_data()
    elf = d["electricField"]
    xmax, xmin, ymax, ymin = [
        d[which] for which in ["gridxMax", "gridxMin", "gridyMax", "gridyMin"]
    ]
    ints = np.abs(elf["x"]) ** 2 + np.abs(elf["y"]) ** 2
    nothing_is_none = np.all([thing is not None for thing in [elf, xmax, xmin, ymax, ymin]])
    lims_ok = xmax > xmin and ymax > ymin
    data_ok = not np.all(ints == 0 + 0j)
    return nothing_is_none and lims_ok and data_ok


def test_divergence():
    "test get_divergence_from_beam_diameter againist reference values"
    test_evs = (1000, 2000, 2567, 1000 * np.pi)
    test_diams = (1e-4, 2e-4, 1e-4 * np.sqrt(2))
    pm_space = [(x, y) for x in test_evs for y in test_diams]  # cartesian product
    res, ref = [], []
    for ev, diam in pm_space:
        res.append(get_divergence_from_beam_diameter(ev, diam))
        w0 = diam / np.sqrt(2 * np.log(2))
        e_joule = ev * electron_volt
        ref.append(2 * hbar * c / (e_joule * w0))

    assert np.allclose(res, ref, rtol=1e-8, atol=1e-8)


def test_get_data(tmp_path="tmp"):
    "test accessing to the results via output.get_data()"
    os.makedirs(tmp_path, exist_ok=True)
    gsc = GaussianSourceCalculator(
        "gaussian_source", instrument_base_dir=tmp_path
    )
    gsc.backengine()
    d = gsc.output.get_data()
    elf = d["electricField"]
    xmax, xmin, ymax, ymin = [
        d[which] for which in ["gridxMax", "gridxMin", "gridyMax", "gridyMin"]
    ]
    assert np.all([data is not None for data in [elf, xmax, xmin, ymax, ymin]])
    assert xmax > xmin and ymax > ymin

    val = (np.abs(elf["x"]) ** 2 + np.abs(elf["y"]) ** 2).transpose((2, 0, 1))
    i = len(val) // 2
    plotdata = val[len(val) // 2]
    fig, ax = plt.subplots()
    ims = ax.imshow(plotdata, extent=(xmin, xmax, ymin, ymax))
    plt.colorbar(ims)
    plt.savefig(os.path.join(tmp_path, f"gsc_{i}.png"))


def test_run_default_parameters(tmp_path='tmp'):
    "Test a simple execution of GSC with the default parameters."
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=tmp_path)
    print(gsc.parameters)
    data_out = gsc.backengine()
    print(type(data_out))
    assert validate_result(gsc)


def test_custom_params(tmp_path='tmp'):
    "Execute GSC with some uglier cusstom parameters."
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=tmp_path)

    # set some "ugly" parameters
    gsc.parameters["photon_energy"].value = 1e3 * np.pi + 0.6
    gsc.parameters["photon_energy_relative_bandwidth"].value = 1e-3 * np.pi / 2
    gsc.parameters["beam_diameter_fwhm"].value = 1e-4 / np.sqrt(2)
    gsc.parameters["pulse_energy"].value = 2e-3 * 2.0 / 3
    gsc.parameters["divergence"].value = get_divergence_from_beam_diameter(
        1e3 * np.pi + 0.6, 1e-4 / np.sqrt(2)
    )
    gsc.parameters["photon_energy_spectrum_type"].value = "SASE"
    gsc.parameters["number_of_transverse_grid_points"].value = 419
    gsc.parameters["number_of_time_slices"].value = 103
    gsc.parameters["z"].value = 29

    print(gsc.parameters)
    gsc.backengine()

    assert validate_result(gsc)


def test_spectrums(tmp_path='tmp'):
    "Test the spectrum options with the default parameters."
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=tmp_path)
    for spectrum in ["SASE", "tophat", "twocolour"]:
        gsc.parameters["photon_energy_spectrum_type"].value = spectrum
        gsc.backengine()
        assert validate_result(gsc)


def test_paths(tmp_path="tmp"):
    "Check if passing custom paths works as excepted"
    os.makedirs(tmp_path, exist_ok=True)
    instr_dir = os.path.join(tmp_path, "gsc_path_test_instr")
    calc_dir = "gsc_path_test_calc"
    outf = "gsc_path_test.h5"
    gsc = GaussianSourceCalculator(
        "gaussian_source",
        output_filenames=outf,
        instrument_base_dir=instr_dir,
        calculator_base_dir=calc_dir,
    )
    gsc.backengine()
    print("output_files: ", gsc.output_file_paths, "\nbase_dir: ", gsc.base_dir)
    assert validate_result(gsc)
    assert os.path.exists(gsc.base_dir)
    assert os.path.exists(gsc.output_file_paths[0])
    assert os.path.samefile(gsc.base_dir, os.path.join(instr_dir, calc_dir))
    assert os.path.samefile(gsc.output_file_paths[0], os.path.join(instr_dir, calc_dir, outf))


def test_save_data(tmp_path="tmp"):
    "Check if the calculation produces a valid HDF5 file"
    os.makedirs(tmp_path, exist_ok=True)
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=tmp_path)
    gsc.backengine()
    for f in gsc.output_file_paths:
        print(f)
        assert os.path.exists(f)
        assert h5py.is_hdf5(f)


def test_dump_and_load(tmp_path="tmp"):
    "Check if dumping and loading an instrument works and leaves parameters unchanged."
    os.makedirs(tmp_path, exist_ok=True)
    tmpf = os.path.join(tmp_path, "dumptest.dump")
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=tmp_path)
    # gsc.backengine()
    gsc.dump(tmpf)
    gsc2 = GaussianSourceCalculator("fromdump")
    gsc2.from_dump(tmpf)
    assert np.all(
        [
            gsc.output_filenames[i] == gsc2.output_filenames[i] for i in range(len(gsc.output_filenames))
        ]
    )
    for key in gsc.parameters.parameters.keys():
        assert gsc2.parameters[key].value == gsc.parameters[key].value
    gsc2.backengine()
    assert validate_result(gsc2)


def main():
    test_divergence()
    test_get_data()
    test_run_default_parameters()
    test_custom_params()
    test_spectrums()
    test_dump_and_load()
    test_paths()
    test_save_data()


if __name__ == "__main__":
    main()
