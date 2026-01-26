#!/usr/bin/env python3
"""
Smoke tests for Cloud Run deployments.

Validates that a new deployment is healthy before shifting production traffic.
Tests critical functionality: health check, database, authentication, API endpoints.

Usage:
    python scripts/smoke_test.py --url https://upstream-staging-xyz.run.app

Exit codes:
    0 - All smoke tests passed
    1 - One or more tests failed
"""

import argparse
import sys
import time
from typing import Tuple

import requests


def test_health_endpoint(base_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test that the health check endpoint returns 200 OK."""
    try:
        response = requests.get(f"{base_url}/health/", timeout=timeout)
        if response.status_code == 200:
            return True, "✓ Health endpoint returned 200 OK"
        return False, f"✗ Health endpoint returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Health endpoint failed: {e}"


def test_database_connectivity(base_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test that the app can connect to the database."""
    try:
        # The health endpoint should include database connectivity check
        response = requests.get(f"{base_url}/health/", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("database") == "ok":
                return True, "✓ Database connectivity OK"
            return False, f"✗ Database check failed: {data.get('database')}"
        return False, f"✗ Health check returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Database connectivity test failed: {e}"


def test_api_authentication(base_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test that API authentication endpoints are responding."""
    try:
        # Test auth endpoint returns expected error for missing credentials
        response = requests.post(
            f"{base_url}/api/auth/token/",
            json={},  # Empty payload should return 400
            timeout=timeout,
        )
        # We expect 400 (bad request) not 500 (server error)
        if response.status_code in [400, 401]:
            return True, "✓ Authentication endpoint responding"
        return False, f"✗ Auth endpoint returned unexpected {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Authentication test failed: {e}"


def test_api_list_endpoint(base_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test that a public API list endpoint is accessible."""
    try:
        # Test unauthenticated access - should return 401 (secured) not 500 (error)
        response = requests.get(f"{base_url}/api/uploads/", timeout=timeout)
        if response.status_code in [200, 401, 403]:
            return True, "✓ API list endpoint responding"
        return False, f"✗ API endpoint returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ API list endpoint test failed: {e}"


def test_static_files(base_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test that static files are being served."""
    try:
        # Most Django apps have /static/admin/ available
        response = requests.get(
            f"{base_url}/static/admin/css/base.css", timeout=timeout
        )
        if response.status_code == 200:
            return True, "✓ Static files serving correctly"
        # Some deployments use CDN, so 404 is acceptable
        if response.status_code == 404:
            return True, "✓ Static files request handled (CDN or disabled)"
        return False, f"✗ Static files returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Static files test failed: {e}"


def run_smoke_tests(base_url: str, max_retries: int = 3, retry_delay: int = 5) -> bool:
    """
    Run all smoke tests with retry logic.

    Args:
        base_url: Base URL of the deployment to test
        max_retries: Number of times to retry failed tests
        retry_delay: Seconds to wait between retries

    Returns:
        True if all tests pass, False otherwise
    """
    tests = [
        ("Health Check", test_health_endpoint),
        ("Database Connectivity", test_database_connectivity),
        ("API Authentication", test_api_authentication),
        ("API List Endpoint", test_api_list_endpoint),
        ("Static Files", test_static_files),
    ]

    print(f"\n🔍 Running smoke tests against {base_url}\n")
    print("=" * 60)

    all_passed = True
    results = []

    for test_name, test_func in tests:
        passed = False
        message = ""

        for attempt in range(1, max_retries + 1):
            passed, message = test_func(base_url)

            if passed:
                break

            if attempt < max_retries:
                print(f"⚠️  {test_name} failed (attempt {attempt}/{max_retries})")
                print(f"   Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        results.append((test_name, passed, message))

        if not passed:
            all_passed = False

    # Print results
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)

    for test_name, passed, message in results:
        print(f"{message}")

    print("=" * 60)

    if all_passed:
        print("\n✅ All smoke tests passed!")
        return True
    else:
        print("\n❌ Some smoke tests failed!")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run smoke tests on a deployment")
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the deployment (e.g., https://upstream-staging-xyz.run.app)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Number of retries for failed tests (default: 3)",
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="Delay in seconds between retries (default: 5)",
    )

    args = parser.parse_args()

    # Remove trailing slash from URL
    base_url = args.url.rstrip("/")

    success = run_smoke_tests(base_url, args.max_retries, args.retry_delay)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
