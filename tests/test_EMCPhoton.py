import numpy as np
import SimExLite.DataAPI.EMCPhoton as EMC
from SimExLite.DiffractionData import DiffractionData
from pathlib import Path
import shutil


def test_RandomData(tmp_path):
    data = (np.random.rand(10, 25)**5 * 5).astype(np.int32)
    data_fn = str(tmp_path / "t.bin")
    EMC.dense_to_PatternsSOne(data).write(data_fn)
    if __name__ == "__main__":
        EMC.plotEMCbin(data_fn, 3)


def test_EMC_geometry(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    out_path = tmp_path / "t.bin"
    diffr.multiply(1e5)
    data_fn = str(out_path)
    geom_path = out_path.with_suffix('.geom')
    diffr.saveAs('emc', data_fn, with_geom=True)
    assert out_path.is_file() is True
    assert geom_path.is_file() is True


def test_plotEMC(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    out_path = tmp_path / "t.emc"
    diffr.multiply(1e5)
    data_fn = str(out_path)
    diffr.saveAs('emc', data_fn)
    if __name__ == "__main__":
        EMC.plotEMCPhoton(data_fn, 0, log_scale=True)
    assert out_path.is_file() is True


def test_pattern_total_h5(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    out_path = tmp_path / "t.emc"
    diffr.multiply(1e5)
    data_fn = str(out_path)
    diffr.saveAs('emc', data_fn)
    emc = EMC.EMCPhoton(data_fn)
    assert emc.pattern_total == 13


def test_pattern_total_binary(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    out_path = tmp_path / "t.emc"
    data_fn = str(out_path)

    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    arr = diffr.array * 1e5
    data = []
    for pattern in arr:
        data.append(pattern.flatten())
    patterns = EMC.dense_to_PatternsSOne(np.array(data))
    patterns.write(data_fn)
    emc = EMC.EMCPhoton(data_fn)
    assert emc.pattern_total == 13


def test_EMC_format(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    dd = DiffractionData(h5_file)
    dd.setArray()
    out_path = tmp_path / "test.emc"
    dd.saveAs("emc", str(out_path))
    assert EMC.isEMCH5(str(out_path)) is True


def test_EMC_format_false(tmp_path):
    h5_file = './testFiles/singfel-multi.h5'
    assert EMC.isEMCH5(str(h5_file)) is False
    touch_file = tmp_path / 'test.txt'
    touch_file.touch()
    assert EMC.isEMCH5(str(touch_file)) is False


def test_setArray(tmp_path):
    diffr_path = './testFiles/singfel-multi.h5'
    diffr = DiffractionData(diffr_path)
    diffr.setArray()
    out_path = tmp_path / "t.emc"
    diffr.multiply(1e5)
    data_fn = str(out_path)
    diffr.saveAs('emc', data_fn)
    emc = EMC.EMCPhoton(data_fn)
    emc.setArray()


if __name__ == "__main__":
    path_name = "tmp"
    tmp = Path(path_name)
    tmp.mkdir(parents=True, exist_ok=True)
    test_RandomData(tmp)
    test_plotEMC(tmp)
    test_EMC_geometry(tmp)
    shutil.rmtree(path_name)
