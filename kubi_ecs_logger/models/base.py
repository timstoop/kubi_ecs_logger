"""Base model for log entries.

This module defines the root container for all log data, including
common fields and support for ECS field sets.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from marshmallow import fields

from kubi_ecs_logger.models import RootSchema
from kubi_ecs_logger.models.fields import FieldSet
from kubi_ecs_logger.exceptions import InvalidTypeError


class Base:
    """Root container for a log entry.

    This class holds the common log fields (@timestamp, message, tags, labels)
    and dynamically accepts ECS field set objects. Only one instance of each
    field type is allowed per log entry (first wins policy).

    Attributes:
        timestamp: The timestamp for the log entry
        labels: Key-value pairs for custom metadata
        message: The log message text
        tags: List of tags for categorization
        **kwargs: Additional custom fields not defined in ECS

    Example:
        >>> from datetime import datetime
        >>> from kubi_ecs_logger.models.fields import Event
        >>> base = Base(message="User login", tags=["auth"])
        >>> base.add_object(Event(action="login"))
        True
    """

    def __init__(self,
                 date: Optional[datetime] = None,
                 labels: Optional[Dict[str, Any]] = None,
                 message: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 objects: Optional[List[FieldSet]] = None,
                 **kwargs) -> None:
        """Initialize a new Base log entry.

        Args:
            date: Timestamp for the log entry (defaults to now)
            labels: Dictionary of custom key-value metadata
            message: The log message text
            tags: List of string tags for categorization
            objects: List of FieldSet objects to include
            **kwargs: Additional custom fields
        """
        self.timestamp = date or datetime.now()
        self.labels = labels
        self.message = message
        self.tags = tags

        # Add custom fields from **kwargs
        for k, v in kwargs.items():
            if not hasattr(self, k):
                setattr(self, k, v)

        # Add the field objects that are passed
        if objects is not None:
            for obj in objects:
                if not self.add_object(obj):
                    raise ValueError(f"You can have only one of: {type(obj).__name__}")

    def add_object(self, obj: FieldSet) -> bool:
        """Add an ECS field set object to this log entry.

        Only one instance of each field type is allowed. If a field of the
        same type already exists, this method returns False and the new
        object is ignored (first wins policy).

        Args:
            obj: A FieldSet instance to add to the log entry

        Returns:
            True if the object was added, False if an object of the same type
            already exists.

        Raises:
            InvalidTypeError: If obj is not a FieldSet instance.

        Example:
            >>> from kubi_ecs_logger.models.fields import Event, User
            >>> base = Base()
            >>> base.add_object(Event(action="login"))
            True
            >>> base.add_object(Event(action="logout"))  # Second event ignored
            False
        """
        if not isinstance(obj, FieldSet):
            raise InvalidTypeError(
                f"Expected FieldSet instance, got {type(obj).__name__}"
            )
        name = obj.__class__.__name__.lower()
        if not hasattr(self, name):
            setattr(self, name, obj)
            return True
        return False


class BaseSchema(RootSchema):
    class Meta:
        include = {
            "@timestamp": fields.DateTime(format="iso", attribute="timestamp", allow_none=False)
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from .include import INCLUDE_FIELDS
        self.declared_fields.update(INCLUDE_FIELDS)

    labels = fields.Dict(allow_none=False, metadata={'skip_if': None})
    message = fields.String(allow_none=True)
    tags = fields.List(fields.String(), allow_none=True)
