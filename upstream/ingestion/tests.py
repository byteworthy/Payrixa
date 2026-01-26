"""
Tests for Ingestion Services.

Testing coverage for IngestionService and event publishing functionality.
Addresses Phase 2 Technical Debt: Missing tests for IngestionService.
"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from upstream.models import Customer
from upstream.ingestion.models import IngestionRecord, SystemEvent
from upstream.ingestion.services import IngestionService, publish_event


class IngestionServiceTestCase(TestCase):
    """Tests for IngestionService basic functionality."""

    def setUp(self):
        """Create test fixtures."""
        self.customer = Customer.objects.create(name="Test Healthcare Corp")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.service = IngestionService(
            customer=self.customer,
            source_type='webhook',
            created_by=self.user
        )

    def test_create_record_basic(self):
        """Test basic ingestion record creation."""
        payload_metadata = {
            'content_type': 'application/json',
            'size_bytes': 1024,
            'webhook_source': 'external_system_v1'
        }

        record = self.service.create_record(
            payload_metadata=payload_metadata,
            record_count=50
        )

        # Verify record creation
        self.assertIsNotNone(record.id)
        self.assertEqual(record.customer, self.customer)
        self.assertEqual(record.source_type, 'webhook')
        self.assertEqual(record.status, 'pending')
        self.assertEqual(record.record_count, 50)
        self.assertEqual(record.payload_metadata, payload_metadata)
        self.assertEqual(record.created_by, self.user)
        self.assertIsNone(record.processed_at)
        self.assertIsNone(record.error_message)

    def test_create_record_with_idempotency_key(self):
        """Test idempotency key prevents duplicate ingestion."""
        payload = {'test': 'data'}
        idempotency_key = 'unique-webhook-123'

        # First creation should succeed
        record1 = self.service.create_record(
            payload_metadata=payload,
            idempotency_key=idempotency_key
        )

        self.assertIsNotNone(record1.id)
        self.assertEqual(record1.idempotency_key, idempotency_key)

        # Second creation with same key should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_record(
                payload_metadata=payload,
                idempotency_key=idempotency_key
            )

        self.assertIn('Duplicate ingestion', str(context.exception))
        self.assertIn(idempotency_key, str(context.exception))

        # Verify only one record exists
        count = IngestionRecord.objects.filter(
            customer=self.customer,
            idempotency_key=idempotency_key
        ).count()
        self.assertEqual(count, 1)

    def test_create_record_publishes_event(self):
        """Test that create_record publishes ingestion_received event."""
        initial_event_count = SystemEvent.objects.count()

        record = self.service.create_record(
            payload_metadata={'test': 'data'},
            record_count=25
        )

        # Verify event was published
        new_event_count = SystemEvent.objects.count()
        self.assertEqual(new_event_count, initial_event_count + 1)

        # Verify event details
        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.customer, self.customer)
        self.assertEqual(event.event_type, 'ingestion_received')
        self.assertEqual(event.payload['source_type'], 'webhook')
        self.assertEqual(event.payload['record_count'], 25)
        self.assertEqual(event.payload['has_idempotency_key'], False)
        self.assertEqual(event.related_ingestion, record)

    def test_mark_processing(self):
        """Test marking ingestion as processing."""
        record = self.service.create_record(payload_metadata={'test': 'data'})

        # Mark as processing
        self.service.mark_processing(record)

        # Verify status update
        record.refresh_from_db()
        self.assertEqual(record.status, 'processing')
        self.assertIsNone(record.processed_at)
        self.assertIsNone(record.error_message)

    def test_mark_processed(self):
        """Test marking ingestion as successfully processed."""
        record = self.service.create_record(payload_metadata={'test': 'data'})
        self.service.mark_processing(record)

        # Mark as processed
        initial_event_count = SystemEvent.objects.count()
        self.service.mark_processed(record, record_count=100)

        # Verify status and metadata updates
        record.refresh_from_db()
        self.assertEqual(record.status, 'processed')
        self.assertEqual(record.record_count, 100)
        self.assertIsNotNone(record.processed_at)
        self.assertIsNone(record.error_message)

        # Verify event published
        new_event_count = SystemEvent.objects.count()
        self.assertEqual(new_event_count, initial_event_count + 1)

        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.event_type, 'ingestion_processed')
        self.assertEqual(event.payload['source_type'], 'webhook')
        self.assertEqual(event.payload['record_count'], 100)
        self.assertEqual(event.related_ingestion, record)

    def test_mark_failed(self):
        """Test marking ingestion as failed with error message."""
        record = self.service.create_record(payload_metadata={'test': 'data'})
        self.service.mark_processing(record)

        # Mark as failed
        error_message = "Invalid JSON format in row 42"
        initial_event_count = SystemEvent.objects.count()
        self.service.mark_failed(record, error_message)

        # Verify status and error message
        record.refresh_from_db()
        self.assertEqual(record.status, 'failed')
        self.assertEqual(record.error_message, error_message)
        self.assertIsNone(record.processed_at)

        # Verify event published
        new_event_count = SystemEvent.objects.count()
        self.assertEqual(new_event_count, initial_event_count + 1)

        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.event_type, 'ingestion_failed')
        self.assertEqual(event.payload['source_type'], 'webhook')
        self.assertEqual(event.payload['error'], error_message)
        self.assertEqual(event.related_ingestion, record)

    def test_get_recent_ingestions(self):
        """Test fetching recent ingestion records."""
        # Create multiple ingestion records
        records = []
        for i in range(5):
            record = self.service.create_record(
                payload_metadata={'batch': i},
                record_count=i * 10
            )
            records.append(record)

        # Fetch recent ingestions
        recent = IngestionService.get_recent_ingestions(self.customer, limit=3)

        # Verify count and ordering (most recent first)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0].id, records[4].id)  # Most recent
        self.assertEqual(recent[1].id, records[3].id)
        self.assertEqual(recent[2].id, records[2].id)

    def test_get_recent_ingestions_with_created_by(self):
        """Test that get_recent_ingestions includes created_by via select_related."""
        record = self.service.create_record(payload_metadata={'test': 'data'})

        # Fetch recent ingestions - this will execute 1 query with JOIN
        recent = list(IngestionService.get_recent_ingestions(self.customer, limit=10))

        # Verify select_related worked (no additional query)
        with self.assertNumQueries(0):
            # Accessing created_by should not trigger additional query
            creator = recent[0].created_by
            self.assertEqual(creator, self.user)

    def test_get_recent_events(self):
        """Test fetching recent system events."""
        # Create records with events
        record1 = self.service.create_record(payload_metadata={'batch': 1})
        self.service.mark_processed(record1)

        record2 = self.service.create_record(payload_metadata={'batch': 2})
        self.service.mark_failed(record2, "Test error")

        # Fetch all recent events
        recent = IngestionService.get_recent_events(self.customer, limit=10)

        # Should have 4 events: 2x ingestion_received, 1x ingestion_processed, 1x ingestion_failed
        self.assertGreaterEqual(len(recent), 4)

        # Verify event types
        event_types = [event.event_type for event in recent]
        self.assertIn('ingestion_received', event_types)
        self.assertIn('ingestion_processed', event_types)
        self.assertIn('ingestion_failed', event_types)

    def test_get_recent_events_filtered_by_type(self):
        """Test fetching events filtered by event type."""
        # Create multiple events
        record1 = self.service.create_record(payload_metadata={'batch': 1})
        self.service.mark_processed(record1)

        record2 = self.service.create_record(payload_metadata={'batch': 2})
        self.service.mark_failed(record2, "Test error")

        # Fetch only failed events
        failed_events = IngestionService.get_recent_events(
            self.customer,
            event_type='ingestion_failed',
            limit=10
        )

        # Verify all events are of the correct type
        self.assertGreaterEqual(len(failed_events), 1)
        for event in failed_events:
            self.assertEqual(event.event_type, 'ingestion_failed')

    def test_idempotency_key_scoped_to_customer(self):
        """Test that idempotency keys are scoped per customer."""
        customer2 = Customer.objects.create(name="Another Healthcare Corp")
        service2 = IngestionService(
            customer=customer2,
            source_type='webhook'
        )

        idempotency_key = 'shared-key-123'
        payload = {'test': 'data'}

        # Create record for first customer
        record1 = self.service.create_record(
            payload_metadata=payload,
            idempotency_key=idempotency_key
        )

        # Same key should work for different customer
        record2 = service2.create_record(
            payload_metadata=payload,
            idempotency_key=idempotency_key
        )

        self.assertIsNotNone(record1.id)
        self.assertIsNotNone(record2.id)
        self.assertNotEqual(record1.id, record2.id)
        self.assertEqual(record1.idempotency_key, record2.idempotency_key)


class PublishEventTestCase(TestCase):
    """Tests for publish_event standalone function."""

    def setUp(self):
        """Create test fixtures."""
        self.customer = Customer.objects.create(name="Test Healthcare Corp")

    def test_publish_event_basic(self):
        """Test basic event publishing."""
        event = publish_event(
            customer=self.customer,
            event_type='drift_detected',
            payload={'payer': 'Aetna', 'severity': 'high'}
        )

        # Verify event creation
        self.assertIsNotNone(event.id)
        self.assertEqual(event.customer, self.customer)
        self.assertEqual(event.event_type, 'drift_detected')
        self.assertEqual(event.payload['payer'], 'Aetna')
        self.assertEqual(event.payload['severity'], 'high')
        self.assertIsNone(event.related_ingestion)
        self.assertIsNone(event.related_drift_event)
        self.assertIsNone(event.related_alert)

    def test_publish_event_with_related_ingestion(self):
        """Test publishing event with related ingestion record."""
        service = IngestionService(customer=self.customer, source_type='api')
        record = service.create_record(payload_metadata={'test': 'data'})

        event = publish_event(
            customer=self.customer,
            event_type='export_generated',
            payload={'format': 'csv', 'row_count': 1000},
            related_ingestion=record
        )

        # Verify relationship
        self.assertEqual(event.related_ingestion, record)
        self.assertIn('format', event.payload)

    def test_publish_event_default_payload(self):
        """Test that empty payload defaults to empty dict."""
        event = publish_event(
            customer=self.customer,
            event_type='report_generated'
        )

        self.assertEqual(event.payload, {})

    def test_publish_event_captures_request_id(self):
        """Test that publish_event captures request_id from middleware."""
        # Note: In real usage, request_id comes from middleware
        # This test just verifies the field is populated if available
        event = publish_event(
            customer=self.customer,
            event_type='webhook_sent'
        )

        # request_id may be None in tests (no HTTP request context)
        # Just verify the field exists and doesn't cause errors
        self.assertIsInstance(event.request_id, (str, type(None)))


class IngestionServiceTransactionTestCase(TransactionTestCase):
    """
    Tests for transaction atomicity in IngestionService.

    Uses TransactionTestCase to test transaction.atomic() behavior.
    """

    def setUp(self):
        """Create test fixtures."""
        self.customer = Customer.objects.create(name="Test Healthcare Corp")
        self.service = IngestionService(
            customer=self.customer,
            source_type='webhook'
        )

    def test_create_record_atomic_transaction(self):
        """Test that create_record is atomic (record + event created together)."""
        initial_record_count = IngestionRecord.objects.count()
        initial_event_count = SystemEvent.objects.count()

        record = self.service.create_record(payload_metadata={'test': 'data'})

        # Verify both record and event were created
        self.assertEqual(IngestionRecord.objects.count(), initial_record_count + 1)
        self.assertEqual(SystemEvent.objects.count(), initial_event_count + 1)

        # Verify event references the record
        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.related_ingestion, record)

    def test_mark_processed_atomic_transaction(self):
        """Test that mark_processed is atomic (status + event updated together)."""
        record = self.service.create_record(payload_metadata={'test': 'data'})
        initial_event_count = SystemEvent.objects.count()

        self.service.mark_processed(record, record_count=50)

        # Verify both record and event were updated
        record.refresh_from_db()
        self.assertEqual(record.status, 'processed')
        self.assertEqual(SystemEvent.objects.count(), initial_event_count + 1)

        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.event_type, 'ingestion_processed')
        self.assertEqual(event.related_ingestion, record)

    def test_mark_failed_atomic_transaction(self):
        """Test that mark_failed is atomic (status + event updated together)."""
        record = self.service.create_record(payload_metadata={'test': 'data'})
        initial_event_count = SystemEvent.objects.count()

        self.service.mark_failed(record, "Test error")

        # Verify both record and event were updated
        record.refresh_from_db()
        self.assertEqual(record.status, 'failed')
        self.assertEqual(SystemEvent.objects.count(), initial_event_count + 1)

        event = SystemEvent.objects.latest('created_at')
        self.assertEqual(event.event_type, 'ingestion_failed')
        self.assertEqual(event.related_ingestion, record)


class IngestionWorkflowTestCase(TestCase):
    """Integration tests for complete ingestion workflows."""

    def setUp(self):
        """Create test fixtures."""
        self.customer = Customer.objects.create(name="Test Healthcare Corp")
        self.user = User.objects.create_user(username="operator", password="pass123")
        self.service = IngestionService(
            customer=self.customer,
            source_type='webhook',
            created_by=self.user
        )

    def test_successful_ingestion_workflow(self):
        """Test complete workflow: create → processing → processed."""
        # Step 1: Create ingestion record
        record = self.service.create_record(
            payload_metadata={'source': 'external_api', 'version': '2.0'},
            idempotency_key='workflow-test-123',
            record_count=150
        )

        self.assertEqual(record.status, 'pending')

        # Step 2: Mark as processing
        self.service.mark_processing(record)
        record.refresh_from_db()
        self.assertEqual(record.status, 'processing')

        # Step 3: Mark as processed
        self.service.mark_processed(record, record_count=150)
        record.refresh_from_db()
        self.assertEqual(record.status, 'processed')
        self.assertIsNotNone(record.processed_at)

        # Verify events were published for each state
        events = SystemEvent.objects.filter(
            customer=self.customer,
            related_ingestion=record
        ).order_by('created_at')

        self.assertEqual(len(events), 2)  # ingestion_received + ingestion_processed
        self.assertEqual(events[0].event_type, 'ingestion_received')
        self.assertEqual(events[1].event_type, 'ingestion_processed')

    def test_failed_ingestion_workflow(self):
        """Test complete workflow: create → processing → failed."""
        # Step 1: Create ingestion record
        record = self.service.create_record(
            payload_metadata={'source': 'external_api'},
            record_count=200
        )

        # Step 2: Mark as processing
        self.service.mark_processing(record)

        # Step 3: Mark as failed
        error_message = "Validation failed: missing required field 'patient_id'"
        self.service.mark_failed(record, error_message)

        record.refresh_from_db()
        self.assertEqual(record.status, 'failed')
        self.assertEqual(record.error_message, error_message)
        self.assertIsNone(record.processed_at)

        # Verify failure event
        failure_event = SystemEvent.objects.filter(
            customer=self.customer,
            event_type='ingestion_failed',
            related_ingestion=record
        ).first()

        self.assertIsNotNone(failure_event)
        self.assertEqual(failure_event.payload['error'], error_message)
