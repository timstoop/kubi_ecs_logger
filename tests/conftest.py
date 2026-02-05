"""Pytest configuration and fixtures for kubi_ecs_logger tests."""

import sys
from io import StringIO
import pytest
from kubi_ecs_logger import Logger, Severity


@pytest.fixture(autouse=True)
def reset_logger():
    """Automatically reset Logger singleton state before each test.

    This ensures tests don't interfere with each other via singleton state.
    """
    logger = Logger()
    logger.dev = False
    logger.severity_output_level = Severity.DEBUG
    logger.defaults = {}
    yield


@pytest.fixture
def logger():
    """Provide a fresh Logger instance for each test.

    Note: Logger is a singleton, so this resets it between tests.
    """
    logger = Logger()
    # Reset to defaults
    logger.dev = False
    logger.severity_output_level = Severity.DEBUG
    logger.defaults = {}
    return logger


@pytest.fixture
def capture_output():
    """Capture stdout for output validation."""
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    yield buffer
    sys.stdout = old_stdout


@pytest.fixture
def mock_event():
    """Sample Event field object."""
    from kubi_ecs_logger.models.fields import Event
    return Event(action="test_action", outcome="success")


@pytest.fixture
def mock_user():
    """Sample User field object."""
    from kubi_ecs_logger.models.fields import User
    return User(name="testuser", id="123")
