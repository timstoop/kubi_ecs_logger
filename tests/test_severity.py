"""Tests for Severity enum."""

import pytest
from kubi_ecs_logger import Severity
from kubi_ecs_logger.exceptions import InvalidSeverityError


class TestSeverityOrdering:
    """Test Severity enum ordering."""

    def test_severity_values(self):
        """Severity levels have correct numeric values."""
        assert Severity.DEBUG.value == 1
        assert Severity.INFO.value == 2
        assert Severity.WARNING.value == 3
        assert Severity.ERROR.value == 4
        assert Severity.CRITICAL.value == 5

    def test_severity_less_than(self):
        """Severity < comparison works correctly."""
        assert Severity.DEBUG < Severity.INFO
        assert Severity.INFO < Severity.WARNING
        assert Severity.WARNING < Severity.ERROR
        assert Severity.ERROR < Severity.CRITICAL

    def test_severity_greater_than(self):
        """Severity > comparison works correctly."""
        assert Severity.CRITICAL > Severity.ERROR
        assert Severity.ERROR > Severity.WARNING
        assert Severity.WARNING > Severity.INFO
        assert Severity.INFO > Severity.DEBUG

    def test_severity_less_than_or_equal(self):
        """Severity <= comparison works correctly."""
        assert Severity.DEBUG <= Severity.DEBUG
        assert Severity.DEBUG <= Severity.INFO

    def test_severity_greater_than_or_equal(self):
        """Severity >= comparison works correctly."""
        assert Severity.CRITICAL >= Severity.CRITICAL
        assert Severity.CRITICAL >= Severity.ERROR

    def test_severity_equality(self):
        """Severity == comparison works correctly."""
        assert Severity.INFO == Severity.INFO
        assert not (Severity.INFO == Severity.DEBUG)


class TestSeverityFromStr:
    """Test Severity.from_str() method."""

    def test_from_str_debug(self):
        """from_str converts 'debug' to DEBUG."""
        assert Severity.from_str("debug") == Severity.DEBUG

    def test_from_str_info(self):
        """from_str converts 'info' to INFO."""
        assert Severity.from_str("info") == Severity.INFO

    def test_from_str_warning(self):
        """from_str converts 'warning' to WARNING."""
        assert Severity.from_str("warning") == Severity.WARNING

    def test_from_str_error(self):
        """from_str converts 'error' to ERROR."""
        assert Severity.from_str("error") == Severity.ERROR

    def test_from_str_critical(self):
        """from_str converts 'critical' to CRITICAL."""
        assert Severity.from_str("critical") == Severity.CRITICAL

    def test_from_str_case_insensitive(self):
        """from_str is case-insensitive."""
        assert Severity.from_str("INFO") == Severity.INFO
        assert Severity.from_str("Info") == Severity.INFO
        assert Severity.from_str("iNfO") == Severity.INFO

    def test_from_str_invalid_raises_error(self):
        """from_str raises InvalidSeverityError for invalid input."""
        with pytest.raises(InvalidSeverityError, match="Invalid severity level: 'invalid'"):
            Severity.from_str("invalid")

    def test_from_str_invalid_with_various_inputs(self):
        """from_str raises InvalidSeverityError for various invalid inputs."""
        invalid_inputs = ["", "trace", "fatal", "notice", "123"]

        for invalid in invalid_inputs:
            with pytest.raises(InvalidSeverityError):
                Severity.from_str(invalid)
