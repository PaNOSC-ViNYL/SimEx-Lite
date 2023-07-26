# Copyright (C) 2023 Juncheng E
# Contact: Juncheng E <juncheng.e@xfel.eu>
# This file is part of SimEx-Lite which is released under GNU General Public License v3.
# See file LICENSE or go to <http://www.gnu.org/licenses> for full license details.
"""Gaussian Noise Detector Calculator Module"""

from tqdm import tqdm
import copy
import numpy as np
from libpyvinyl.BaseCalculator import BaseCalculator, CalculatorParameters
from libpyvinyl.BaseData import DataCollection
from SimExLite.DiffractionData import DiffractionData
from SimExLite.utils.Logger import setLogger


logger = setLogger("GaussianNoiseCalculator")


def spliterate(buf, chunk):
    for start in range(0, len(buf), chunk):
        # print(start, start+chunk)
        yield buf[start : start + chunk]


class GaussianNoiseCalculator(BaseCalculator):
    """Implement Gaussian noise to input diffraction data"""

    def __init__(
        self,
        name: str,
        input: DataCollection,
        output_keys: str = "diffr_GaussianNoise",
        output_data_types=DiffractionData,
        output_filenames: str = None,
        instrument_base_dir="./",
        calculator_base_dir="GaussianNoiseCalculator",
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
        mu = parameters.new_parameter(
            "mu",
            comment="The AUD/keV value of the one photon peak position, the unit needs to be consistent with that of the sigma slop and intercept. The default value is for AGIPD high-CDS mode.",
        )
        mu.value = 58.234

        sigma_slope = parameters.new_parameter(
            "sigma_slope",
            comment="The linear fitting slope for sigma. The unit needes to be consistent with that of the mu value. The default value is for AGIPD high-CDS mode.",
        )
        sigma_slope.value = 1.814

        sigma_intercept = parameters.new_parameter(
            "sigma_intercept",
            comment="The linear fitting intercept for sigma. The unit needes to be consistent with that of the mu value. The default value is for AGIPD high-CDS mode.",
        )
        sigma_intercept.value = 9.041

        chunk_size = parameters.new_parameter(
            "chunk_size", comment="To manipulate the data in memory in chunk."
        )
        chunk_size.value = 10000

        copy_input = parameters.new_parameter(
            "copy_input",
            comment="If it's true, the output of this calculator a new copy from the input data will be used. File mapping input is not affected by this option and will always be copied.",
        )
        copy_input.value = False

        self.parameters = parameters

    def backengine(self):
        """Method to do the actual calculation."""
        self.parse_input()
        if self.parameters["copy_input"].value:
            if self.input_data.mapping_type == dict:
                work_data = copy.deepcopy(self.input_data)
            else:
                work_data = self.input_data
        else:
            work_data = self.input_data
        data_dict = work_data.get_data()
        key = self.output_keys[0]
        output_data = self.output[key]
        output_data.set_dict(data_dict)

        diffr_arr = data_dict["img_array"]
        mu = self.parameters["mu"].value
        sigma_slope = self.parameters["sigma_slope"].value
        sigma_intercept = self.parameters["sigma_intercept"].value
        output_data.addGaussianNoise(mu, [sigma_slope, sigma_intercept])
        logger.info("Convert back to nphotons...")
        chunk_size = self.parameters["chunk_size"].value
        output_data.multiply(1 / mu, chunk_size)
        logger.info("Get round values...")
        for arr in tqdm(
            spliterate(diffr_arr, chunk_size),
            total=int(np.ceil(float(len(diffr_arr)) / chunk_size)),
        ):
            arr[:] = np.round(arr)
            arr[arr < 0] = 0
        output_data.setArrayDataType("i4")
        return self.output

    def parse_input(self):
        """Check the beam data"""
        assert len(self.input) == 1
        self.input_data = self.input.to_list()[0]
        assert isinstance(self.input_data, DiffractionData)
