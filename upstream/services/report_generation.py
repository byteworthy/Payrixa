"""
Report Generation Service

Extracts report generation business logic from views into a stateless,
framework-agnostic service layer.

This service is responsible for:
- Generating payer summaries with metrics
- Generating drift reports with analysis
- Generating recovery statistics
- Formatting report data for export (PDF/Excel)

All methods accept domain objects (Customer, date ranges, filters) and return
structured dicts that views/tasks can format into HTTP responses or files.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """
    Stateless service for report generation and formatting.

    All methods are static methods - no instance state.
    This ensures the service is framework-agnostic and easily testable.
    """

    @staticmethod
    def generate_payer_summary(
        customer_id: int,
        date_range: Tuple[date, date],
        claim_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate payer summary report with metrics.

        Aggregates claim data by payer to show:
        - Total claims per payer
        - Approval/denial rates
        - Average decision times
        - Payment metrics

        Args:
            customer_id: ID of the customer
            date_range: Tuple of (start_date, end_date) for report period
            claim_records: Optional list of claim dicts. If None, returns
                empty summary structure.

        Returns:
            dict: Payer summary with keys:
                - period_start: date - Start of reporting period
                - period_end: date - End of reporting period
                - customer_id: int - Customer ID
                - payers: list[dict] - Per-payer metrics
                - total_claims: int - Total claims across all payers
                - overall_approval_rate: float - Overall approval percentage

        Example:
            >>> summary = ReportGenerationService.generate_payer_summary(
            ...     customer_id=1,
            ...     date_range=(date(2024, 1, 1), date(2024, 1, 31)),
            ...     claim_records=claims
            ... )
            >>> print(f"Total claims: {summary['total_claims']}")
        """
        start_date, end_date = date_range

        # Initialize summary structure
        summary = {
            "period_start": start_date,
            "period_end": end_date,
            "customer_id": customer_id,
            "payers": [],
            "total_claims": 0,
            "overall_approval_rate": 0.0,
        }

        if not claim_records:
            return summary

        # Aggregate by payer
        payer_metrics: Dict[str, Dict[str, Any]] = {}

        for claim in claim_records:
            payer = claim.get("payer", "Unknown")
            outcome = claim.get("outcome", "").upper()

            if payer not in payer_metrics:
                payer_metrics[payer] = {
                    "payer_name": payer,
                    "total_claims": 0,
                    "approved_claims": 0,
                    "denied_claims": 0,
                    "approval_rate": 0.0,
                    "denial_rate": 0.0,
                }

            payer_metrics[payer]["total_claims"] += 1

            if outcome == "PAID":
                payer_metrics[payer]["approved_claims"] += 1
            elif outcome == "DENIED":
                payer_metrics[payer]["denied_claims"] += 1

        # Calculate rates and sort
        payer_list = []
        total_claims = 0
        total_approved = 0

        for payer, metrics in payer_metrics.items():
            total = metrics["total_claims"]
            approved = metrics["approved_claims"]
            denied = metrics["denied_claims"]

            if total > 0:
                metrics["approval_rate"] = round((approved / total) * 100, 1)
                metrics["denial_rate"] = round((denied / total) * 100, 1)

            payer_list.append(metrics)
            total_claims += total
            total_approved += approved

        # Sort by total claims descending
        payer_list.sort(key=lambda x: x["total_claims"], reverse=True)

        # Calculate overall approval rate
        overall_approval_rate = 0.0
        if total_claims > 0:
            overall_approval_rate = round((total_approved / total_claims) * 100, 1)

        summary["payers"] = payer_list
        summary["total_claims"] = total_claims
        summary["overall_approval_rate"] = overall_approval_rate

        return summary

    @staticmethod
    def generate_drift_report(
        customer_id: int,
        filters: Optional[Dict[str, Any]] = None,
        drift_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate drift detection report with analysis.

        Summarizes drift events by severity, payer, and drift type.
        Provides actionable insights on significant changes.

        Args:
            customer_id: ID of the customer
            filters: Optional dict with filter criteria:
                - min_severity: float - Minimum severity threshold
                - payer: str - Filter by payer name
                - drift_type: str - Filter by drift type
            drift_events: Optional list of drift event dicts

        Returns:
            dict: Drift report with keys:
                - customer_id: int - Customer ID
                - filters_applied: dict - Filters used
                - total_events: int - Total drift events
                - events_by_severity: dict - Count by severity level
                - events_by_type: dict - Count by drift type
                - top_payers: list[dict] - Payers with most drift
                - critical_events: list[dict] - High severity events
                - summary_text: str - Human-readable summary

        Example:
            >>> report = ReportGenerationService.generate_drift_report(
            ...     customer_id=1,
            ...     filters={"min_severity": 0.7},
            ...     drift_events=events
            ... )
            >>> print(report['summary_text'])
        """
        if filters is None:
            filters = {}

        report = {
            "customer_id": customer_id,
            "filters_applied": filters,
            "total_events": 0,
            "events_by_severity": {"high": 0, "medium": 0, "low": 0},
            "events_by_type": {},
            "top_payers": [],
            "critical_events": [],
            "summary_text": "",
        }

        if not drift_events:
            report["summary_text"] = "No drift events found for the specified period."
            return report

        # Apply filters
        filtered_events = drift_events
        if "min_severity" in filters:
            min_sev = float(filters["min_severity"])
            filtered_events = [
                e for e in filtered_events if e.get("severity", 0) >= min_sev
            ]

        if "payer" in filters:
            payer_filter = filters["payer"].lower()
            filtered_events = [
                e for e in filtered_events if payer_filter in e.get("payer", "").lower()
            ]

        if "drift_type" in filters:
            drift_type = filters["drift_type"]
            filtered_events = [
                e for e in filtered_events if e.get("drift_type") == drift_type
            ]

        report["total_events"] = len(filtered_events)

        # Categorize by severity
        for event in filtered_events:
            severity = event.get("severity", 0)
            if severity >= 0.7:
                report["events_by_severity"]["high"] += 1
            elif severity >= 0.4:
                report["events_by_severity"]["medium"] += 1
            else:
                report["events_by_severity"]["low"] += 1

            # Count by drift type
            drift_type = event.get("drift_type", "UNKNOWN")
            report["events_by_type"][drift_type] = (
                report["events_by_type"].get(drift_type, 0) + 1
            )

        # Find top payers by event count
        payer_counts: Dict[str, int] = {}
        for event in filtered_events:
            payer = event.get("payer", "Unknown")
            payer_counts[payer] = payer_counts.get(payer, 0) + 1

        top_payers = [
            {"payer": payer, "event_count": count}
            for payer, count in sorted(
                payer_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]
        report["top_payers"] = top_payers

        # Get critical events (severity >= 0.9)
        critical_events = [
            {
                "payer": e.get("payer"),
                "drift_type": e.get("drift_type"),
                "severity": e.get("severity"),
                "delta_value": e.get("delta_value"),
            }
            for e in filtered_events
            if e.get("severity", 0) >= 0.9
        ][:10]
        report["critical_events"] = critical_events

        # Generate summary text
        high_count = report["events_by_severity"]["high"]
        medium_count = report["events_by_severity"]["medium"]
        summary_parts = [
            f"Found {len(filtered_events)} drift events.",
            f"{high_count} high severity, {medium_count} medium severity.",
        ]
        if critical_events:
            summary_parts.append(
                f"{len(critical_events)} critical events require immediate attention."
            )
        report["summary_text"] = " ".join(summary_parts)

        return report

    @staticmethod
    def generate_recovery_stats(
        customer_id: int, claim_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate recovery statistics report.

        Calculates metrics related to payment recovery:
        - Total billed vs. allowed vs. paid amounts
        - Recovery rate percentages
        - Underpayment analysis

        Args:
            customer_id: ID of the customer
            claim_records: Optional list of claim dicts with amount fields

        Returns:
            dict: Recovery stats with keys:
                - customer_id: int - Customer ID
                - total_billed: Decimal - Sum of billed amounts
                - total_allowed: Decimal - Sum of allowed amounts
                - total_paid: Decimal - Sum of paid amounts
                - recovery_rate: float - (paid / billed) * 100
                - underpayment_count: int - Claims where paid < allowed
                - underpayment_amount: Decimal - Total underpayment

        Example:
            >>> stats = ReportGenerationService.generate_recovery_stats(
            ...     customer_id=1, claim_records=claims
            ... )
            >>> print(f"Recovery rate: {stats['recovery_rate']:.1f}%")
        """
        stats = {
            "customer_id": customer_id,
            "total_billed": Decimal("0.00"),
            "total_allowed": Decimal("0.00"),
            "total_paid": Decimal("0.00"),
            "recovery_rate": 0.0,
            "underpayment_count": 0,
            "underpayment_amount": Decimal("0.00"),
        }

        if not claim_records:
            return stats

        for claim in claim_records:
            # Parse amounts
            billed = claim.get("billed_amount")
            allowed = claim.get("allowed_amount")
            paid = claim.get("paid_amount")

            if billed is not None:
                stats["total_billed"] += Decimal(str(billed))

            if allowed is not None:
                stats["total_allowed"] += Decimal(str(allowed))

            if paid is not None:
                stats["total_paid"] += Decimal(str(paid))

            # Check for underpayment
            if allowed and paid and Decimal(str(paid)) < Decimal(str(allowed)):
                stats["underpayment_count"] += 1
                stats["underpayment_amount"] += Decimal(str(allowed)) - Decimal(
                    str(paid)
                )

        # Calculate recovery rate
        if stats["total_billed"] > 0:
            stats["recovery_rate"] = round(
                float((stats["total_paid"] / stats["total_billed"]) * 100), 1
            )

        return stats

    @staticmethod
    def format_report_for_export(
        report_data: Dict[str, Any], export_format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Format report data for export to PDF or Excel.

        Prepares report data structure for export generation.
        Returns formatted data structure that export handlers can use.

        Args:
            report_data: Dict with report data to format
            export_format: Export format - 'pdf' or 'xlsx'

        Returns:
            dict: Formatted export data with keys:
                - format: str - Export format requested
                - title: str - Report title
                - sections: list[dict] - Report sections
                - metadata: dict - Export metadata (generated_at, etc.)

        Example:
            >>> export_data = ReportGenerationService.format_report_for_export(
            ...     report_data=summary,
            ...     export_format="pdf"
            ... )
            >>> # Pass export_data to PDF generator
        """
        if export_format not in ["pdf", "xlsx"]:
            raise ValueError(f"Unsupported export format: {export_format}")

        # Extract report type
        report_type = report_data.get("report_type", "report")

        formatted = {
            "format": export_format,
            "title": f"{report_type.replace('_', ' ').title()} Report",
            "sections": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "export_format": export_format,
            },
        }

        # Format sections based on report data keys
        if "payers" in report_data:
            # Payer summary report
            formatted["sections"].append(
                {
                    "title": "Payer Summary",
                    "type": "table",
                    "data": report_data.get("payers", []),
                }
            )

        if "drift_events" in report_data or "total_events" in report_data:
            # Drift report
            formatted["sections"].append(
                {
                    "title": "Drift Analysis",
                    "type": "summary",
                    "data": {
                        "total_events": report_data.get("total_events", 0),
                        "events_by_severity": report_data.get("events_by_severity", {}),
                    },
                }
            )

        if "recovery_rate" in report_data:
            # Recovery stats report
            formatted["sections"].append(
                {
                    "title": "Recovery Statistics",
                    "type": "metrics",
                    "data": {
                        "recovery_rate": report_data.get("recovery_rate", 0),
                        "total_paid": str(report_data.get("total_paid", 0)),
                        "underpayment_count": report_data.get("underpayment_count", 0),
                    },
                }
            )

        return formatted
