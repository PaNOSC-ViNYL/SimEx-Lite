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
        calculator_base_dir="CrystfelDiffractionCalculator",
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
            comment="Use pointgroup as the symmetry of the intensity list. E.g. '422' for Lysozyme.",
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
        intensities_fn.value = None
        gaussian_background.value = [0.0, 0.0]
        point_group.value = None
        geometry_fn.value = None
        beam_radius.value = 5e-6
        max_crystal_size.value = 5e-8
        min_crystal_size.value = 5e-8
        gpu.value = False
        spectrum.value = "tophat"

        self.parameters = parameters

    def backengine(self):
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
        intensities_fn = self.__get_intensities_file()

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
        print(*command_sequence)

        # # Executing:
        proc = Popen(command_sequence, stdin=PIPE, stdout=PIPE, stderr=PIPE)

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
        logger.info(f'Writting in CXI format to "{output_fn}" ...')
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

    def __get_intensities_file(self):
        if self.parameters["intensities_fn"].value is None:
            fn = pkg_resources.resource_filename(
                "SimExLite.DiffractionCalculators", "agipd_simple_2d.geom"
            )
        else:
            fn = self.parameters["intensities_fn"].value
        return fn
