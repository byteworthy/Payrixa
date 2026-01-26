"""
Tests for model indexes and database schema.

Phase 6: Database Indexes - Verify that composite indexes are created correctly.
"""

from django.test import TestCase
from django.db import connection


class AlertRuleIndexTest(TestCase):
    """Test that AlertRule has the correct composite index."""

    def test_alertrule_has_customer_enabled_index(self):
        """Verify that AlertRule has composite index on (customer, enabled)."""
        # Get the table name for AlertRule
        from upstream.alerts.models import AlertRule
        table_name = AlertRule._meta.db_table

        # Query the database for indexes on the AlertRule table
        with connection.cursor() as cursor:
            # SQLite query to get indexes
            cursor.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=%s",
                [table_name]
            )
            indexes = cursor.fetchall()

        # Convert to a dict for easier checking
        index_dict = {name: sql for name, sql in indexes if sql is not None}

        # Check that the composite index exists
        self.assertIn(
            "idx_alertrule_customer_enabled",
            index_dict,
            f"Expected index 'idx_alertrule_customer_enabled' not found. Available indexes: {list(index_dict.keys())}"
        )

        # Verify the index is on the correct columns
        index_sql = index_dict["idx_alertrule_customer_enabled"]
        self.assertIn("customer_id", index_sql.lower(), "Index should include customer_id column")
        self.assertIn("enabled", index_sql.lower(), "Index should include enabled column")

    def test_alertrule_index_column_order(self):
        """Verify that the index has columns in the correct order (customer, enabled)."""
        from upstream.alerts.models import AlertRule
        table_name = AlertRule._meta.db_table

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_alertrule_customer_enabled'",
            )
            result = cursor.fetchone()

        self.assertIsNotNone(result, "Index 'idx_alertrule_customer_enabled' not found")

        index_sql = result[0]

        # Extract the column list from the SQL: ON table ("col1", "col2")
        # Split by ON, get the part after it, then extract columns from parentheses
        import re
        match = re.search(r'ON\s+\S+\s+\((.+?)\)', index_sql)
        self.assertIsNotNone(match, f"Could not parse columns from SQL: {index_sql}")

        columns_str = match.group(1)
        # Remove quotes and split by comma
        columns = [col.strip().strip('"').strip("'") for col in columns_str.split(',')]

        # Verify column order
        self.assertEqual(len(columns), 2, "Index should have exactly 2 columns")
        self.assertEqual(columns[0], "customer_id", "First column should be customer_id")
        self.assertEqual(columns[1], "enabled", "Second column should be enabled")
