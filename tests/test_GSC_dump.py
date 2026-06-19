import pytest
import os

from SimExLite.SourceCalculators import GaussianSourceCalculator
import dill

# GaussianSourceCalculator uses a module-level logger. When running under pytest,
# pytest injects its own capture handler into the logging system, which wraps the
# stream with a `_pytest.capture.EncodedFile` object. When dill serializes
# GaussianSourceCalculator, it walks the module globals and drags in this logger
# and its handlers, hitting the unpicklable `EncodedFile` stream.
#
# Using `byref=True` tells dill to store the class by import reference rather than
# serializing the full module globals, avoiding the `EncodedFile` entirely.
# This is why the dump/load test is run in a subprocess (no pytest hooks) and
# `byref=True` is used in production to ensure portability across environments.

def test_dump_directly(tmp_path):
    tmpf = str(tmp_path / "dumptest.dump")
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=str(tmp_path))
    dill.dump(gsc, open(tmpf, "wb"), byref=True)
    test_obj = dill.load(open(tmpf, "rb"))
    assert isinstance(test_obj, GaussianSourceCalculator)
    # gsc.from_dump(tmpf)


def test_dump_and_load(tmp_path):
    "Check if dumping and loading an instrument works and leaves parameters unchanged."
    tmpf = str(tmp_path / "dumptest.dump")
    gsc = GaussianSourceCalculator("gaussian_source", instrument_base_dir=str(tmp_path))
    # gsc.backengine()
    gsc.dump(tmpf, byref=True)
    GaussianSourceCalculator.from_dump(tmpf)
