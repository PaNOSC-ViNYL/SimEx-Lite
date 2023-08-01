# Copyright (C) 2022 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.

from pathlib import Path
from subprocess import Popen, PIPE
import pkg_resources
import time
from libpyvinyl.BaseCalculator import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.PhotonBeamData import SimpleBeam
from SimExLite.DetectorData import DetectorData, CXIFormat
from SimExLite.SampleData import ASEFormat
from SimExLite.utils.Logger import setLogger
from .convert_sim_to_CXI import convert_to_CXI

logger = setLogger("CrystfelDiffractionCalculator")


class CrystfelDiffractionCalculator(BaseCalculator):
    """Crystfel diffraction pattern calculator."""

    def __init__(
        self,
        name: str,
        input: DataCollection,
        output_keys: str = "crystfel_diffraction",
        output_data_types=DetectorData,
        output_filenames: str = "diffr.cxi",
        instrument_base_dir="./",
        calculator_base_dir=None,
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
        geometry_fn = parameters.new_parameter(
            "geometry_fn",
            comment="The path of the geometry file in crystfel format (Cheetah style).",
        )
        number_of_diffraction_patterns = parameters.new_parameter(
            "number_of_diffraction_patterns",
            comment="The number of diffraction patterns to calculate",
        )
        number_of_diffraction_patterns.add_interval(
            min_value=2, max_value=None, intervals_are_legal=True
        )

        random_rotation = parameters.new_parameter(
            "random_rotation",
            comment="If it's False, the orientation of the sample will not change."
            + " If it's True, it will be a random sampling in the SO3 space",
        )
        really_random = parameters.new_parameter(
            "really_random",
            comment="Seed the random number generator using the kernel random number generator (/dev/urandom)."
            + "This means that truly random numbers for the orientation and crystal size,"
            + "instead of the same sequence being used for each new run.",
        )
        beam_bandwidth = parameters.new_parameter(
            "beam_bandwidth",
            comment="The wavelength bandwidth, expressed as a decimal fraction applying to to wavelengths"
            + "Note: When using the two-colour or SASE spectrum, the spectrum calculation actually takes this value to be the bandwidth applying to the photon energies"
            + "instead of the wavelengths. For small bandwidths, the difference should be very small. Sorry for the horrifying inconsistency.",
        )
        photon_energy = parameters.new_parameter(
            "photon_energy", comment="The mean photon energy", unit="eV"
        )
        pulse_energy = parameters.new_parameter(
            "pulse_energy", comment="Total energy of the pulse", unit="joule"
        )
        beam_radius = parameters.new_parameter(
            "beam_radius", comment="The radius of the X-ray beam", unit="meter"
        )
        spectrum = parameters.new_parameter(
            "spectrum", comment="The spectrum of the X-ray beam"
        )
        spectrum.add_option(["tophat", "sase", "twocolour"], options_are_legal=True)

        point_group = parameters.new_parameter(
            "point_group",
            comment="Use point group as the symmetry of the intensity list. E.g. '422' for Lysozyme.",
        )
        space_group = parameters.new_parameter(
            "space_group",
            comment="The space group used for sfs intensity calculation. E.g. 'P43212' for Lysozyme.",
        )

        intensities_resolution = parameters.new_parameter(
            "intensities_resolution",
            comment="The resolution used for sfs intensity calculation. The default value is 3 angstrom",
            unit="angstrom",
        )
        intensities_fn = parameters.new_parameter(
            "intensities_fn",
            comment="The file name of the intensities and phases at the reciprocal lattice points. If 'None' is provided,"
            + "the intensities will be calculated by gen-sfs in the CCP4 tools with the pointgroup provided in the parameters.",
        )
        max_crystal_size = parameters.new_parameter(
            "max_crystal_size", comment="The maximum crystal size.", unit="meter"
        )
        min_crystal_size = parameters.new_parameter(
            "min_crystal_size", comment="The minimum crystal size.", unit="meter"
        )
        gaussian_background = parameters.new_parameter(
            "gaussian_background",
            comment="If the parameter is [100, 5], a background complying a Gaussian distribution with mean = 100 and standard deviation = 5 will be added to the patterns."
            + "The unit is eV",
        )

        gpu = parameters.new_parameter(
            "gpu", comment="If the GPU is enabled for calculation."
        )

        random_rotation.value = True
        really_random.value = True
        number_of_diffraction_patterns.value = 2
        beam_bandwidth.value = 0.01
        photon_energy.value = 9.3e3
        pulse_energy.value = 2e-3
        gaussian_background.value = [0.0, 0.0]
        # With the file, one doesn't need to provide the following parameters
        intensities_fn.value = None

        # SFS intensity calculation
        intensities_resolution.value = 3.0
        space_group.value = None
        point_group.value = None

        geometry_fn.value = None
        beam_radius.value = 5e-6
        max_crystal_size.value = 5e-8
        min_crystal_size.value = 5e-8
        gpu.value = False
        spectrum.value = "tophat"

        self.parameters = parameters

    def backengine(self, is_convert_to_cxi: bool = True):
        """If `is_convert_to_cxi` is False, for debugging, will not convert the result to CXI."""
        input_fn = self.get_input_fn()
        output_fn = self.output_file_paths[0]
        tmp_dir_path = Path(self.base_dir) / "diffr"
        tmp_dir_path.mkdir(parents=True, exist_ok=True)
        fn_prefix = "diffr_out"
        tmp_output = str(tmp_dir_path / fn_prefix)
        param = self.parameters
        assert len(self.output_file_paths) == 1
        assert param["point_group"].value is not None
        geometry_fn = self.__get_geometry_file()
        intensities_fn = self.__get_intensities_file(input_fn)

        # These two noise settings are only for converting to CXI format
        noise_base = param["gaussian_background"].value[0]
        noise_std = param["gaussian_background"].value[1]
        # fmt: off
        command_sequence = ['pattern_sim',
                            '-p',               input_fn,
                            '--geometry',       geometry_fn,
                            '--output',         tmp_output,
                            '--number',         str(param["number_of_diffraction_patterns"].value),
                            '--beam-bandwidth', str(param["beam_bandwidth"].value),
                            '--nphotons',       str(self.__get_n_photons()),
                            '--beam-radius',    str(param["beam_radius"].value),
                            '--spectrum',       param["spectrum"].value,
                            '--intensities',    intensities_fn,
                            '--min-size',       str(param["min_crystal_size"].value*1e9),
                            '--max-size',       str(param["max_crystal_size"].value*1e9),
                            '-y',               str(param["point_group"].value)
                            ]
        # fmt: on
        if param["random_rotation"].value is True:
            command_sequence += ["--random-orientation"]
        if param["really_random"].value is True:
            command_sequence += ["--really-random"]
        if param["gpu"].value is True:
            command_sequence += ["--gpu"]
        # print(*command_sequence)

        # # Executing:
        try:
            proc = Popen(command_sequence, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except FileNotFoundError as e:
            if "pattern_sim" in str(e):
                raise RuntimeError(
                    "pattern_sim not found, please install crystfel: https://www.desy.de/~twhite/crystfel/manual-pattern_sim.html"
                )
            else:
                raise

        while proc.poll() is None:
            # Here the output of crystfel is in stderr
            output = proc.stderr.readline()
            if output:
                logger.info(output.decode("ascii").strip())

        # t0 = time.process_time()
        output, err = proc.communicate()
        # t1 = time.process_time()
        # print("Time spent", t1 - t0)

        rc = proc.returncode
        if rc != 0:
            print(output.decode("ascii"))
            raise RuntimeError(err.decode("ascii"))

        # Save in CXI format
        vds_ref_geom = pkg_resources.resource_filename(
            "SimExLite.DiffractionCalculators.convert_to_cxi_geoms",
            "agipd_2120_vds.geom",
        )
        # This is needed to convert the CXI script, not relevent to the geom used for crystfel simulation.
        sim_geom = pkg_resources.resource_filename(
            "SimExLite.DiffractionCalculators.convert_to_cxi_geoms",
            "detector_sim.geom",
        )
        # print(vds_ref_geom)
        # print(sim_geom)
        if is_convert_to_cxi:
            logger.info(f'Writting in CXI format to "{output_fn}" ...')
            convert_to_CXI(
                sim_geom,
                vds_ref_geom,
                str(tmp_dir_path),
                output_fn,
                f"{fn_prefix}.(\\d+).h5",
                noise_base,
                noise_std,
            )
        assert len(self.output_keys) == 1
        key = self.output_keys[0]
        output_data = self.output[key]
        output_data.set_file(self.output_file_paths[0], CXIFormat)
        logger.info(f"Done")
        return self.output

    def get_input_fn(self):
        """Make sure the data is sample data"""
        assert len(self.input) == 1
        input_data = self.input.to_list()[0]
        if input_data.mapping_type == ASEFormat:
            if Path(input_data.filename).suffix.lower() == ".pdb":
                # Keep in .pdb format
                input_fn = input_data.filename
            else:
                # Convert to .pdb format
                input_fn = str(Path(input_data.filename).with_suffix(".pdb"))
                input_data.write(input_fn, ASEFormat)
        else:
            # If it's in dict format
            filepath = Path(self.base_dir) / "sample.pdb"
            input_data.write(str(filepath), ASEFormat)
            input_fn = str(filepath)

        return input_fn

    def __get_n_photons(self):
        photon_energy = self.parameters["photon_energy"].value
        pulse_energy = self.parameters["pulse_energy"].value
        beam = SimpleBeam(photon_energy=photon_energy, pulse_energy=pulse_energy)
        return float(beam.get_photons_per_pulse())

    def __get_geometry_file(self):
        """Get the geometry file for crystfel simulation."""
        if self.parameters["geometry_fn"].value is None:
            # geom_path = Path(diffcalc.__file__).with_name("agipd_simple_2d.geom")
            geom_path = pkg_resources.resource_filename(
                "SimExLite.DiffractionCalculators", "agipd_simple_2d.geom"
            )
        else:
            geom_path = self.parameters["geometry_fn"].value
        return geom_path

    def __get_intensities_file(self, input_fn):
        if self.parameters["intensities_fn"].value is None:
            if self.parameters["space_group"].value is not None:
                logger.info(
                    "Intensities list file was not provided, will calculate them with the space_group, point_group and intensities_resolution parameters..."
                )
                space_group = self.parameters["space_group"].value
                point_group = self.parameters["point_group"].value
                resolution = self.parameters["intensities_resolution"].value

                command_sequence = [
                    "gen-sfs",
                    input_fn,
                    str(space_group),
                    str(resolution),
                    str(point_group),
                ]
                # print(command_sequence)
                # # Executing:
                proc = Popen(command_sequence, stdin=PIPE, stdout=PIPE, stderr=PIPE)

                while proc.poll() is None:
                    output = proc.stdout.readline()
                    if output:
                        logger.info(output.decode("ascii").strip())

                # t0 = time.process_time()
                output, err = proc.communicate()
                # t1 = time.process_time()
                # print("Time spent", t1 - t0)

                rc = proc.returncode
                if rc != 0:
                    if "sfall: command not found" in err.decode("ascii"):
                        err_txt = err.decode("ascii")
                        err_txt += "\nsfall not found, please install CCP4 (https://www.ccp4.ac.uk/html/index.html)."
                        raise RuntimeError(err_txt)
                    else:
                        print(output.decode("ascii"))
                        raise RuntimeError(err.decode("ascii"))

                logger.info(f"Save .hkl file in {input_fn}.hkl")
                return input_fn + ".hkl"
            else:
                err = "Intensity information is not provided.\n"
                err += 'Please set either parameters["intensities_fn"] or parameters["space_group"].'
                raise KeyError(err)
        elif self.parameters["space_group"].value is not None:
            err = 'parameters["intensities_fn"] and parameters["space_group"] cannot be set at the same time, '
            err += 'please set either "intensities_fn" or "space_group".'
            raise KeyError(err)
        else:
            fn = self.parameters["intensities_fn"].value
        return fn
