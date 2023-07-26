
# Copyright (C) 2023 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

import os
from pathlib import Path
from subprocess import Popen, PIPE
import shlex
import h5py
import numpy as np
from libpyvinyl.BaseCalculator import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.DiffractionData import DiffractionData, SingFELFormat
from SimExLite.PhotonBeamData import SimpleBeam
from SimExLite.utils.Logger import setLogger

logger = setLogger("SingFELPDBDiffractionCalculator")


class SingFELPDBDiffractionCalculator(BaseCalculator):
    """SingFEL diffraction pattern from pdb file calculator."""

    def __init__(
        self,
        name: str,
        input: DataCollection,
        sample: str,
        output_keys: str = "singfelPDB_diffraction",
        output_data_types=DiffractionData,
        output_filenames: str = "diffr.h5",
        instrument_base_dir="./",
        calculator_base_dir="SingFELPDBDiffractionCalculator",
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
        # The trait of this backengine makes the sample to be treated as
        # sample to check suffix.
        self.sample = sample

    def init_parameters(self):
        parameters = CalculatorParameters()
        random_rotation = parameters.new_parameter(
            "random_rotation",
            comment="If it's False, the orientations are fixed to ensure the SO3 space is always uniformly sampled."
            + " If it's True, it will be a random sampling complying a uniform distribution in the SO3 space",
        )
        random_rotation.value = True

        number_of_diffraction_patterns = parameters.new_parameter(
            "number_of_diffraction_patterns",
            comment="The number of diffraction patterns to generate",
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

        number_of_diffraction_patterns.value = 10
        pixel_size.value = 0.001
        pixels_x.value = 10
        pixels_y.value = 5
        distance.value = 0.13
        mpi_command.value = "mpirun -n 2"

        self.parameters = parameters

    def backengine(self):
        self.parse_input()
        exec_bin = Path(__file__).parent / "SingFELPDB.py"
        output_stem = str(Path(self.output_file_paths[0]).stem)
        output_dir = Path(self.output_file_paths[0]).parent / output_stem
        geom_file = self.get_geometry_file()
        beam_file = self.get_beam_file()
        uniform_rotation = not self.parameters["random_rotation"].value
        number_of_diffraction_patterns = self.parameters[
            "number_of_diffraction_patterns"
        ].value
        mpi_command = self.parameters["mpi_command"].value
        # fmt: off
        output_dir.mkdir(parents=True, exist_ok=False)
        # TODO: include single orientation
        command_sequence = ['python3',             str(exec_bin),
                            '--inputFile',         str(self.sample),
                            '--outputDir',        str(output_dir),
                            '--geomFile',         str(geom_file),
                            '--beamFile',         str(beam_file),
                            '--uniformRotation',  str(uniform_rotation),
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

    def parse_input(self):
        """Check the beam data"""
        assert len(self.input) == 1
        # self.sample_fn = self.input.to_list()[0]
        self.photon_beam = self.input.to_list()[0]
        assert isinstance(self.photon_beam, SimpleBeam)
        
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

    def get_beam_file(self):
        filename = str(Path(self.base_dir) / "singfel.beam")
        photon_energy = self.photon_beam.get_photon_energy().magnitude
        n_photons = self.photon_beam.get_photons_per_pulse().magnitude
        beam_size = self.photon_beam.get_beam_size().magnitude
        # To get the same area
        diameter = np.sqrt(beam_size[0]*beam_size[1])
        write_singfel_beam_file(filename, photon_energy, n_photons, diameter)
        return filename


def write_singfel_beam_file(file_name, photon_energy, n_photons, diameter):
    """Write the beam file for pysingfel

    :param file_name: The file name of the beam file.
    :type output_path: string
    :param photon_energy: The photon energy in eV.
    :type photon_energy: float
    :param n_photons: The number of photons per pulse.
    :type n_photons: float
    :param diameter: The diameter of a round beam spot.
    :type diameter: float
    """
    strings = f"beam/photon_energy = {photon_energy}\n"
    strings += f"beam/fluence = {n_photons}\n"
    # This 'radius' is treated as diameter in pysingfel'
    strings += f"beam/radius = {diameter}\n"
    with open(file_name, "w") as fh:
        fh.write(strings)


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
