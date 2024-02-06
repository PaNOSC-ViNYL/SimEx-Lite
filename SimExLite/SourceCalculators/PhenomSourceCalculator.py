""":module PhenomCalculator: Module that holds the PhenomCalculator class.  """
import h5py
import numpy as np
from SimExLite.utils.Logger import setLogger
from SimExLite.WavefrontData import WavefrontData, WPGFormat
from SimExLite.utils.Logger import setLogger
from libpyvinyl import BaseCalculator, CalculatorParameters

try:
    from phenom.source import sase_pulse

    PHENOM_AVAILABLE = True
except ModuleNotFoundError:
    PHENOM_AVAILABLE = False


# WPG is necessary to execute the calculator, but it's not a hard dependency of SimExLite.
try:
    from phenom.wpg import complex_to_wpg
    from wpg import Wavefront
    from wpg.srw import srwlpy

    WPG_AVAILABLE = True
except ModuleNotFoundError:
    WPG_AVAILABLE = False


logger = setLogger("PhenomSourceCalculator")


class PhenomSourceCalculator(BaseCalculator):
    """
    Class calculating a x-ray free electron laser photon source under the gaussian assumption.

    Args:
        name (str): The name of this calculator.
        output_keys (str, optional): The key(s) of this calculator's output data. It's a list of ``str``s or
            a single str. Defaults to "Gaussian_wavefront".
        output_filenames (str, optional): The output filename of this calculator. Defaults to "wavefront.h5".
            instrument_base_dir (str, optional): The base directory for the instrument to which this calculator
            belongs. Defaults to "./". The final exact output file path depends on ``instrument_base_dir``
            and ``calculator_base_dir``: ``instrument_base_dir``/``calculator_base_dir``/filename.
        calculator_base_dir (str, optional): The base directory for this calculator. Defaults to "./". The final
            exact output file path depends on `instrument_base_dir` and `calculator_base_dir`:
            ``instrument_base_dir``/``calculator_base_dir``/filename.
    """

    def __init__(
        self,
        name: str,
        output_keys: str = "Phenom_wavefront",
        output_filenames: str = "wavefront.h5",
        instrument_base_dir="./",
        calculator_base_dir="PhenomSourceCalculator",
        parameters=None,
    ):
        # Issue a warning if WPG is not available.
        if not WPG_AVAILABLE:
            logger.warning(
                'Cannot find the "WPG" module, which is required to run\n'
                "PhenomSourceCalculator.backengine(). Is it included in PYTHONPATH?\n"
                "If not, set your WPG path with 'import sys; sys.path.append(WPG_PATH)' before importing this module."
            )

        # Init parent class.
        super().__init__(
            name,
            None,
            output_keys,
            output_data_types=WavefrontData,
            output_filenames=output_filenames,
            instrument_base_dir=instrument_base_dir,
            calculator_base_dir=calculator_base_dir,
            parameters=parameters,
        )

    def init_parameters(self):
        """
        Initialize calculator parameters.
        """
        parameters = CalculatorParameters()

        range_x = parameters.new_parameter(
            "range_x",
            comment="The spacial mesh range in x direction. [start, end]",
            unit="meter",
        )
        range_x.value = [-250e-6, 250e-6]

        num_x = parameters.new_parameter(
            "num_x", comment="Number of mesh points in x direction."
        )
        num_x.value = 500

        range_y = parameters.new_parameter(
            "range_y",
            comment="The spacial mesh range in y direction. [start, end]",
            unit="meter",
        )
        range_y.value = [-250e-6, 250e-6]

        num_y = parameters.new_parameter(
            "num_y", comment="Number of mesh points in y direction."
        )
        num_y.value = 500

        range_t = parameters.new_parameter(
            "range_t", comment="The temporal range. [start, end]", unit="s"
        )
        range_t.value = [-25e-15, 25e-15]

        num_t = parameters.new_parameter(
            "num_t", comment="Number of mesh points in t direction."
        )
        num_t.value = 250

        photon_energy = parameters.new_parameter(
            "photon_energy", comment="The photon energy of X-ray beam.", unit="eV"
        )
        photon_energy.value = 10e3

        pulse_energy = parameters.new_parameter(
            "pulse_energy", comment="Total energy of the pulse", unit="joule"
        )
        pulse_energy.value = 1e-4

        pulse_duration = parameters.new_parameter(
            "pulse_duration", comment="The length of a pulse", unit="second"
        )
        pulse_duration.value = 15e-15

        spectral_bandwidth = parameters.new_parameter(
            "spectral_bandwidth",
            comment="The bandwith of the beam spectrum (\delta E/E)",
        )
        spectral_bandwidth.value = 1e-3

        sigma = parameters.new_parameter(
            "sigma",
            comment="sigma value",
        )
        sigma.value = 50e-06

        div = parameters.new_parameter(
            "div",
            comment="div value",
        )
        div.value = 2.5e-03

        self.parameters = parameters

    def _ensure_unit(self, param: str, unit: str):
        """Ensure the unit is correct"""
        return self.parameters[param].value_no_conversion.to(unit).magnitude

    def backengine(self):

        # check for WPG first
        if not WPG_AVAILABLE:
            raise ModuleNotFoundError(
                'Cannot find the "WPG" module, which is required to run\n'
                "PhenomSourceCalculator.backengine(). Is it included in PYTHONPATH?\n"
                "If not, set your WPG path with 'import sys; sys.path.append(WPG_PATH)' before import this module."
            )

        pulse_energy = self._ensure_unit("pulse_energy", "joule")
        photon_energy = self._ensure_unit("photon_energy", "eV")
        pulse_duration = self._ensure_unit("pulse_duration", "second")
        bandwidth = self.parameters["spectral_bandwidth"].value
        sigma = self.parameters["sigma"].value
        div = self.parameters["div"].value
        range_x = self._ensure_unit("range_x", "meter")
        range_y = self._ensure_unit("range_y", "meter")
        range_t = self._ensure_unit("range_t", "second")

        x = np.linspace(range_x[0], range_x[1], self.parameters["num_x"].value)
        y = np.linspace(range_y[0], range_y[1], self.parameters["num_y"].value)
        t = np.linspace(range_t[0], range_t[1], self.parameters["num_t"].value)

        # Construct the pulse.
        pulse = sase_pulse(
            x=x,
            y=y,
            t=t,
            photon_energy=photon_energy,
            pulse_energy=pulse_energy,
            pulse_duration=pulse_duration,
            bandwidth=bandwidth,
            sigma=sigma,
            div=div,
            x0=0.0,
            y0=0.0,
            t0=0.0,
            theta_x=0.0,
            theta_y=0.0,
        )

        key = self.output_keys[0]
        filename = self.output_file_paths[0]
        output_data = self.output[key]

        photon_energy = photon_energy
        nx, ny, nt = pulse.shape
        wfr = Wavefront()
        # Setup E-field.
        wfr.data.arrEhor = np.zeros(shape=(nx, ny, nt, 2))
        wfr.data.arrEver = np.zeros(shape=(nx, ny, nt, 2))

        wfr.params.wEFieldUnit = "sqrt(W/mm^2)"
        wfr.params.photonEnergy = photon_energy
        wfr.params.wDomain = "time"
        wfr.params.Mesh.nSlices = nt
        wfr.params.Mesh.nx = nx
        wfr.params.Mesh.ny = ny

        wfr.params.Mesh.sliceMin = np.min(t)
        wfr.params.Mesh.sliceMax = np.max(t)

        wfr.params.Mesh.xMin = np.min(x)
        wfr.params.Mesh.xMax = np.max(x)
        wfr.params.Mesh.yMin = np.min(y)
        wfr.params.Mesh.yMax = np.max(y)

        wfr.params.Rx = 1
        wfr.params.Ry = 1

        wfr.data.arrEhor = complex_to_wpg(pulse)
        srwlpy.SetRepresElecField(wfr._srwl_wf, "frequency")

        wfr.store_hdf5(filename)

        output_data.set_file(filename, WPGFormat)

        return self.output
