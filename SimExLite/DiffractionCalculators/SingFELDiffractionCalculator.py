# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

import os
from pathlib import Path
from subprocess import Popen, PIPE
import sys
import shlex
import h5py
import numpy as np
from tqdm.autonotebook import tqdm

try:
    from pysingfel.detector import Detector
    from pysingfel.beam import Beam
    from pysingfel.radiationDamage import setEnergyFromFile

    PYSINGFEL_AVAILABLE = True
except ModuleNotFoundError:
    PYSINGFEL_AVAILABLE = False
from libpyvinyl.BaseCalculator import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.DiffractionData import DiffractionData, SingFELFormat
from SimExLite.PMIData import XMDYNFormat
import shutil
from SimExLite.utils.Logger import setLogger

logger = setLogger("SingFELDiffractionCalculator")


class SingFELDiffractionCalculator(BaseCalculator):
    """Diffraction pattern calculator with pysingfel backend.

    Args:
        name (str): The name of this calculator.
        input (PMIData): The input data in `PMIData` class.

    :param output_keys: The key(s) of this calculator's output data.

    :param output_data_types: The data type(s), i.e., classes, of each output.
                                It's a list of the data classes or a single data class.
                                The available data classes are based on `BaseData`.
    :param output_filenames: The name(s) of the output file(s).
                                It can be a str of a filename or a list of filenames.
                                If the mapping is dict mapping, the name is `None`.
                                Defaults to None.

    :param instrument_base_dir: The base directory for the instrument to which
                                this calculator belongs.
                                The final exact output file path depends on `instrument_base_dir` and `calculator_base_dir`: `instrument_base_dir`/`calculator_base_dir`/filename

    :param calculator_base_dir: The base directory for this calculator. The final
                                exact output file path depends on `instrument_base_dir` and
                                `calculator_base_dir`: `instrument_base_dir`/`calculator_base_dir`/filename

    :param parameters: The parameters for this calculator.

    """

    def __init__(
        self,
        name: str,
        input: DataCollection,
        output_keys: str = "singfel_diffraction",
        output_data_types=DiffractionData,
        output_filenames: str = "diffr.h5",
        instrument_base_dir="./",
        calculator_base_dir="SingFELDiffractionCalculator",
        parameters=None,
    ):
        super().__init__(
            name,
            input,
            output_keys,
            output_data_types=output_data_types,
            output_filenames=output_filenames,
            instrument_base_dir=instrument_base_dir,
            calculator_base_dir=calculator_base_dir,
            parameters=parameters,
        )

    def init_parameters(self):
        parameters = CalculatorParameters()
        uniform_rotation = parameters.new_parameter(
            "uniform_rotation",
            comment="If it's True, the orientations are fixed to ensure the SO3 space is always uniformly sampled."
            + " If it's False, it will be a random sampling complying a uniform distribution in the SO3 space",
        )
        uniform_rotation.value = False

        calculate_Compton = parameters.new_parameter(
            "calculate_Compton", comment="If calculate the compton scattering."
        )
        slice_interval = parameters.new_parameter(
            "slice_interval", comment="The slice interval of the pmi time frames"
        )
        slice_index_upper = parameters.new_parameter(
            "slice_index_upper",
            comment="The upper limit of the slice index for diffraction calculation ",
        )
        back_rotation = parameters.new_parameter(
            "back_rotation",
            comment="Before applying diffraction rotation, rotate the sample back to its original position before photon matter interaction.",
        )
        pmi_start_ID = parameters.new_parameter(
            "pmi_start_ID", comment="The start ID of the pmi files"
        )
        pmi_stop_ID = parameters.new_parameter(
            "pmi_stop_ID", comment="The stop ID of the pmi files"
        )
        number_of_diffraction_patterns = parameters.new_parameter(
            "number_of_diffraction_patterns",
            comment="The number of diffraction patterns to generate per pmi file",
        )
        pixel_size = parameters.new_parameter(
            "pixel_size", comment="The pixel size of the detector", unit="m"
        )
        pixels_x = parameters.new_parameter(
            "pixels_x", comment="Number of pixels in x direction"
        )
        pixels_y = parameters.new_parameter(
            "pixels_y", comment="Number of pixels in y direction"
        )
        distance = parameters.new_parameter(
            "distance", comment="Sample to detector distance", unit="m"
        )
        mpi_command = parameters.new_parameter(
            "mpi_command", comment="The mpi command to run pysingfel"
        )
        allow_rewrite = parameters.new_parameter(
            "allow_rewrite", comment="Allow rewrite the ouput."
        )

        calculate_Compton.value = False
        back_rotation.value = False
        slice_interval.value = 100
        slice_index_upper.value = 1
        pmi_start_ID.value = 1
        pmi_stop_ID.value = 1
        number_of_diffraction_patterns.value = 10
        pixel_size.value = 0.001
        pixels_x.value = 10
        pixels_y.value = 5
        distance.value = 0.13
        mpi_command.value = "mpirun -n 2"
        allow_rewrite.value = False

        self.parameters = parameters

    def backengine(self):
        input_fn = self.get_input_fn()
        # input_dir = Path(input_fn).parent
        input_dir = self.__get_input_dir(input_fn)
        output_stem = str(Path(self.output_file_paths[0]).stem)
        output_dir = Path(self.output_file_paths[0]).parent / output_stem
        geom_file = self.get_geometry_file()
        # uniform_rotation = not self.parameters["random_rotation"].value
        uniform_rotation = self.parameters["uniform_rotation"].value
        calculate_Compton = self.parameters["calculate_Compton"].value
        slice_interval = self.parameters["slice_interval"].value
        number_of_slices = self.parameters["slice_index_upper"].value
        pmi_start_ID = self.parameters["pmi_start_ID"].value
        pmi_stop_ID = self.parameters["pmi_stop_ID"].value
        number_of_diffraction_patterns = self.parameters[
            "number_of_diffraction_patterns"
        ].value

        mpi_command = self.parameters["mpi_command"].value
        python_command = str(sys.executable)
        # fmt: off
        if self.parameters["allow_rewrite"].value is True:
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir.mkdir(parents=True, exist_ok=False)
        
        err_info = "Cannot find the 'pysingfel' module, which is required to run" + "SingFELDiffractionCalculator.backengine(). Did you install it following the instruction: https://simex-lite.readthedocs.io/en/latest/backengines/pysingfel.html"

        try:
            import pysingfel
        except ModuleNotFoundError:
            raise ModuleNotFoundError(err_info)
        
        command_sequence = [python_command, pysingfel.__path__[0]+'/radiationDamageMPI.py',
                            '--inputDir',         str(input_dir),
                            '--outputDir',        str(output_dir),
                            '--geomFile',         str(geom_file),
                            '--configFile',       "/dev/null",
                            '--backRotation',     str(self.parameters["back_rotation"].value),
                            '--uniformRotation',  str(uniform_rotation),
                            '--calculateCompton', str(calculate_Compton),
                            '--sliceInterval',    str(slice_interval),
                            '--numSlices',        str(number_of_slices),
                            '--pmiStartID',       str(pmi_start_ID),
                            '--pmiEndID',         str(pmi_stop_ID),
                            '--numDP',            str(number_of_diffraction_patterns),
                            ]
        # fmt: on
        args = shlex.split(mpi_command) + command_sequence
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        # proc.wait()
        # The above one can be replaced by proc.communicate()
        output, err = proc.communicate()
        rc = proc.returncode
        if rc != 0:
            print(output.decode("ascii"))
            raise RuntimeError(err.decode("ascii"))
        saveH5(str(output_dir))
        assert len(self.output_keys) == 1
        key = self.output_keys[0]
        output_data = self.output[key]
        output_data.set_file(self.output_file_paths[0], SingFELFormat)
        return self.output

    def get_input_fn(self):
        """Make sure the data is a mapping of PMI file"""
        assert len(self.input) == 1
        input_data = self.input.to_list()[0]
        if input_data.mapping_type == XMDYNFormat:
            input_fn = input_data.filename
        else:
            filepath = Path(self.base_dir) / "pmi_out_0000001.h5"
            input_data.write(str(filepath), XMDYNFormat)
            input_fn = str(filepath)

        return input_fn

    def get_geometry_file(self):
        simple_config = {
            "pixel_size": self.parameters["pixel_size"].value,
            "slow_pixels": self.parameters["pixels_y"].value,
            "fast_pixels": self.parameters["pixels_x"].value,
        }
        distance = self.parameters["distance"].value
        filename = str(Path(self.base_dir) / "singfel.geom")
        write_singfel_geom_file(filename, simple_config, distance)
        return filename

    def __get_input_dir(self, input_fn):
        """Create/get the input dir for PMI_input files"""
        input_path = Path(input_fn)
        dir_path = input_path.with_suffix("")
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)
        dir_path.mkdir()
        p = dir_path / "pmi_out_0000001.h5"
        p.symlink_to(input_path.resolve())
        return str(dir_path)


