"""Severity levels for log entries.

This module defines the Severity enum used to classify log messages
by importance and filter output based on configured thresholds.
"""

from enum import Enum
from ..exceptions import InvalidSeverityError


class OrderedEnum(Enum):
    """Base class for enums that support comparison operators.

    This class enables comparison operations (<, <=, >, >=) between
    enum members based on their numeric values.
    """
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Severity(OrderedEnum):
    """Ordered severity levels for log messages.

    Severity levels are ordered from DEBUG (least severe) to CRITICAL
    (most severe). This ordering enables filtering log output based on
    minimum severity thresholds.

    Attributes:
        DEBUG: Detailed diagnostic information (value=1)
        INFO: General informational messages (value=2)
        WARNING: Warning messages for potentially harmful situations (value=3)
        ERROR: Error messages for failures (value=4)
        CRITICAL: Critical errors that may cause application failure (value=5)

    Example:
        >>> Severity.INFO < Severity.ERROR
        True
        >>> Severity.from_str("warning")
        <Severity.WARNING: 3>
    """
    CRITICAL = 5
    ERROR = 4
    WARNING = 3
    INFO = 2
    DEBUG = 1

    @staticmethod
    def from_str(severity_str: str) -> 'Severity':
        """Convert a string to a Severity enum member.

        Args:
            severity_str: Case-insensitive severity name
                ("debug", "info", "warning", "error", "critical")

        Returns:
            The corresponding Severity enum member.

        Raises:
            InvalidSeverityError: If severity_str is not a valid severity name.

        Example:
            >>> Severity.from_str("INFO")
            <Severity.INFO: 2>
        """
        severity_str = severity_str.lower()
        if severity_str == "debug":
            return Severity.DEBUG
        elif severity_str == "info":
            return Severity.INFO
        elif severity_str == "warning":
            return Severity.WARNING
        elif severity_str == "error":
            return Severity.ERROR
        elif severity_str == "critical":
            return Severity.CRITICAL
        else:
            raise InvalidSeverityError(f"Invalid severity level: '{severity_str}'")
