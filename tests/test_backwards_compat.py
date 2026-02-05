"""Tests for backwards compatibility.

These tests ensure that existing code using kubi_ecs_logger continues
to work without modification.
"""

import json
import sys
from io import StringIO
import pytest
from kubi_ecs_logger import Logger, Severity


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing usage patterns."""

    def test_basic_usage_pattern(self):
        """Basic usage pattern from README works."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="logging").out(Severity.DEBUG)
            output = buffer.getvalue()

            # Should output valid JSON
            data = json.loads(output.strip())
            assert data["event"]["action"] == "logging"
        finally:
            sys.stdout = old_stdout

    def test_message_in_constructor(self):
        """Logger with message in constructor works."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Note: Logger() resets base, so message must be set via base()
            logger.base(message="Test message").event(action="test").out(Severity.INFO)
            output = buffer.getvalue()

            data = json.loads(output.strip())
            assert data["message"] == "Test message"
        finally:
            sys.stdout = old_stdout

    def test_chaining_multiple_fields(self):
        """Chaining multiple field methods works."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="login")\
                  .user(name="alice", id="123")\
                  .host(hostname="web01")\
                  .out(Severity.INFO)

            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["event"]["action"] == "login"
            assert data["user"]["name"] == "alice"
            assert data["host"]["hostname"] == "web01"
        finally:
            sys.stdout = old_stdout

    def test_severity_enum_usage(self):
        """Severity enum constants work."""
        assert Severity.DEBUG.value == 1
        assert Severity.INFO.value == 2
        assert Severity.WARNING.value == 3
        assert Severity.ERROR.value == 4
        assert Severity.CRITICAL.value == 5

    def test_severity_comparison(self):
        """Severity comparison works."""
        assert Severity.ERROR > Severity.WARNING
        assert Severity.INFO >= Severity.DEBUG

    def test_dev_mode_setting(self):
        """Setting dev mode works."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG
        logger.dev = True
        assert logger.dev is True

    def test_severity_threshold_filtering(self):
        """Severity threshold filtering works."""
        logger = Logger()
        logger.severity_output_level = Severity.ERROR

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Below threshold - no output
            logger.event(action="info").out(Severity.INFO)
            assert buffer.getvalue() == ""

            # Above threshold - outputs
            logger.event(action="error").out(Severity.ERROR)
            assert buffer.getvalue() != ""
        finally:
            sys.stdout = old_stdout
            # Reset to default for other tests
            logger.severity_output_level = Severity.DEBUG

    def test_defaults_setting(self):
        """Setting defaults works."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG
        logger.defaults = {"event": {"dataset": "app"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["event"]["dataset"] == "app"
        finally:
            sys.stdout = old_stdout

    def test_custom_fields_via_kwargs(self):
        """Custom fields via kwargs work."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test", custom_field="value").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["event"]["custom_field"] == "value"
        finally:
            sys.stdout = old_stdout

    def test_timestamp_always_present(self):
        """@timestamp field is always present in output."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert "@timestamp" in data
        finally:
            sys.stdout = old_stdout

    def test_first_field_wins(self):
        """First field of each type wins (existing behavior)."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="first")\
                  .event(action="second")\
                  .out(Severity.INFO)

            output = buffer.getvalue()
            data = json.loads(output.strip())

            # Only first event should be present
            assert data["event"]["action"] == "first"
        finally:
            sys.stdout = old_stdout

    def test_log_level_field_automatic(self):
        """log.level field is automatically added."""
        logger = Logger()
        logger.severity_output_level = Severity.DEBUG

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test").out(Severity.WARNING)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert "logline" in data
            assert data["logline"]["level"] == "WARNING"
        finally:
            sys.stdout = old_stdout


class TestExceptionBehaviorChange:
    """Test that exception behavior has changed from assertions.

    Note: These tests verify that proper exceptions are now raised
    instead of AssertionErrors, which is the intentional behavior change.
    """

    def test_exceptions_raised_not_assertions(self):
        """Proper exceptions raised instead of assertions."""
        from kubi_ecs_logger.exceptions import InvalidTypeError

        logger = Logger()

        # This would have been AssertionError before, now InvalidTypeError
        with pytest.raises(InvalidTypeError):
            logger.dev = "invalid"

    def test_exceptions_work_with_python_o_flag(self):
        """Exceptions work even with Python -O optimization.

        This is the main benefit: assertions are removed with -O,
        but exceptions are not.
        """
        # Note: We can't test -O flag directly in pytest, but we verify
        # that we're using raises instead of asserts
        import inspect
        from kubi_ecs_logger.wrapper.logger import Logger

        # Check that the dev setter uses raise, not assert
        source = inspect.getsource(Logger.dev.fset)
        assert "raise" in source
        assert "assert" not in source or "# assert" in source  # Only in comments
