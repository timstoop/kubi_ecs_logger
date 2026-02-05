"""Tests that verify README examples work correctly.

These tests mirror the exact examples from README.md to ensure
they continue to work as documented.
"""

import json
import sys
from io import StringIO
from kubi_ecs_logger import Logger, Severity


class TestReadmeExamples:
    """Test that all README.md examples work correctly."""

    def test_readme_example_1_configuration_loaded(self):
        """Test first README example: configuration loaded."""
        # Reset logger
        logger = Logger()
        logger.dev = False  # Disable dev mode for test
        logger.severity_output_level = Severity.INFO
        logger.defaults = {
            "event": {
                "test": "test value"
            }
        }

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Log loaded configuration (from README)
            Logger().event(
                category="configuration",
                action="configuration loaded",
                dataset="The configuration is loaded from config.yaml"
            ).out(severity=Severity.INFO)

            output = buffer.getvalue()
            data = json.loads(output.strip())

            # Verify output matches README expectations
            assert "@timestamp" in data
            assert data["event"]["action"] == "configuration loaded"
            assert data["event"]["category"] == "configuration"
            assert data["event"]["dataset"] == "The configuration is loaded from config.yaml"
            assert data["event"]["test"] == "test value"  # From defaults
            assert data["logline"]["level"] == "INFO"

        finally:
            sys.stdout = old_stdout
            # Reset defaults for other tests
            logger.defaults = {}

    def test_readme_example_2_request_received(self):
        """Test second README example: request received."""
        logger = Logger()
        logger.dev = False  # Disable dev mode for test
        logger.severity_output_level = Severity.INFO
        logger.defaults = {
            "event": {
                "test": "test value"
            }
        }

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            # Here is a little bit bigger example (from README)
            Logger() \
                .event(category="requests", action="request received") \
                .url(path="/test", domain="test.com") \
                .source(ip="123.251.512.152") \
                .http_response(status_code=200) \
                .out(severity=Severity.INFO)

            output = buffer.getvalue()
            data = json.loads(output.strip())

            # Verify output matches README expectations
            assert "@timestamp" in data
            assert data["event"]["action"] == "request received"
            assert data["event"]["category"] == "requests"
            assert data["event"]["test"] == "test value"  # From defaults
            assert data["httpresponse"]["status_code"] == "200"
            assert data["logline"]["level"] == "INFO"
            assert data["source"]["ip"] == "123.251.512.152"
            assert data["url"]["domain"] == "test.com"
            assert data["url"]["path"] == "/test"

        finally:
            sys.stdout = old_stdout
            # Reset defaults for other tests
            logger.defaults = {}

    def test_readme_configuration_examples(self):
        """Test README configuration examples."""
        logger = Logger()

        # If in development mode the lib will output formatted json.
        logger.dev = True
        assert logger.dev is True

        # The minimum level of severity for outputing
        logger.severity_output_level = Severity.INFO
        assert logger.severity_output_level == Severity.INFO

        # Set default key/value pairs
        logger.defaults = {
            "event": {
                "test": "test value"
            }
        }
        assert logger.defaults == {"event": {"test": "test value"}}

        # Reset for other tests
        logger.dev = False
        logger.defaults = {}
