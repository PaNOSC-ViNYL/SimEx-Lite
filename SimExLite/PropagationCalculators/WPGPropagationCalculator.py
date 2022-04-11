""":module WPGPropagationCalculator: Module that holds the WPGPropagationCalculator class."""

from pathlib import Path
import shutil
import sys

from libpyvinyl import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from SimExLite.utils.Logger import setLogger

logger = setLogger(__name__)

# WPG (https://github.com/samoylv/WPG) is neccessary to execute the calculator,
# but it's not a hard dependency of SimExLite.
try:
    from wpg.generators import build_gauss_wavefront
    from wpg import Wavefront
    from s2e.prop import propagate_s2e

    WPG_AVAILABLE = True
except ModuleNotFoundError:
    WPG_AVAILABLE = False


class WPGPropagationCalculator(BaseCalculator):
    """:class WPGPropagationCalculator: Class representing photon propagation through X-ray optics."""

    def __init__(
        self,
        name: str,
        input: DataCollection,
        output_keys: str = "WPG_wavefront",
        output_data_types=WavefrontData,
        output_filenames: str = "wavefront.h5",
        instrument_base_dir="./",
        calculator_base_dir="WPGPropagationCalculator",
        parameters=None,
    ):
        if not WPG_AVAILABLE:
            logger.warning('Cannot find the "WPG" module, which is required to run '
                    'WPGPropagationCalculator.backengine(). Is it included in PYTHONPATH?'
                )
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
        beamline_config = parameters.new_parameter(
            "beamline_config_file", comment="The beamline_configfile"
        )
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        simple_beamline_fn = str(Path(self.base_dir) / "simple_beamline.py")
        beamline_config.value = create_simple_beamline_file(simple_beamline_fn)

        self.parameters = parameters

    def prep_beamline_config(self):
        """Copy the beamline config file to the working dir to import the beamline module"""
        beamline_config_fn = self.parameters["beamline_config_file"].value
        dst_path = Path(self.base_dir) / "WPG_beamline.py"
        shutil.copyfile(beamline_config_fn, str(dst_path))

    def get_input_fn(self):
        """Make sure the data is a mapping of WPGFormat file"""
        assert len(self.input) == 1
        input_data = self.input.to_list()[0]
        if input_data.mapping_type == WPGFormat:
            input_fn = input_data.filename
        else:
            filepath = Path(self.base_dir) / "input_wavefront.h5"
            input_data.write(str(filepath), WPGFormat)
            input_fn = str(filepath)

        return input_fn

    def backengine(self)->DataCollection:

        # check for WPG first
        if not WPG_AVAILABLE:
            raise ModuleNotFoundError(
                'Cannot find the "WPG" module, which is required to run '
                "WPGPropagationCalculator.backengine(). Is it included in PYTHONPATH?"
            )

        self.prep_beamline_config()

        input_fn = self.get_input_fn()
        output_fn = str(Path(self.base_dir) / self.output_filenames[0])

        propagate_s2e.propagate(input_fn, output_fn, WPG_beamline.get_beamline)

        assert len(self.output_keys) == 1
        key = self.output_keys[0]
        output_data = self.output[key]
        output_data.set_file(output_fn, WavefrontData)

        return self.output


def create_simple_beamline_file(filename: str):
    """Create a simple beamline file for the default setting"""
    strings = """def get_beamline():

        distance = 300.
        foc_dist = 2.

        import wpg.optical_elements
        from wpg.optical_elements import Use_PP

        drift0 = wpg.optical_elements.Drift(distance)
        lens0  = wpg.optical_elements.Lens(foc_dist, foc_dist)
        drift1 = wpg.optical_elements.Drift(1./(1./foc_dist-1./distance))

        bl0 = wpg.Beamline()
        bl0.append(drift0, Use_PP(semi_analytical_treatment=1, zoom=0.50, sampling=8))
        bl0.append(lens0,  Use_PP())
        bl0.append(drift1, Use_PP(semi_analytical_treatment=1, zoom=4.2,  sampling=0.5))

        return bl0"""
    with open(filename, "w") as fh:
        fh.write(strings)
    return filename
