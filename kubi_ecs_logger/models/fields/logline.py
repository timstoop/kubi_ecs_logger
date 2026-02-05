"""ECS log fields.

This module defines the LogLine field set for log-specific metadata.
"""

from typing import Union, Optional
from marshmallow import fields

from .field_set import FieldSet, FieldSetSchema
from ..severity import Severity
from ...exceptions import InvalidTypeError


class LogLine(FieldSet):
    """ECS log field set.

    Represents metadata about the log entry itself, such as the log level
    and the original log message before parsing.

    Attributes:
        level: Log level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        original: The original log message before any parsing
    """

    def __init__(self,
                 level: Optional[Union[str, Severity]] = None,
                 original: Optional[str] = None,
                 *args, **kwargs) -> None:
        """Initialize log fields.

        Args:
            level: The log level (Severity enum or string)
            original: The original log message text
            **kwargs: Additional custom fields
        """
        super().__init__(*args, **kwargs)

        if isinstance(level, Severity):
            level = level.name

        self._level = level
        self.original = original

    @property
    def level(self) -> Optional[str]:
        """Get the log level.

        Returns:
            The log level as a string, or None if not set.
        """
        return self._level

    @level.setter
    def level(self, value: Severity) -> None:
        """Set the log level from a Severity enum.

        Args:
            value: The severity level to set.

        Raises:
            InvalidTypeError: If value is not a Severity enum member.
        """
        if not isinstance(value, Severity):
            raise InvalidTypeError(f"level must be a Severity, got {type(value).__name__}")
        self._level = value.name


class LogLineSchema(FieldSetSchema):
    level = fields.String()
    original = fields.String()
