import pytest

import sys
from pathlib import Path

WPG_path = "/home/juncheng/GPFS/exfel/data/user/juncheng/WPG"
sys.path.insert(0, WPG_path)
from libpyvinyl.Instrument import Instrument
from libpyvinyl.BaseData import DataCollection
from SimExLite.SampleData import SampleData, ASEFormat
from SimExLite.SourceCalculators import GaussianSourceCalculator
from SimExLite.PropagationCalculators import WPGPropagationCalculator
from SimExLite.PMICalculators import SimpleScatteringPMICalculator


def test_CalculationInstrument(tmpdir):
    """PlusCalculator test function, the native output of MinusCalculator is a python dictionary"""

    source = GaussianSourceCalculator("gaussian_source", WPG_path)
    source.parameters["photon_energy"] = 9000
    soruce_data = source.output
    propogation = WPGPropagationCalculator(name="WPGCalculator", input=soruce_data)
    prop_data_collection = propogation.output
    prop_data = prop_data_collection.to_list()[0]
    sample_file = "./testFiles/2nip.pdb"
    sample_data = SampleData.from_file(sample_file, ASEFormat, "sample_data")
    pmi_input = DataCollection(sample_data, prop_data)
    pmi = SimpleScatteringPMICalculator(name="PMI_calculator", input=pmi_input)

    calculation_instrument = Instrument("SPB_instrument")
    instrument_path = tmpdir / "SPB_instrument"
    calculation_instrument.add_calculator(source)
    calculation_instrument.add_calculator(propogation)
    calculation_instrument.add_calculator(pmi)
    calculation_instrument.set_instrument_base_dir(str(instrument_path))
    for calculator in calculation_instrument.calculators.values():
        print(calculator.name)
        print(calculator.parameters)
    print("Backengine output:")
    calculation_instrument.run()
    pmi.output.get_data()

if __name__ == "__main__":
    my_path = Path("./")
    test_CalculationInstrument(my_path)
