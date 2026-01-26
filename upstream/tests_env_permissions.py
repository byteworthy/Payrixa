"""
Unit tests for .env file permission validation.

Tests the security validation logic in upstream/env_permissions.py to ensure:
1. Secure permissions (600, 400) are accepted
2. Insecure permissions (666, 644) are rejected appropriately
3. Development mode warns but doesn't block
4. Production mode blocks on insecure permissions
5. Missing .env files are handled gracefully
6. CI environments skip validation
"""

import os
import stat
import tempfile
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from upstream.env_permissions import (
    check_env_permissions,
    get_permission_mode,
    is_ci_environment,
)


class EnvPermissionsTestCase(TestCase):
    """Test cases for .env file permission validation."""

    def setUp(self):
        """Create a temporary .env file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = Path(self.temp_dir) / ".env"
        self.env_file.write_text("SECRET_KEY=test\nFIELD_ENCRYPTION_KEY=test123")

    def tearDown(self):
        """Clean up temporary files."""
        if self.env_file.exists():
            self.env_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_secure_permissions_600_pass(self):
        """Test that 600 permissions (owner read/write) are accepted."""
        self.env_file.chmod(0o600)

        # Should not raise in strict mode
        try:
            check_env_permissions(self.env_file, strict=True)
        except ImproperlyConfigured:
            self.fail("600 permissions should be accepted in strict mode")

        # Verify permissions are correct
        mode = get_permission_mode(self.env_file)
        self.assertEqual(oct(stat.S_IMODE(mode))[-3:], "600")

    def test_secure_permissions_400_pass(self):
        """Test that 400 permissions (owner read-only) are accepted."""
        self.env_file.chmod(0o400)

        # Should not raise in strict mode
        try:
            check_env_permissions(self.env_file, strict=True)
        except ImproperlyConfigured:
            self.fail("400 permissions should be accepted in strict mode")

        # Verify permissions are correct
        mode = get_permission_mode(self.env_file)
        self.assertEqual(oct(stat.S_IMODE(mode))[-3:], "400")

    def test_insecure_permissions_666_dev_warns(self):
        """Test that 666 permissions in dev mode logs warning but doesn't block."""
        self.env_file.chmod(0o666)

        # Should not raise in non-strict (dev) mode
        with self.assertLogs("upstream.env_permissions", level="WARNING") as cm:
            check_env_permissions(self.env_file, strict=False)

        # Verify warning was logged
        self.assertTrue(
            any("SECURITY ERROR" in msg for msg in cm.output),
            "Warning should be logged for insecure permissions in dev mode",
        )

    def test_insecure_permissions_666_prod_errors(self):
        """Test that 666 permissions in prod mode raises exception."""
        self.env_file.chmod(0o666)

        # Should raise in strict (production) mode
        with self.assertRaises(ImproperlyConfigured) as cm:
            check_env_permissions(self.env_file, strict=True)

        # Verify error message contains key information
        error_msg = str(cm.exception)
        self.assertIn("SECURITY ERROR", error_msg)
        self.assertIn("666", error_msg)
        self.assertIn("FIELD_ENCRYPTION_KEY", error_msg)
        self.assertIn("chmod 600", error_msg)
        self.assertIn("HIPAA", error_msg)

    def test_insecure_permissions_644_prod_errors(self):
        """Test 644 permissions (group/other read) raises in prod mode."""
        self.env_file.chmod(0o644)

        # Should raise in strict mode
        with self.assertRaises(ImproperlyConfigured) as cm:
            check_env_permissions(self.env_file, strict=True)

        error_msg = str(cm.exception)
        self.assertIn("644", error_msg)

    def test_insecure_permissions_664_prod_errors(self):
        """Test that 664 permissions (group write) in prod mode raises exception."""
        self.env_file.chmod(0o664)

        # Should raise in strict mode
        with self.assertRaises(ImproperlyConfigured):
            check_env_permissions(self.env_file, strict=True)

    def test_env_file_missing_skips(self):
        """Test that missing .env file is handled gracefully."""
        non_existent = Path(self.temp_dir) / "nonexistent.env"

        # Should not raise for missing file
        try:
            check_env_permissions(non_existent, strict=True)
        except Exception as e:
            self.fail(f"Missing .env file should be skipped, but raised: {e}")

    def test_ci_environment_skips_github_actions(self):
        """Test that GitHub Actions CI environment skips validation."""
        self.env_file.chmod(0o666)  # Insecure permissions

        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            # Verify CI is detected
            self.assertTrue(is_ci_environment())

            # Should not raise even with insecure permissions in CI
            try:
                check_env_permissions(self.env_file, strict=True)
            except ImproperlyConfigured:
                self.fail("CI environment should skip permission check")

    def test_ci_environment_skips_gitlab_ci(self):
        """Test that GitLab CI environment skips validation."""
        self.env_file.chmod(0o666)

        with mock.patch.dict(os.environ, {"GITLAB_CI": "true"}):
            self.assertTrue(is_ci_environment())

            try:
                check_env_permissions(self.env_file, strict=True)
            except ImproperlyConfigured:
                self.fail("GitLab CI environment should skip permission check")

    def test_ci_environment_skips_generic_ci(self):
        """Test that generic CI environment variable skips validation."""
        self.env_file.chmod(0o666)

        with mock.patch.dict(os.environ, {"CI": "true"}):
            self.assertTrue(is_ci_environment())

            try:
                check_env_permissions(self.env_file, strict=True)
            except ImproperlyConfigured:
                self.fail("Generic CI environment should skip permission check")

    def test_non_ci_environment_detected(self):
        """Test that non-CI environment is correctly detected."""
        # Clear any CI environment variables
        ci_vars = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "CIRCLECI",
            "TRAVIS",
            "JENKINS_HOME",
            "BUILDKITE",
        ]

        with mock.patch.dict(os.environ, {var: "" for var in ci_vars}, clear=False):
            self.assertFalse(is_ci_environment())

    def test_get_permission_mode(self):
        """Test that get_permission_mode returns correct mode."""
        self.env_file.chmod(0o600)
        mode = get_permission_mode(self.env_file)

        # Verify mode is an integer
        self.assertIsInstance(mode, int)

        # Verify we can extract permissions
        perms = oct(stat.S_IMODE(mode))[-3:]
        self.assertEqual(perms, "600")

    def test_insecure_permissions_with_execute_bit(self):
        """Test that permissions with execute bits are also rejected."""
        self.env_file.chmod(0o755)

        with self.assertRaises(ImproperlyConfigured) as cm:
            check_env_permissions(self.env_file, strict=True)

        error_msg = str(cm.exception)
        self.assertIn("755", error_msg)

    def test_error_message_contains_fix_command(self):
        """Test that error message includes the fix command."""
        self.env_file.chmod(0o666)

        with self.assertRaises(ImproperlyConfigured) as cm:
            check_env_permissions(self.env_file, strict=True)

        error_msg = str(cm.exception)
        self.assertIn(f"chmod 600 {self.env_file}", error_msg)

    def test_error_message_mentions_hipaa(self):
        """Test that error message mentions HIPAA compliance."""
        self.env_file.chmod(0o666)

        with self.assertRaises(ImproperlyConfigured) as cm:
            check_env_permissions(self.env_file, strict=True)

        error_msg = str(cm.exception)
        self.assertIn("HIPAA", error_msg)
        self.assertIn("45 CFR 164.312", error_msg)
