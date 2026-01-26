"""
Django Query Count Tests for N+1 Optimization (Phase 07).

Tests verify that select_related/prefetch_related optimizations reduce query counts:
- Story #3: Upload list view optimization
- Story #4: ClaimRecord list view optimization
- Story #5: Query count regression tests
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from upstream.models import ClaimRecord, Upload
from upstream.test_fixtures import TenantTestMixin


class QueryOptimizationTests(TenantTestMixin, TestCase):
    """
    Test suite verifying N+1 query optimizations (Story #5 - Phase 07).

    Performance thresholds:
    - Upload list: 3-4 queries (main + count + JOINs for customer/uploaded_by)
    - ClaimRecord list: <10 queries for 50 claims
    - Drift computation: <15 queries for 100 claims
    """

    def setUp(self):
        """Create test customer and user."""
        super().setUp()
        self.customer = self.create_customer("Test Hospital")
        self.user = self.create_user(self.customer, username="testuser")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_upload_list_query_optimization(self):
        """
        Story #3: Verify Upload list view uses select_related for customer/uploaded_by.

        Expected: ~3-4 queries
        - Main query with JOINs
        - Count query for pagination
        """
        # Create 25 uploads with uploaded_by
        for i in range(25):
            Upload.objects.create(
                customer=self.customer,
                filename=f"upload_{i}.csv",
                status="success",
                row_count=100,
                uploaded_by=self.user,
            )

        # Query uploads through API
        with override_settings(DEBUG=True):
            from django.db import reset_queries

            reset_queries()

            response = self.client.get("/api/v1/uploads/")
            self.assertEqual(response.status_code, 200)

            query_count = len(connection.queries)

            # Should be ~3-6 queries total (main + count + maybe permissions check)
            self.assertLessEqual(
                query_count,
                6,
                f"Upload list used {query_count} queries, expected <=6. "
                f"Queries: {[q['sql'][:100] for q in connection.queries]}",
            )

    def test_claimrecord_list_query_optimization(self):
        """
        Story #4: Verify ClaimRecord list view prefetches drift_events.

        Expected: <10 queries for 50 claims
        """
        upload = self.create_upload(self.customer, uploaded_by=self.user)

        # Create 50 claim records using bulk_create for speed
        claims = []
        for i in range(50):
            claims.append(
                ClaimRecord(
                    customer=self.customer,
                    upload=upload,
                    payer=f"Payer{i % 10}",
                    cpt="99213",
                    cpt_group="OFFICE",
                    outcome="PAID" if i % 2 == 0 else "DENIED",
                    submitted_date=date.today() - timedelta(days=i),
                    decided_date=date.today() - timedelta(days=i - 7),
                    allowed_amount=Decimal("150.00") if i % 2 == 0 else Decimal("0.00"),
                )
            )
        ClaimRecord.objects.bulk_create(claims)

        # Query claims through API
        with override_settings(DEBUG=True):
            from django.db import reset_queries

            reset_queries()

            response = self.client.get("/api/v1/claims/?page_size=50")
            self.assertEqual(response.status_code, 200)

            query_count = len(connection.queries)

            # Should be <10 queries
            self.assertLess(
                query_count,
                10,
                f"ClaimRecord list used {query_count} queries, expected <10",
            )

    def test_drift_computation_query_efficiency(self):
        """
        Story #1: Verify drift computation is efficient with .values() optimization.

        Expected: <15 queries for 100 claims
        """
        from upstream.services.payer_drift import compute_weekly_payer_drift

        upload = self.create_upload(self.customer, uploaded_by=self.user)

        # Create 100 claims spanning baseline and current windows
        claims = []
        today = date.today()
        for i in range(100):
            days_ago = 104 - i
            claims.append(
                ClaimRecord(
                    customer=self.customer,
                    upload=upload,
                    payer=f"Payer{i % 5}",
                    cpt="99213",
                    cpt_group=f"Group{i % 3}",
                    outcome="PAID" if i % 3 == 0 else "DENIED",
                    submitted_date=today - timedelta(days=days_ago),
                    decided_date=today - timedelta(days=days_ago - 5),
                    allowed_amount=Decimal("150.00") if i % 3 == 0 else Decimal("0.00"),
                )
            )
        ClaimRecord.objects.bulk_create(claims)

        # Run drift computation and count queries
        with override_settings(DEBUG=True):
            from django.db import reset_queries

            reset_queries()

            report_run = compute_weekly_payer_drift(
                customer=self.customer, as_of_date=today
            )

            query_count = len(connection.queries)

            # Current .values() implementation is efficient
            self.assertLess(
                query_count,
                15,
                f"Drift computation used {query_count} queries, expected <15",
            )
            self.assertEqual(report_run.status, "success")

    def test_upload_retrieve_with_select_related(self):
        """
        Verify that single upload retrieval also uses select_related.
        """
        upload = Upload.objects.create(
            customer=self.customer,
            filename="test.csv",
            status="success",
            row_count=100,
            uploaded_by=self.user,
        )

        with override_settings(DEBUG=True):
            from django.db import reset_queries

            reset_queries()

            response = self.client.get(f"/api/v1/uploads/{upload.id}/")
            self.assertEqual(response.status_code, 200)

            query_count = len(connection.queries)

            # Should be minimal queries (main query with JOIN + maybe permissions)
            self.assertLessEqual(
                query_count,
                5,
                f"Upload retrieve used {query_count} queries, expected <=5",
            )
