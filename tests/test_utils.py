import pytest
from .logger_module import info_log


def test_setLogger(caplog):
    """Test the setLooger."""
    info_log()
    assert "tests.logger_module" in caplog.text
