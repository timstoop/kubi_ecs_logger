"""Tests for custom exceptions."""

import pytest
from kubi_ecs_logger.exceptions import LoggerError, InvalidTypeError, InvalidSeverityError


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_logger_error_inherits_from_exception(self):
        """LoggerError inherits from Exception."""
        assert issubclass(LoggerError, Exception)

    def test_invalid_type_error_inherits_from_logger_error(self):
        """InvalidTypeError inherits from LoggerError."""
        assert issubclass(InvalidTypeError, LoggerError)

    def test_invalid_type_error_inherits_from_type_error(self):
        """InvalidTypeError inherits from TypeError."""
        assert issubclass(InvalidTypeError, TypeError)

    def test_invalid_severity_error_inherits_from_logger_error(self):
        """InvalidSeverityError inherits from LoggerError."""
        assert issubclass(InvalidSeverityError, LoggerError)

    def test_invalid_severity_error_inherits_from_value_error(self):
        """InvalidSeverityError inherits from ValueError."""
        assert issubclass(InvalidSeverityError, ValueError)


class TestExceptionCatching:
    """Test exception catching patterns."""

    def test_can_catch_specific_exception(self):
        """Specific exceptions can be caught."""
        try:
            raise InvalidTypeError("test error")
        except InvalidTypeError as e:
            assert str(e) == "test error"

    def test_can_catch_by_base_class(self):
        """Library exceptions can be caught by LoggerError."""
        try:
            raise InvalidTypeError("test error")
        except LoggerError:
            pass  # Should catch it

    def test_can_catch_by_builtin_type(self):
        """InvalidTypeError can be caught as TypeError."""
        try:
            raise InvalidTypeError("test error")
        except TypeError:
            pass  # Should catch it

    def test_invalid_severity_error_caught_as_value_error(self):
        """InvalidSeverityError can be caught as ValueError."""
        try:
            raise InvalidSeverityError("test error")
        except ValueError:
            pass  # Should catch it


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_logger_error_with_message(self):
        """LoggerError accepts and stores message."""
        error = LoggerError("custom message")
        assert str(error) == "custom message"

    def test_invalid_type_error_with_message(self):
        """InvalidTypeError accepts and stores message."""
        error = InvalidTypeError("expected str, got int")
        assert str(error) == "expected str, got int"

    def test_invalid_severity_error_with_message(self):
        """InvalidSeverityError accepts and stores message."""
        error = InvalidSeverityError("Invalid severity: foo")
        assert str(error) == "Invalid severity: foo"
