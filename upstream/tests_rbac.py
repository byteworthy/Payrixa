"""
Tests for RBAC (Role-Based Access Control) system.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from upstream.models import Customer, UserProfile
from upstream.permissions import (
    has_permission,
    validate_role_change,
    validate_remove_member,
    is_last_owner,
)


class RBACPermissionTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")

        # Create users with different roles
        self.owner_user = User.objects.create_user(username="owner", password="pass")
        self.owner_profile = UserProfile.objects.create(
            user=self.owner_user, customer=self.customer, role="owner"
        )

        self.admin_user = User.objects.create_user(username="admin", password="pass")
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, customer=self.customer, role="admin"
        )

        self.analyst_user = User.objects.create_user(
            username="analyst", password="pass"
        )
        self.analyst_profile = UserProfile.objects.create(
            user=self.analyst_user, customer=self.customer, role="analyst"
        )

        self.viewer_user = User.objects.create_user(username="viewer", password="pass")
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user, customer=self.customer, role="viewer"
        )

    def test_owner_permissions(self):
        """Test that owners have all permissions."""
        self.assertTrue(has_permission(self.owner_user, "view_reports"))
        self.assertTrue(has_permission(self.owner_user, "upload_claims"))
        self.assertTrue(has_permission(self.owner_user, "manage_mappings"))
        self.assertTrue(has_permission(self.owner_user, "manage_alerts"))
        self.assertTrue(has_permission(self.owner_user, "manage_webhooks"))
        self.assertTrue(has_permission(self.owner_user, "manage_users"))
        self.assertTrue(has_permission(self.owner_user, "manage_configuration"))

    def test_admin_permissions(self):
        """Test that admins have admin-level permissions."""
        self.assertTrue(has_permission(self.admin_user, "view_reports"))
        self.assertTrue(has_permission(self.admin_user, "upload_claims"))
        self.assertTrue(has_permission(self.admin_user, "manage_mappings"))
        self.assertTrue(has_permission(self.admin_user, "manage_alerts"))
        self.assertTrue(has_permission(self.admin_user, "manage_webhooks"))
        self.assertTrue(has_permission(self.admin_user, "manage_users"))
        self.assertTrue(has_permission(self.admin_user, "manage_configuration"))

    def test_analyst_permissions(self):
        """Test that analysts have analyst-level permissions."""
        self.assertTrue(has_permission(self.analyst_user, "view_reports"))
        self.assertTrue(has_permission(self.analyst_user, "upload_claims"))
        self.assertTrue(has_permission(self.analyst_user, "manage_mappings"))
        self.assertFalse(has_permission(self.analyst_user, "manage_alerts"))
        self.assertFalse(has_permission(self.analyst_user, "manage_webhooks"))
        self.assertFalse(has_permission(self.analyst_user, "manage_users"))
        self.assertFalse(has_permission(self.analyst_user, "manage_configuration"))

    def test_viewer_permissions(self):
        """Test that viewers have view-only permissions."""
        self.assertTrue(has_permission(self.viewer_user, "view_reports"))
        self.assertFalse(has_permission(self.viewer_user, "upload_claims"))
        self.assertFalse(has_permission(self.viewer_user, "manage_mappings"))
        self.assertFalse(has_permission(self.viewer_user, "manage_alerts"))
        self.assertFalse(has_permission(self.viewer_user, "manage_webhooks"))
        self.assertFalse(has_permission(self.viewer_user, "manage_users"))
        self.assertFalse(has_permission(self.viewer_user, "manage_configuration"))

    def test_unauthenticated_user_no_permissions(self):
        """Test that unauthenticated users have no permissions."""
        anon_user = User()
        self.assertFalse(has_permission(anon_user, "view_reports"))
        self.assertFalse(has_permission(anon_user, "upload_claims"))
        self.assertFalse(has_permission(anon_user, "manage_configuration"))

    def test_last_owner_protection(self):
        """Test that the last owner cannot be removed/demoted."""
        # Owner is the only owner
        self.assertTrue(is_last_owner(self.owner_profile))

        # Try to remove last owner
        valid, error = validate_remove_member(self.owner_user, self.owner_profile)
        self.assertFalse(valid)
        self.assertIn("last owner", error.lower())

        # Try to demote last owner
        valid, error = validate_role_change(
            self.owner_user, self.owner_profile, "admin"
        )
        self.assertFalse(valid)
        self.assertIn("last owner", error.lower())

    def test_multiple_owners_allows_demotion(self):
        """Test that when there are multiple owners, one can be demoted."""
        # Create second owner
        owner2_user = User.objects.create_user(username="owner2", password="pass")
        owner2_profile = UserProfile.objects.create(
            user=owner2_user, customer=self.customer, role="owner"
        )

        # Now first owner is not the last owner
        self.assertFalse(is_last_owner(self.owner_profile))

        # Should be able to demote first owner
        valid, error = validate_role_change(
            self.owner_user, self.owner_profile, "admin"
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_admin_cannot_promote_to_owner(self):
        """Test that admins cannot promote users to owner."""
        # Admin tries to promote viewer to owner
        valid, error = validate_role_change(
            self.admin_user, self.viewer_profile, "owner"
        )
        self.assertFalse(valid)
        self.assertIn("only owners", error.lower())

    def test_admin_cannot_modify_owner(self):
        """Test that admins cannot modify owner roles."""
        valid, error = validate_role_change(
            self.admin_user, self.owner_profile, "admin"
        )
        self.assertFalse(valid)
        # Error message could be either "cannot modify" or about role restriction
        self.assertTrue("cannot modify" in error.lower() or "owner" in error.lower())

    def test_owner_can_promote_to_admin(self):
        """Test that owners can promote users to admin."""
        valid, error = validate_role_change(
            self.owner_user, self.analyst_profile, "admin"
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_admin_can_promote_analyst_to_analyst(self):
        """Test that admins can change analyst/viewer roles."""
        valid, error = validate_role_change(
            self.admin_user, self.viewer_profile, "analyst"
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_viewer_cannot_manage_users(self):
        """Test that viewers cannot manage users."""
        valid, error = validate_role_change(
            self.viewer_user, self.analyst_profile, "viewer"
        )
        self.assertFalse(valid)
        self.assertIn("do not have permission", error.lower())


class RBACViewPermissionTests(TestCase):
    """Test permission checks for views using the mixin."""

    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")

        self.analyst_user = User.objects.create_user(
            username="analyst", password="pass"
        )
        self.analyst_profile = UserProfile.objects.create(
            user=self.analyst_user, customer=self.customer, role="analyst"
        )

        self.viewer_user = User.objects.create_user(username="viewer", password="pass")
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user, customer=self.customer, role="viewer"
        )

    def test_upload_claims_permission_check(self):
        """Test that upload_claims permission is checked correctly."""
        # Analyst should have permission
        self.assertTrue(has_permission(self.analyst_user, "upload_claims"))
        # Viewer should not
        self.assertFalse(has_permission(self.viewer_user, "upload_claims"))

    def test_manage_mappings_permission_check(self):
        """Test that manage_mappings permission is checked correctly."""
        # Analyst should have permission
        self.assertTrue(has_permission(self.analyst_user, "manage_mappings"))
        # Viewer should not
        self.assertFalse(has_permission(self.viewer_user, "manage_mappings"))


class RBACAPIEndpointTests(TestCase):
    """
    Test RBAC enforcement at API endpoint level.

    Verifies that users cannot access endpoints they don't have permissions for,
    preventing privilege escalation and unauthorized access.
    """

    def setUp(self):
        """Create users with different roles for testing."""
        from rest_framework.test import APIClient

        self.customer = Customer.objects.create(name="RBAC Test Customer")

        # Viewer (read-only)
        self.viewer_user = User.objects.create_user(
            username="rbac_viewer", email="viewer@test.com", password="testpass123"
        )
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user, customer=self.customer, role="viewer"
        )

        # Analyst (can upload/manage data)
        self.analyst_user = User.objects.create_user(
            username="rbac_analyst", email="analyst@test.com", password="testpass123"
        )
        self.analyst_profile = UserProfile.objects.create(
            user=self.analyst_user, customer=self.customer, role="analyst"
        )

        # Admin (can manage alerts/webhooks/users)
        self.admin_user = User.objects.create_user(
            username="rbac_admin", email="admin@test.com", password="testpass123"
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user, customer=self.customer, role="admin"
        )

        self.client = APIClient()

    def test_viewer_cannot_create_upload(self):
        """Test that viewers cannot POST to uploads endpoint."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.post(
            "/api/uploads/",
            {"filename": "test.csv", "file_type": "claims_data"},
            format="json",
        )

        # Viewers are read-only - should get 403 Forbidden
        self.assertEqual(
            response.status_code,
            403,
            f"Viewer should not be able to create uploads. Got {response.status_code}: {response.data}",
        )

    def test_viewer_can_list_uploads(self):
        """Test that viewers CAN GET uploads (read-only access)."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.get("/api/uploads/")

        # Viewers can read data - should succeed
        self.assertEqual(response.status_code, 200)

    def test_analyst_can_create_upload(self):
        """Test that analysts can POST to uploads endpoint."""
        self.client.force_authenticate(user=self.analyst_user)

        response = self.client.post(
            "/api/uploads/",
            {"filename": "analyst_test.csv", "file_type": "claims_data"},
            format="json",
        )

        # Analysts can upload - should succeed or validation error
        self.assertIn(
            response.status_code,
            [200, 201, 400],
            f"Analyst should be able to create uploads. Got {response.status_code}: {response.data}",
        )

    def test_viewer_cannot_create_payer_mapping(self):
        """Test that viewers cannot create payer mappings."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.post(
            "/api/payer-mappings/",
            {"raw_name": "Aetna Corporation", "canonical_name": "Aetna"},
            format="json",
        )

        # Viewers cannot modify mappings
        self.assertEqual(response.status_code, 403)

    def test_analyst_can_create_payer_mapping(self):
        """Test that analysts can create payer mappings."""
        self.client.force_authenticate(user=self.analyst_user)

        response = self.client.post(
            "/api/payer-mappings/",
            {"raw_name": "Aetna Corporation", "canonical_name": "Aetna"},
            format="json",
        )

        # Analysts can manage mappings
        self.assertIn(response.status_code, [200, 201, 400])

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users cannot access API."""
        # Don't authenticate

        response = self.client.get("/api/uploads/")

        # Should be 401 Unauthorized or 403 Forbidden
        self.assertIn(response.status_code, [401, 403])


class RBACCustomerIsolationTests(TestCase):
    """
    Comprehensive tests for customer isolation across all API endpoints.

    Validates that:
    - Superusers can access all customers' data
    - Customer admins can only access their own customer's data
    - Cross-customer access returns 404 (not 403) to avoid leaking existence
    - Viewers have read-only access
    """

    def setUp(self):
        """Set up multi-customer test environment with different user roles."""
        from rest_framework.test import APIClient

        # Create two customers
        self.customer_a = Customer.objects.create(name="Customer A")
        self.customer_b = Customer.objects.create(name="Customer B")

        # Create superuser (no UserProfile needed)
        self.superuser = User.objects.create_superuser(
            username="superuser", email="super@test.com", password="testpass123"
        )

        # Customer A users
        self.customer_a_admin = User.objects.create_user(
            username="admin_a", email="admin_a@test.com", password="testpass123"
        )
        self.profile_a_admin = UserProfile.objects.create(
            user=self.customer_a_admin, customer=self.customer_a, role="admin"
        )

        self.customer_a_viewer = User.objects.create_user(
            username="viewer_a", email="viewer_a@test.com", password="testpass123"
        )
        self.profile_a_viewer = UserProfile.objects.create(
            user=self.customer_a_viewer, customer=self.customer_a, role="viewer"
        )

        # Customer B users
        self.customer_b_admin = User.objects.create_user(
            username="admin_b", email="admin_b@test.com", password="testpass123"
        )
        self.profile_b_admin = UserProfile.objects.create(
            user=self.customer_b_admin, customer=self.customer_b, role="admin"
        )

        # Create test data for both customers using all_objects manager
        from upstream.models import (
            Upload,
            ClaimRecord,
            ReportRun,
            DriftEvent,
            PayerMapping,
        )
        from django.utils import timezone
        from datetime import timedelta

        # Customer A data
        self.upload_a = Upload.all_objects.create(
            customer=self.customer_a,
            filename="upload_a.csv",
            status="success",
            row_count=100,
        )

        self.claim_a1 = ClaimRecord.all_objects.create(
            customer=self.customer_a,
            upload=self.upload_a,
            payer="Payer A1",
            cpt="99213",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="PAID",
        )

        self.claim_a2 = ClaimRecord.all_objects.create(
            customer=self.customer_a,
            upload=self.upload_a,
            payer="Payer A2",
            cpt="99214",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="DENIED",
        )

        self.report_run_a = ReportRun.all_objects.create(
            customer=self.customer_a,
            run_type="weekly",
            status="success",
            summary_json={
                "baseline_start": "2025-10-01",
                "baseline_end": "2025-12-30",
                "current_start": "2025-12-31",
                "current_end": "2026-01-14",
            },
        )

        self.drift_event_a1 = DriftEvent.all_objects.create(
            customer=self.customer_a,
            report_run=self.report_run_a,
            payer="Payer A1",
            cpt_group="EVAL",
            drift_type="DENIAL_RATE",
            baseline_value=0.2,
            current_value=0.6,
            delta_value=0.4,
            severity=0.8,
            confidence=0.9,
            baseline_start=timezone.now().date() - timedelta(days=104),
            baseline_end=timezone.now().date() - timedelta(days=14),
            current_start=timezone.now().date() - timedelta(days=14),
            current_end=timezone.now().date(),
        )

        self.drift_event_a2 = DriftEvent.all_objects.create(
            customer=self.customer_a,
            report_run=self.report_run_a,
            payer="Payer A2",
            cpt_group="OFFICE",
            drift_type="DENIAL_RATE",
            baseline_value=0.3,
            current_value=0.7,
            delta_value=0.4,
            severity=0.75,
            confidence=0.85,
            baseline_start=timezone.now().date() - timedelta(days=104),
            baseline_end=timezone.now().date() - timedelta(days=14),
            current_start=timezone.now().date() - timedelta(days=14),
            current_end=timezone.now().date(),
        )

        self.payer_mapping_a = PayerMapping.all_objects.create(
            customer=self.customer_a, raw_name="Payer A Raw", normalized_name="Payer A"
        )

        # Customer B data
        self.upload_b = Upload.all_objects.create(
            customer=self.customer_b,
            filename="upload_b.csv",
            status="success",
            row_count=200,
        )

        self.claim_b1 = ClaimRecord.all_objects.create(
            customer=self.customer_b,
            upload=self.upload_b,
            payer="Payer B1",
            cpt="99215",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="PAID",
        )

        self.claim_b2 = ClaimRecord.all_objects.create(
            customer=self.customer_b,
            upload=self.upload_b,
            payer="Payer B2",
            cpt="99203",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="OTHER",
        )

        self.report_run_b = ReportRun.all_objects.create(
            customer=self.customer_b,
            run_type="weekly",
            status="success",
            summary_json={
                "baseline_start": "2025-10-01",
                "baseline_end": "2025-12-30",
                "current_start": "2025-12-31",
                "current_end": "2026-01-14",
            },
        )

        self.drift_event_b1 = DriftEvent.all_objects.create(
            customer=self.customer_b,
            report_run=self.report_run_b,
            payer="Payer B1",
            cpt_group="SURGERY",
            drift_type="DENIAL_RATE",
            baseline_value=0.15,
            current_value=0.55,
            delta_value=0.4,
            severity=0.85,
            confidence=0.9,
            baseline_start=timezone.now().date() - timedelta(days=104),
            baseline_end=timezone.now().date() - timedelta(days=14),
            current_start=timezone.now().date() - timedelta(days=14),
            current_end=timezone.now().date(),
        )

        self.drift_event_b2 = DriftEvent.all_objects.create(
            customer=self.customer_b,
            report_run=self.report_run_b,
            payer="Payer B2",
            cpt_group="LAB",
            drift_type="DENIAL_RATE",
            baseline_value=0.25,
            current_value=0.65,
            delta_value=0.4,
            severity=0.8,
            confidence=0.88,
            baseline_start=timezone.now().date() - timedelta(days=104),
            baseline_end=timezone.now().date() - timedelta(days=14),
            current_start=timezone.now().date() - timedelta(days=14),
            current_end=timezone.now().date(),
        )

        self.payer_mapping_b = PayerMapping.all_objects.create(
            customer=self.customer_b, raw_name="Payer B Raw", normalized_name="Payer B"
        )

        self.client = APIClient()

    def authenticate_as_superuser(self):
        """Authenticate client as superuser."""
        self.client.force_authenticate(user=self.superuser)

    def authenticate_as_customer_a_admin(self):
        """Authenticate client as Customer A admin."""
        self.client.force_authenticate(user=self.customer_a_admin)

    def authenticate_as_customer_a_viewer(self):
        """Authenticate client as Customer A viewer."""
        self.client.force_authenticate(user=self.customer_a_viewer)

    def authenticate_as_customer_b_admin(self):
        """Authenticate client as Customer B admin."""
        self.client.force_authenticate(user=self.customer_b_admin)

    # Superuser Access Tests

    def test_superuser_can_list_all_uploads(self):
        """Test that superuser can see uploads from all customers."""
        self.authenticate_as_superuser()

        response = self.client.get("/api/v1/uploads/")

        self.assertEqual(response.status_code, 200)
        # Should see both uploads (Customer A and B)
        self.assertEqual(len(response.data["results"]), 2)

    def test_superuser_can_retrieve_any_customer_upload(self):
        """Test that superuser can retrieve Customer B's upload."""
        self.authenticate_as_superuser()

        response = self.client.get(f"/api/v1/uploads/{self.upload_b.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.upload_b.id)

    # Customer Isolation Tests

    def test_customer_a_admin_list_only_sees_own_uploads(self):
        """Test that Customer A admin only sees Customer A's uploads."""
        self.authenticate_as_customer_a_admin()

        response = self.client.get("/api/v1/uploads/")

        self.assertEqual(response.status_code, 200)
        # Should only see 1 upload (Customer A)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.upload_a.id)

    def test_customer_a_admin_cannot_retrieve_customer_b_upload(self):
        """Test that Customer A admin gets 404 when accessing Customer B's upload."""
        self.authenticate_as_customer_a_admin()

        response = self.client.get(f"/api/v1/uploads/{self.upload_b.id}/")

        # Should return 404 (not 403) to avoid leaking existence
        self.assertEqual(response.status_code, 404)

    def test_customer_a_admin_list_only_sees_own_drift_events(self):
        """Test that Customer A admin only sees Customer A's drift events."""
        self.authenticate_as_customer_a_admin()

        response = self.client.get("/api/v1/drift-events/")

        self.assertEqual(response.status_code, 200)
        # Should only see 2 drift events (Customer A)
        self.assertEqual(len(response.data["results"]), 2)
        drift_ids = [d["id"] for d in response.data["results"]]
        self.assertIn(self.drift_event_a1.id, drift_ids)
        self.assertIn(self.drift_event_a2.id, drift_ids)

    def test_customer_a_admin_cannot_retrieve_customer_b_drift_event(self):
        """Test that Customer A admin gets 404 when accessing Customer B's drift event."""
        self.authenticate_as_customer_a_admin()

        response = self.client.get(f"/api/v1/drift-events/{self.drift_event_b1.id}/")

        # Should return 404 (not 403)
        self.assertEqual(response.status_code, 404)

    def test_customer_a_admin_list_only_sees_own_claim_records(self):
        """Test that Customer A admin only sees Customer A's claim records."""
        self.authenticate_as_customer_a_admin()

        response = self.client.get("/api/v1/claims/")

        self.assertEqual(response.status_code, 200)
        # Should only see 2 claims (Customer A)
        self.assertEqual(len(response.data["results"]), 2)
        claim_ids = [c["id"] for c in response.data["results"]]
        self.assertIn(self.claim_a1.id, claim_ids)
        self.assertIn(self.claim_a2.id, claim_ids)

    def test_customer_b_admin_cannot_see_customer_a_data(self):
        """Test that Customer B admin cannot access Customer A's data."""
        self.authenticate_as_customer_b_admin()

        # Try to access Customer A's upload
        response = self.client.get(f"/api/v1/uploads/{self.upload_a.id}/")
        self.assertEqual(response.status_code, 404)

        # Try to access Customer A's drift event
        response = self.client.get(f"/api/v1/drift-events/{self.drift_event_a1.id}/")
        self.assertEqual(response.status_code, 404)

    # Viewer Read-Only Tests

    def test_viewer_can_list_own_customer_uploads(self):
        """Test that viewer can list their own customer's uploads."""
        self.authenticate_as_customer_a_viewer()

        response = self.client.get("/api/v1/uploads/")

        self.assertEqual(response.status_code, 200)
        # Should see Customer A's upload
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.upload_a.id)

    # Note: Viewer write restrictions are tested in RBACAPIEndpointTests
    # These customer isolation tests focus on cross-customer access, not role permissions

    # Admin Write Tests

    def test_admin_can_create_payer_mapping(self):
        """Test that admin can POST to create payer mapping."""
        self.authenticate_as_customer_a_admin()

        response = self.client.post(
            "/api/v1/payer-mappings/",
            {
                "raw_name": "Admin Test Payer",
                "normalized_name": "Admin Test Payer Normalized",
            },
            format="json",
        )

        # Admins can create - should succeed or validation error
        self.assertIn(response.status_code, [200, 201, 400])

    def test_admin_can_update_own_payer_mapping(self):
        """Test that admin can PUT to update their own payer mapping."""
        self.authenticate_as_customer_a_admin()

        response = self.client.put(
            f"/api/v1/payer-mappings/{self.payer_mapping_a.id}/",
            {"raw_name": "Updated Payer A Raw", "normalized_name": "Updated Payer A"},
            format="json",
        )

        # Admins can update own customer's data - should succeed or validation error
        self.assertIn(response.status_code, [200, 400])

    # Cross-Customer Write Protection

    def test_admin_cannot_update_other_customer_payer_mapping(self):
        """Test that admin cannot PUT to update another customer's payer mapping."""
        self.authenticate_as_customer_a_admin()

        response = self.client.put(
            f"/api/v1/payer-mappings/{self.payer_mapping_b.id}/",
            {"raw_name": "Hacked Payer B", "normalized_name": "Hacked"},
            format="json",
        )

        # Should return 404 (object not found in customer scope)
        self.assertEqual(response.status_code, 404)

    # Unauthenticated Access Tests

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users cannot access API."""
        # Don't authenticate

        response = self.client.get("/api/v1/uploads/")

        # Should be 401 Unauthorized
        self.assertIn(response.status_code, [401, 403])
