"""Tests for Base model."""

import pytest
from datetime import datetime
from kubi_ecs_logger.models import Base, BaseSchema
from kubi_ecs_logger.models.fields import Event, User, FieldSet
from kubi_ecs_logger.exceptions import InvalidTypeError


class TestBaseInitialization:
    """Test Base initialization."""

    def test_base_with_no_args(self):
        """Base can be initialized with no arguments."""
        base = Base()
        assert base.timestamp is not None
        assert base.labels is None
        assert base.message is None
        assert base.tags is None

    def test_base_with_message(self):
        """Base accepts message parameter."""
        base = Base(message="test message")
        assert base.message == "test message"

    def test_base_with_labels(self):
        """Base accepts labels parameter."""
        labels = {"env": "prod", "team": "backend"}
        base = Base(labels=labels)
        assert base.labels == labels

    def test_base_with_tags(self):
        """Base accepts tags parameter."""
        tags = ["auth", "security"]
        base = Base(tags=tags)
        assert base.tags == tags

    def test_base_with_custom_date(self):
        """Base accepts custom timestamp."""
        custom_date = datetime(2024, 1, 1, 12, 0, 0)
        base = Base(date=custom_date)
        assert base.timestamp == custom_date

    def test_base_with_kwargs(self):
        """Base accepts custom fields via kwargs."""
        base = Base(custom_field="value")
        assert base.custom_field == "value"

    def test_base_with_field_objects(self):
        """Base accepts field objects during initialization."""
        event = Event(action="test")
        base = Base(objects=[event])
        assert hasattr(base, 'event')
        assert base.event.action == "test"


class TestBaseAddObject:
    """Test Base.add_object() method."""

    def test_add_object_with_field_set(self):
        """add_object accepts FieldSet instances."""
        base = Base()
        event = Event(action="test")
        result = base.add_object(event)
        assert result is True
        assert hasattr(base, 'event')

    def test_add_object_returns_true_on_success(self):
        """add_object returns True when object is added."""
        base = Base()
        event = Event(action="test")
        assert base.add_object(event) is True

    def test_add_object_returns_false_on_duplicate(self):
        """add_object returns False for duplicate field types."""
        base = Base()
        event1 = Event(action="first")
        event2 = Event(action="second")

        base.add_object(event1)
        result = base.add_object(event2)

        assert result is False
        assert base.event.action == "first"  # First wins

    def test_add_object_rejects_non_field_set(self):
        """add_object raises InvalidTypeError for non-FieldSet."""
        base = Base()
        with pytest.raises(InvalidTypeError, match="Expected FieldSet instance"):
            base.add_object("not a field set")

    def test_add_object_with_multiple_types(self):
        """add_object accepts different field types."""
        base = Base()
        event = Event(action="test")
        user = User(name="alice")

        base.add_object(event)
        base.add_object(user)

        assert hasattr(base, 'event')
        assert hasattr(base, 'user')


class TestBaseSerialization:
    """Test Base serialization via BaseSchema."""

    def test_serialize_empty_base(self):
        """Empty Base serializes to JSON with timestamp."""
        base = Base()
        schema = BaseSchema()
        data = schema.dump(base)

        assert "@timestamp" in data
        assert isinstance(data["@timestamp"], str)

    def test_serialize_base_with_message(self):
        """Base with message serializes correctly."""
        base = Base(message="test message")
        schema = BaseSchema()
        data = schema.dump(base)

        assert data["message"] == "test message"

    def test_serialize_base_with_fields(self):
        """Base with field objects serializes correctly."""
        base = Base()
        base.add_object(Event(action="test", outcome="success"))
        base.add_object(User(name="alice", id="123"))

        schema = BaseSchema()
        data = schema.dump(base)

        assert data["event"]["action"] == "test"
        assert data["event"]["outcome"] == "success"
        assert data["user"]["name"] == "alice"
        assert data["user"]["id"] == "123"

    def test_serialize_excludes_none_values(self):
        """Serialization excludes None values."""
        base = Base(message=None, tags=None)
        schema = BaseSchema()
        data = schema.dump(base)

        assert "message" not in data
        assert "tags" not in data

    def test_serialize_includes_custom_fields(self):
        """Serialization includes custom kwargs fields."""
        base = Base(custom_field="value", another=42)
        schema = BaseSchema()
        data = schema.dump(base)

        assert data["custom_field"] == "value"
        assert data["another"] == 42
