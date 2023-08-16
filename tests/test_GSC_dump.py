import pytest
from SimExLite.SourceCalculators import GaussianSourceCalculator
import dill


def test_dump_directly(tmp_path):
    tmpf = str(tmp_path/"dumptest.dump")
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=str(tmp_path))
    dill.dump(gsc,open(tmpf, "wb"))
    test_obj = dill.load(open(tmpf, "rb"))
    isinstance(test_obj, GaussianSourceCalculator)
    # gsc.from_dump(tmpf)

def test_dump_and_load(tmp_path):
    "Check if dumping and loading an instrument works and leaves parameters unchanged."
    tmpf = str(tmp_path/"dumptest.dump")
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=str(tmp_path))
    # gsc.backengine()
    gsc.dump(tmpf)
    GaussianSourceCalculator.from_dump(tmpf)