def write_singfel_geom_file(file_name, simeple_config, distance):
    """Write the geom file for pysingfel"""
    # fmt: off
    panel_id_str = 0
    serialization = ";panel %s\n" % (panel_id_str)
    serialization += "panel%s/min_fs         = %d\n" % (panel_id_str, 0)
    serialization += "panel%s/max_fs         = %d\n" % (panel_id_str, simeple_config["fast_pixels"]-1)
    serialization += "panel%s/min_ss         = %d\n" % (panel_id_str, 0)
    serialization += "panel%s/max_ss         = %d\n" % (panel_id_str, simeple_config["slow_pixels"]-1)
    # fmt: on
    # This is allowed to be float
    corner_x = -(simeple_config["fast_pixels"] - 1) / 2
    corner_y = -(simeple_config["slow_pixels"] - 1) / 2
    # fmt: off
    serialization += "panel%s/fs             = %s\n" % (panel_id_str, "1.0x")
    serialization += "panel%s/ss             = %s\n" % (panel_id_str, "1.0y")
    serialization += "panel%s/clen           = %8.7e\n" % (panel_id_str, distance)
    serialization += "panel%s/res            = %8.7e\n" % (panel_id_str, 1 / simeple_config["pixel_size"])
    serialization += "panel%s/coffset        = %8.7e\n" % (panel_id_str, 0)
    serialization += "panel%s/px             = %d\n" % (panel_id_str, simeple_config["fast_pixels"])
    serialization += "panel%s/py             = %d\n" % (panel_id_str, simeple_config["slow_pixels"])
    serialization += "panel%s/pix_width      = %8.7e\n" % (panel_id_str, simeple_config["pixel_size"])
    serialization += "panel%s/d              = %8.7e\n" % (panel_id_str, distance)
    serialization += "panel%s/corner_x       = %d\n" % (panel_id_str, corner_x)
    serialization += "panel%s/corner_y       = %d\n" % (panel_id_str, corner_y)
    serialization += "\n"
    # fmt: on

    with open(file_name, "w") as fh:
        fh.write(serialization)


