"""
Report Scheduler Service

Extracts report scheduling business logic from Celery tasks into a stateless,
framework-agnostic service layer.

This service is responsible for:
- Scheduling weekly reports (creating ReportRun records)
- Computing drift for report runs
- Coordinating artifact generation (PDF/CSV)
- Managing report status transitions

All methods are static - no instance state.
This ensures the service is framework-agnostic and easily testable.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from upstream.models import Customer, ReportRun

logger = logging.getLogger(__name__)


class ReportSchedulerService:
    """
    Stateless service for report scheduling and orchestration.

    Coordinates report run lifecycle:
    - Creating ReportRun records
    - Triggering drift computation
    - Coordinating artifact generation
    - Managing report status transitions

    All methods are static - no instance state.
    """

    @staticmethod
    def schedule_weekly_report(
        customer: "Customer",
        period_start: date,
        period_end: date,
    ) -> Dict[str, Any]:
        """
        Schedule a weekly drift report for a customer.

        Creates ReportRun, coordinates drift computation and PDF generation.
        This is the business logic currently in send_scheduled_report_task.

        Args:
            customer: Customer instance to generate report for
            period_start: Start date of report period
            period_end: End date of report period

        Returns:
            dict with keys:
                - report_run_id: int - Created ReportRun ID
                - status: str - Completion status ('success' or 'failed')
                - events_detected: int - Number of drift events found
                - artifact_id: int|None - Generated PDF artifact ID

        Example:
            >>> result = ReportSchedulerService.schedule_weekly_report(
            ...     customer=customer,
            ...     period_start=date(2024, 1, 1),
            ...     period_end=date(2024, 1, 7)
            ... )
            >>> print(f"Report run ID: {result['report_run_id']}")
        """
        from upstream.models import ReportRun
        from upstream.services.payer_drift import compute_weekly_payer_drift
        from upstream.reporting.services import generate_weekly_drift_pdf

        try:
            logger.info(
                f"Scheduling weekly report for customer {customer.id} "
                f"({period_start} to {period_end})"
            )

            # Create ReportRun record
            report_run = ReportRun.objects.create(
                customer=customer,
                period_start=period_start,
                period_end=period_end,
                status="pending",
                summary_json={
                    "baseline_start": str(period_start),
                    "baseline_end": str(period_end),
                    "current_start": str(period_start),
                    "current_end": str(period_end),
                },
            )

            logger.info(f"Created ReportRun {report_run.id}")

            # Compute drift for this report run
            report_run = compute_weekly_payer_drift(customer, report_run=report_run)

            # Count drift events
            drift_event_count = report_run.drift_events.count()
            logger.info(
                f"Computed drift for ReportRun {report_run.id}: "
                f"{drift_event_count} events"
            )

            # Generate PDF artifact
            artifact = generate_weekly_drift_pdf(report_run.id)
            logger.info(
                f"Generated PDF artifact {artifact.id} for ReportRun {report_run.id}"
            )

            # Update report run status to completed
            report_run.status = "completed"
            report_run.save()

            return {
                "report_run_id": report_run.id,
                "status": "success",
                "events_detected": drift_event_count,
                "artifact_id": artifact.id,
            }

        except Exception as e:
            logger.error(
                f"Error scheduling report for customer {customer.id}: {str(e)}",
                exc_info=True,
            )
            # Mark report as failed if it exists
            try:
                if "report_run" in locals() and report_run:
                    report_run.status = "failed"
                    report_run.save()
            except Exception:
                pass

            return {
                "report_run_id": locals().get("report_run").id
                if "report_run" in locals()
                else None,
                "status": "failed",
                "events_detected": 0,
                "artifact_id": None,
                "error": str(e),
            }

    @staticmethod
    def compute_report_drift(report_run: "ReportRun") -> Dict[str, Any]:
        """
        Compute drift events for a report run.

        Coordinates drift computation and updates ReportRun status.
        This is the business logic currently in compute_report_drift_task.

        Args:
            report_run: ReportRun instance to compute drift for

        Returns:
            dict with keys:
                - report_run_id: int - Report run ID
                - events_detected: int - Number of drift events found
                - status: str - Completion status ('success' or 'failed')

        Example:
            >>> result = ReportSchedulerService.compute_report_drift(report_run)
            >>> print(f"Found {result['events_detected']} drift events")
        """
        from upstream.services.payer_drift import compute_weekly_payer_drift

        try:
            logger.info(f"Computing drift for report run {report_run.id}")

            # Compute drift for this report run
            report_run = compute_weekly_payer_drift(
                report_run.customer, report_run=report_run
            )

            # Update report run status
            report_run.status = "completed"
            report_run.save()

            # Count drift events for this report
            drift_event_count = report_run.drift_events.count()
            logger.info(
                f"Completed drift computation for report run {report_run.id}: "
                f"{drift_event_count} events"
            )

            return {
                "report_run_id": report_run.id,
                "events_detected": drift_event_count,
                "status": "success",
            }

        except Exception as e:
            logger.error(
                f"Error computing drift for report run {report_run.id}: {str(e)}",
                exc_info=True,
            )
            # Mark report as failed
            try:
                report_run.status = "failed"
                report_run.save()
            except Exception:
                pass

            return {
                "report_run_id": report_run.id,
                "events_detected": 0,
                "status": "failed",
                "error": str(e),
            }

    @staticmethod
    def generate_report_artifact(
        report_run: "ReportRun",
        artifact_type: str = "pdf",
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate report artifact (PDF/CSV) for a report run.

        Delegates to reporting/services.py for actual generation.
        This is the business logic currently in generate_report_artifact_task.

        Args:
            report_run: ReportRun instance to generate artifact for
            artifact_type: Type of artifact ('pdf' or 'csv')
            params: Optional parameters for artifact generation (e.g., filters)

        Returns:
            dict with keys:
                - artifact_id: int|None - Generated artifact ID
                - artifact_type: str - Type of artifact generated
                - file_path: str|None - Path to generated file
                - status: str - Completion status ('success' or 'failed')

        Example:
            >>> result = ReportSchedulerService.generate_report_artifact(
            ...     report_run=report_run,
            ...     artifact_type="pdf"
            ... )
            >>> print(f"Generated: {result['file_path']}")
        """
        from upstream.reporting.services import (
            generate_weekly_drift_pdf,
            generate_drift_events_csv,
        )

        try:
            logger.info(
                f"Generating {artifact_type} artifact for report run {report_run.id}"
            )

            if artifact_type == "pdf":
                artifact = generate_weekly_drift_pdf(report_run.id)
            elif artifact_type == "csv":
                artifact = generate_drift_events_csv(report_run, params=params)
            else:
                raise ValueError(f"Unsupported artifact type: {artifact_type}")

            logger.info(
                f"Generated {artifact_type} artifact {artifact.id} "
                f"for report run {report_run.id}"
            )

            return {
                "artifact_id": artifact.id,
                "artifact_type": artifact_type,
                "file_path": artifact.file_path,
                "status": "success",
            }

        except Exception as e:
            logger.error(
                f"Error generating {artifact_type} artifact "
                f"for report run {report_run.id}: {str(e)}",
                exc_info=True,
            )

            return {
                "artifact_id": None,
                "artifact_type": artifact_type,
                "file_path": None,
                "status": "failed",
                "error": str(e),
            }
