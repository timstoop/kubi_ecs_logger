"""Base marshmallow schema for ECS models.

This module provides the RootSchema base class that handles serialization
of Base and FieldSet objects to JSON, including filtering None values and
adding custom fields.
"""
from marshmallow import Schema, post_dump


class RootSchema(Schema):
    """Base schema for serializing ECS log entries.

    This schema provides common post-dump processing for all ECS models:
    - Removes fields with None values to keep JSON compact
    - Automatically serializes FieldSet objects using their schemas
    - Includes custom fields (attributes not defined in the schema)

    Attributes:
        SKIP_VALUES: List of values to exclude from serialized output
    """
    SKIP_VALUES = [None]

    @post_dump
    def remove_skip_values(self, data, many, **kwargs):
        """Remove fields with skip values from serialized data.

        This removes any fields whose values are in SKIP_VALUES (e.g., None),
        keeping the JSON output compact.

        Args:
            data: The serialized data dictionary
            many: Whether serializing multiple objects
            **kwargs: Additional marshmallow arguments

        Returns:
            Filtered dictionary with skip values removed.
        """
        return {
            key: value for key, value in data.items()
            if value not in self.SKIP_VALUES
        }

    @post_dump(pass_original=True)
    def add_extra(self, serialized, original, many, **kwargs):
        """Add field objects and custom attributes to serialized data.

        This method handles:
        1. Serializing FieldSet objects using their registered schemas
        2. Including custom fields (int, float, str, bool, dict attributes)

        Args:
            serialized: The already-serialized data
            original: The original Python object being serialized
            many: Whether serializing multiple objects
            **kwargs: Additional marshmallow arguments

        Returns:
            Enhanced dictionary with FieldSet objects and custom fields added.
        """
        from kubi_ecs_logger.models.include import INCLUDE_FIELDS

        for k, v in original.__dict__.items():
            if k not in serialized and v is not None:
                type_name = v.__class__.__name__.lower()
                if type_name in INCLUDE_FIELDS:
                    schema = INCLUDE_FIELDS[type_name].schema
                    data = schema.dump(v)
                    if "kind" not in data:
                        data["kind"] = type_name
                    serialized[k] = data
                elif isinstance(v, (int, float, str, bool, dict)):
                    if not str(k).startswith('_'):
                        serialized[k] = v

        return serialized