def saveH5(path_to_files):
    """
    Private method to save the object to a file. Creates links to h5 files that all contain only one pattern.

    :param output_path: The file where to save the object's data.
    :type output_path: string, default b
    """

    # Setup new file.
    with h5py.File(path_to_files + ".h5", "w") as h5_outfile:
        # Files to read from.
        individual_files = [
            os.path.join(path_to_files, f) for f in os.listdir(path_to_files)
        ]
        individual_files.sort()

        # Keep track of global parameters being linked.
        global_parameters = False
        # Loop over all individual files and link in the top level groups.
        for ind_file in individual_files:
            # Open file.
            with h5py.File(ind_file, "r") as h5_infile:
                # Links must be relative.
                relative_link_target = os.path.relpath(
                    path=ind_file, start=os.path.dirname(os.path.dirname(ind_file))
                )

                # Link global parameters.
                if not global_parameters:
                    global_parameters = True

                    h5_outfile["params"] = h5py.ExternalLink(
                        relative_link_target, "params"
                    )
                    h5_outfile["info"] = h5py.ExternalLink(relative_link_target, "info")
                    h5_outfile["misc"] = h5py.ExternalLink(relative_link_target, "misc")
                    h5_outfile["version"] = h5py.ExternalLink(
                        relative_link_target, "version"
                    )

                for key in h5_infile["data"]:
                    # Link in the data.
                    ds_path = "data/%s" % (key)
                    h5_outfile[ds_path] = h5py.ExternalLink(
                        relative_link_target, ds_path
                    )


def get_solid_angle(geom_fn: str):
    """Get the solid angle array from a pysingfel geom file.

    Args:
        geom_fn (str): The geometry file in pysingfel format.

    Returns:
        ndarray: A 2D array of solid angles.
    """
    if not PYSINGFEL_AVAILABLE:
        err_info = (
            "Cannot find the 'pysingfel' module, which is required to run"
            + "SingFELDiffractionCalculator.backengine(). Did you install it following the instruction: https://simex-lite.readthedocs.io/en/latest/backengines/pysingfel.html"
        )
        raise ModuleNotFoundError(err_info)
    det = Detector(geom_fn)
    solidAngle = np.zeros((det.py, det.px))
    for ind_x in range(det.px):
        for ind_y in range(det.py):
            rx = (ind_x - det.cx) * det.pix_width
            ry = (ind_y - det.cy) * det.pix_height
            r = np.sqrt(rx**2 + ry**2)
            pixDist = np.sqrt(r**2 + det.d**2)
            ss = det.pix_width**2 / (4 * pixDist**2 + det.pix_width**2)
            solidAngle[ind_y, ind_x] = 4 * np.arcsin(ss)
    return solidAngle


def get_qmap(geom_fn: str, PMI_file: str):
    """Get the reciprocal space magnitude map from pysingfel geom and PMI file. q=2sin(theta)/lambda

    Args:
        geom_fn (str): The geometry file in pysingfel format.
        PMI_file (str): The PMI file in XMDYN format.

    Returns:
        ndarray: A 2D array of qmap.
    """
    if not PYSINGFEL_AVAILABLE:
        err_info = (
            "Cannot find the 'pysingfel' module, which is required to run"
            + "SingFELDiffractionCalculator.backengine(). Did you install it following the instruction: https://simex-lite.readthedocs.io/en/latest/backengines/pysingfel.html"
        )
        raise ModuleNotFoundError(err_info)
    det = Detector(geom_fn)
    beam = Beam(None)
    setEnergyFromFile(PMI_file, beam)
    print("Beam energy =", beam.photon_energy)
    det.init_dp(beam)
    return det.q_mod / 1e10
