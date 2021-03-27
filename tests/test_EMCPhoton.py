import numpy as np
import SimExLite.DataAPI.EMCPhoton as EMC
from pathlib import Path
import shutil


def test_RandomData(tmp_path):
    data = (np.random.rand(10, 25)**5 * 5).astype(np.int32)
    data_fn = str(tmp_path / "t.bin")
    EMC.dense_to_PatternsSOne(data).write(data_fn)
    EMC.plotEMCPhoton(data_fn, 3)


if __name__ == "__main__":
    path_name = "tmp"
    tmp = Path(path_name)
    tmp.mkdir(parents=True, exist_ok=True)
    test_RandomData(tmp)
    # tmp.rmdir()
    shutil.rmtree(path_name)
