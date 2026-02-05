"""Tests for Logger singleton and fluent interface."""

import json
import sys
from io import StringIO
import pytest
from kubi_ecs_logger import Logger, Severity
from kubi_ecs_logger.exceptions import InvalidTypeError


class TestLoggerSingleton:
    """Test Logger singleton behavior."""

    def test_singleton_returns_same_instance(self):
        """Multiple Logger() calls return the same instance."""
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_singleton_resets_base_on_call(self):
        """Logger() resets internal Base object."""
        logger = Logger()
        logger.event(action="first")

        # Reinitialize
        logger = Logger()

        # Should not have event from before
        assert not hasattr(logger._base, 'event')


class TestLoggerConfiguration:
    """Test Logger configuration properties."""

    def test_dev_mode_get_set(self, logger):
        """Dev mode can be set and retrieved."""
        logger.dev = True
        assert logger.dev is True
        logger.dev = False
        assert logger.dev is False

    def test_dev_mode_invalid_type(self, logger):
        """Setting dev to non-bool raises InvalidTypeError."""
        with pytest.raises(InvalidTypeError, match="dev must be a bool"):
            logger.dev = "true"

    def test_severity_output_level_get_set(self, logger):
        """Severity output level can be set and retrieved."""
        logger.severity_output_level = Severity.WARNING
        assert logger.severity_output_level == Severity.WARNING

    def test_severity_output_level_invalid_type(self, logger):
        """Setting severity_output_level to non-Severity raises error."""
        with pytest.raises(InvalidTypeError, match="severity_output_level must be a Severity"):
            logger.severity_output_level = "WARNING"

    def test_defaults_get_set(self, logger):
        """Defaults can be set and retrieved."""
        defaults = {"event": {"dataset": "myapp"}}
        logger.defaults = defaults
        assert logger.defaults == defaults

    def test_defaults_invalid_type(self, logger):
        """Setting defaults to non-dict raises InvalidTypeError."""
        with pytest.raises(InvalidTypeError, match="defaults must be a dict"):
            logger.defaults = ["event"]


class TestLoggerFluentInterface:
    """Test fluent interface and method chaining."""

    def test_base_returns_logger(self, logger):
        """base() returns Logger instance."""
        result = logger.base(message="test")
        assert result is logger

    def test_event_returns_logger(self, logger):
        """event() returns Logger instance."""
        result = logger.event(action="test")
        assert result is logger

    def test_user_returns_logger(self, logger):
        """user() returns Logger instance."""
        result = logger.user(name="alice")
        assert result is logger

    def test_method_chaining(self, logger):
        """Multiple methods can be chained."""
        result = logger.event(action="login").user(name="alice").host(hostname="web01")
        assert result is logger


class TestLoggerOutput:
    """Test log output functionality."""

    def test_out_outputs_json(self, logger):
        """out() outputs valid JSON to stdout."""
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test").out(Severity.INFO)
            output = buffer.getvalue()

            # Should be valid JSON
            data = json.loads(output.strip())
            assert "@timestamp" in data
            assert data["event"]["action"] == "test"
        finally:
            sys.stdout = old_stdout

    def test_out_resets_state(self, logger):
        """out() resets internal Base for next log entry."""
        logger.event(action="first").out(Severity.INFO)

        # Base should be reset
        assert not hasattr(logger._base, 'event')

    def test_out_invalid_severity(self, logger):
        """out() with non-Severity raises InvalidTypeError."""
        with pytest.raises(InvalidTypeError, match="severity must be a Severity"):
            logger.out("INFO")

    def test_out_respects_severity_threshold(self, logger):
        """out() only outputs if severity >= threshold."""
        logger.severity_output_level = Severity.WARNING

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Below threshold - no output
            logger.event(action="info_event").out(Severity.INFO)
            assert buffer.getvalue() == ""

            # At threshold - outputs
            logger.event(action="warning_event").out(Severity.WARNING)
            assert buffer.getvalue() != ""
        finally:
            sys.stdout = old_stdout


class TestLoggerDefaults:
    """Test defaults merging functionality."""

    def test_defaults_merged_into_fields(self, logger):
        """Default values are merged into field objects."""
        logger.defaults = {"event": {"dataset": "myapp"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["event"]["dataset"] == "myapp"
            assert data["event"]["action"] == "test"
        finally:
            sys.stdout = old_stdout

    def test_explicit_values_override_defaults(self, logger):
        """Explicit field values override defaults."""
        logger.defaults = {"event": {"dataset": "default"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.event(action="test", dataset="override").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["event"]["dataset"] == "override"
        finally:
            sys.stdout = old_stdout


class TestLoggerFieldMethods:
    """Test that all field methods work correctly."""

    def test_all_field_methods_exist(self, logger):
        """All 27+ field methods are available."""
        methods = [
            'agent', 'client', 'cloud', 'container', 'destination', 'ecs',
            'error', 'event', 'file', 'geo', 'group', 'host', 'http_request',
            'http_response', 'log', 'network', 'observer', 'organization',
            'os', 'process', 'related', 'server', 'service', 'source',
            'url', 'user', 'user_agent'
        ]

        for method in methods:
            assert hasattr(logger, method)
            assert callable(getattr(logger, method))

    def test_field_method_adds_to_base(self, logger):
        """Field methods add objects to internal Base."""
        logger.user(name="alice")
        assert hasattr(logger._base, 'user')
        assert logger._base.user.name == "alice"

    def test_first_wins_policy(self, logger):
        """Only first field of each type is accepted."""
        logger.event(action="first")
        logger.event(action="second")  # Should be ignored

        assert logger._base.event.action == "first"
