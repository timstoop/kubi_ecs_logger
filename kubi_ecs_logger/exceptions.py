"""Custom exceptions for kubi_ecs_logger.

This module defines exception classes used throughout the library for
proper error handling and validation.
"""


class LoggerError(Exception):
    """Base exception for all kubi_ecs_logger errors.

    All custom exceptions in this library inherit from this class,
    making it easy to catch any library-specific error.
    """
    pass


class InvalidTypeError(LoggerError, TypeError):
    """Raised when a value has an incorrect type.

    This exception is raised when type validation fails, for example
    when setting a boolean property with a non-boolean value.

    Example:
        >>> Logger().dev = "true"  # Should be bool, not str
        Traceback (most recent call last):
        InvalidTypeError: dev must be a bool, got str
    """
    pass


class InvalidSeverityError(LoggerError, ValueError):
    """Raised when an invalid severity level is provided.

    This exception is raised when a severity string cannot be converted
    to a valid Severity enum member.

    Example:
        >>> Severity.from_str("invalid")
        Traceback (most recent call last):
        InvalidSeverityError: Invalid severity level: 'invalid'
    """
    pass
