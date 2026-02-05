"""Base class for ECS field sets.

This module provides the FieldSet base class that all ECS field groups inherit from.
"""

from marshmallow import post_load
from kubi_ecs_logger.models import RootSchema


class FieldSet:
    """Base class for all ECS field set objects.

    This class provides the foundation for all ECS field groups (Event, User,
    Host, etc.). It accepts arbitrary keyword arguments that become attributes,
    allowing for both defined ECS fields and custom extensions.

    All field set subclasses should inherit from this class and define their
    specific ECS fields as __init__ parameters.

    Example:
        >>> class Custom Field(FieldSet):
        ...     def __init__(self, my_field=None, **kwargs):
        ...         self.my_field = my_field
        ...         super().__init__(**kwargs)
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a FieldSet with arbitrary attributes.

        Args:
            **kwargs: Field names and values to set as attributes.
                Any kwargs not defined by subclasses become custom fields.
        """
        for k, v in kwargs.items():
            if not hasattr(self, k):
                setattr(self, k, v)


class FieldSetSchema(RootSchema):
    class Meta:
        model = FieldSet

    @post_load
    def load_data(self, data):
        return FieldSet(**data)


