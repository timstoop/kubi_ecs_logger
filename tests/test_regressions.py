"""Regression tests for bug fixes.

These tests verify that specific bugs have been fixed and prevent them
from being reintroduced.
"""

import json
import sys
from io import StringIO
from kubi_ecs_logger import Logger, Severity


class TestEcsMethodRegression:
    """Regression tests for ecs() method (PR #2 feedback)."""

    def test_ecs_uses_correct_class_for_defaults(self):
        """ecs() should use ECS class for defaults, not Client.

        Regression test for bug where _get_defaults_for(Client) was called
        instead of _get_defaults_for(ECS).
        """
        logger = Logger()
        logger.defaults = {"ecs": {"version": "1.12.0"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.base(message="test").ecs().out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert "ecs" in data
            assert data["ecs"]["version"] == "1.12.0"
        finally:
            sys.stdout = old_stdout

    def test_ecs_explicit_version_overrides_defaults(self):
        """ecs() explicit version parameter should override defaults.

        Regression test for bug where kwargs were merged with defaults
        but then never passed to ECS constructor.
        """
        logger = Logger()
        logger.defaults = {"ecs": {"version": "1.12.0"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.base(message="test").ecs(version="8.0.0").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert data["ecs"]["version"] == "8.0.0"
        finally:
            sys.stdout = old_stdout

    def test_ecs_kwargs_passed_to_constructor(self):
        """ecs() should pass kwargs to ECS constructor.

        Regression test for bug where kwargs were collected but never
        passed to the ECS() constructor.
        """
        logger = Logger()

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.base(message="test").ecs(custom_field="value").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            assert "ecs" in data
            assert data["ecs"]["custom_field"] == "value"
        finally:
            sys.stdout = old_stdout

    def test_ecs_kwargs_override_defaults(self):
        """ecs() kwargs should override defaults correctly.

        Regression test verifying the complete parameter precedence:
        explicit params > kwargs > defaults
        """
        logger = Logger()
        logger.defaults = {"ecs": {"version": "1.0.0", "custom": "default"}}

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            logger.base(message="test").ecs(custom="override").out(Severity.INFO)
            output = buffer.getvalue()
            data = json.loads(output.strip())

            # version should come from defaults
            assert data["ecs"]["version"] == "1.0.0"
            # custom should be overridden by kwargs
            assert data["ecs"]["custom"] == "override"
        finally:
            sys.stdout = old_stdout

    def test_ecs_follows_same_pattern_as_error(self):
        """ecs() should follow the same implementation pattern as error().

        Both methods should handle defaults and kwargs identically.
        """
        logger = Logger()
        logger.defaults = {
            "ecs": {"version": "1.0.0"},
            "error": {"code": "DEFAULT_CODE"}
        }

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Test ecs pattern
            logger.base(message="test1").ecs(version="8.0.0").out(Severity.INFO)
            output1 = buffer.getvalue()
            data1 = json.loads(output1.strip())
            buffer.truncate(0)
            buffer.seek(0)

            # Test error pattern
            logger.base(message="test2").error(code="EXPLICIT_CODE").out(Severity.ERROR)
            output2 = buffer.getvalue()
            data2 = json.loads(output2.strip())

            # Both should have explicit params override defaults
            assert data1["ecs"]["version"] == "8.0.0"
            assert data2["error"]["code"] == "EXPLICIT_CODE"
        finally:
            sys.stdout = old_stdout
