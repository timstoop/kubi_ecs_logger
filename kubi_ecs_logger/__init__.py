"""kubi_ecs_logger - JSON logging following Elasticsearch Common Schema.

This library provides a fluent API for creating JSON-formatted log entries
that conform to the Elasticsearch Common Schema (ECS) specification. It enables
structured logging with strongly-typed field sets for consistent log formatting.

Key Features:
    - Fluent interface for building log entries
    - ECS-compliant JSON output
    - Support for 27+ ECS field sets
    - Configurable severity filtering
    - Development mode with pretty-printed output
    - Default values for repeated fields

Example:
    >>> from kubi_ecs_logger import Logger, Severity
    >>> logger = Logger()
    >>> logger.event(action="login", outcome="success").user(name="alice").out(Severity.INFO)
    {"@timestamp": "2026-02-05T...", "event": {"action": "login", ...}, ...}

For more information on ECS fields:
    https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html
"""

from .wrapper import Logger
from .models import Severity
from .exceptions import LoggerError, InvalidTypeError, InvalidSeverityError

__all__ = ['Logger', 'Severity', 'LoggerError', 'InvalidTypeError', 'InvalidSeverityError']
