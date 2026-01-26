"""
Rollback Test Suite

Tests the deployment rollback validation script works correctly.
These tests run locally against the Django test server.

The rollback script is designed to validate that deployments can
recover from failures. This test suite ensures the script itself
works correctly in different scenarios.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from django.test import LiveServerTestCase


class RollbackScriptTests(LiveServerTestCase):
    """Tests for the rollback validation script."""

    def test_rollback_script_syntax(self):
        """Test that rollback script has valid Python syntax."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "scripts/test_rollback.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"Syntax error: {result.stderr}")

    def test_rollback_script_help(self):
        """Test that rollback script shows help."""
        result = subprocess.run(
            [sys.executable, "scripts/test_rollback.py", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--url", result.stdout)
        self.assertIn("--local", result.stdout)
        self.assertIn("--timeout", result.stdout)
        self.assertIn("--retries", result.stdout)

    def test_rollback_local_mode_healthy(self):
        """Test rollback script passes with healthy server."""
        # LiveServerTestCase provides self.live_server_url
        result = subprocess.run(
            [
                sys.executable,
                "scripts/test_rollback.py",
                "--url",
                self.live_server_url,
                "--local",
                "--timeout",
                "10",
                "--retries",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        # Should pass since health endpoint is available
        self.assertEqual(
            result.returncode,
            0,
            f"Rollback test failed: stdout={result.stdout}, stderr={result.stderr}",
        )
        self.assertIn("PASSED", result.stdout)

    def test_rollback_invalid_url_fails(self):
        """Test rollback script fails with invalid URL."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/test_rollback.py",
                "--url",
                "http://localhost:99999",
                "--local",
                "--timeout",
                "2",
                "--retries",
                "1",
                "--retry-delay",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        # Should fail since nothing is running on port 99999
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAILED", result.stdout)

    def test_rollback_script_invalid_url_format(self):
        """Test rollback script rejects invalid URL format."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/test_rollback.py",
                "--url",
                "invalid-url",
                "--local",
            ],
            capture_output=True,
            text=True,
        )
        # Should fail with exit code 2 (configuration error)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Invalid URL format", result.stdout)

    def test_rollback_script_with_retries(self):
        """Test rollback script retry logic."""
        # Test with very short timeout to trigger retries
        result = subprocess.run(
            [
                sys.executable,
                "scripts/test_rollback.py",
                "--url",
                self.live_server_url,
                "--local",
                "--timeout",
                "10",
                "--retries",
                "2",
                "--retry-delay",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        # Should pass and show retry configuration
        self.assertEqual(result.returncode, 0)
        self.assertIn("Retries: 2", result.stdout)
