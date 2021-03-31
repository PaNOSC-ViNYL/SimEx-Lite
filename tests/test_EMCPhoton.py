import numpy as np
import SimExLite.DataAPI.EMCPhoton as EMC
from SimExLite.DiffractionData import DiffractionData
from pathlib import Path
import shutil


def test_RandomData(tmp_path):
    data = (np.random.rand(10, 25)**5 * 5).astype(np.int32)
    data_fn = str(tmp_path / "t.bin")
    EMC.dense_to_PatternsSOne(data).write(data_fn)
    EMC.plotEMCPhoton(data_fn, 3)


def test_MultiData(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    data_fn = str(tmp_path / "t.bin")
    diffr.saveAs('emc', data_fn)
    EMC.plotEMCPhoton(data_fn, 3)


if __name__ == "__main__":
    path_name = "tmp"
    tmp = Path(path_name)
    tmp.mkdir(parents=True, exist_ok=True)
    # test_RandomData(tmp)
    test_MultiData(tmp)
    # tmp.rmdir()
    shutil.rmtree(path_name)
