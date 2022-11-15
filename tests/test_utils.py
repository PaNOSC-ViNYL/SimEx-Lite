import pytest
# from .logger_module import info_log
from pathlib import Path
from SimExLite.utils.geometry import writeSimpleGeometry


# def test_setLogger(capsys, caplog):
#     """Test the setLooger."""
#     info_log()
#     captured = capsys.readouterr()
#     print(caplog.text)
#     print(captured.err)
#     print(captured.out)
#     assert "tests.logger_module" in caplog.text
#     # assert "tests.logger_module" in captured.err


def test_write_simple_geometry(tmpdir):
    writeSimpleGeometry(str(tmpdir / "test.geom"))


if __name__ == "__main__":
    test_write_simple_geometry(Path("./"))
