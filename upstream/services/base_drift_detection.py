"""
Base drift detection service providing common patterns for all drift detection products.

This module defines the abstract base class and shared utilities for:
- DriftWatch (denial rate, payment variance, processing time drift)
- DelayGuard (payment delay monitoring)
- DenialScope (denial reason analysis)

Architecture Pattern: Template Method + Strategy Pattern
- Template Method: Defines computation workflow skeleton
- Strategy Pattern: Subclasses implement specific detection algorithms

Related to ARCH-3 (Technical Debt): Drift detection abstraction.
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Tuple, TypedDict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from upstream.models import Customer
from upstream.ingestion.services import publish_event
from upstream.metrics import drift_computation_time
import logging

logger = logging.getLogger(__name__)


class TimeWindow(TypedDict):
    """Time window for baseline vs current comparison."""

    start: date
    end: date


class ComputationResult(TypedDict):
    """Standard result structure for drift detection computations."""

    signals_created: int
    aggregates_created: int
    baseline_window: TimeWindow
    current_window: TimeWindow
    metadata: Dict[str, Any]


class BaseDriftDetectionService(ABC):
    """
    Abstract base class for drift detection services.

    Provides common infrastructure for:
    - Time window computation
    - Statistical comparison patterns
    - Transaction management
    - Event publishing
    - Result structuring

    Subclasses must implement:
    - _compute_aggregates(): Compute daily/periodic aggregates
    - _detect_signals(): Detect meaningful drift signals
    - _get_signal_type_name(): Return product-specific signal type

    Usage:
        class MyDriftService(BaseDriftDetectionService):
            def _compute_aggregates(self, start_date, end_date):
                # Product-specific aggregate logic
                return aggregates

            def _detect_signals(self, baseline_window, current_window):
                # Product-specific signal detection
                return signals

            def _get_signal_type_name(self):
                return "my_product_drift"
    """

    # Subclasses can override these defaults
    DEFAULT_BASELINE_DAYS = 90
    DEFAULT_CURRENT_DAYS = 14
    MIN_SAMPLE_SIZE = 20
    SIGNIFICANCE_THRESHOLD = 0.05

    def __init__(self, customer: Customer):
        """
        Initialize drift detection service for a customer.

        Args:
            customer: The customer to analyze drift for
        """
        self.customer = customer

    def compute(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> ComputationResult:
        """
        Main computation entry point following template method pattern.

        Workflow:
        1. Compute time windows (baseline vs current)
        2. Compute aggregates within transaction
        3. Detect signals based on aggregates
        4. Publish audit events
        5. Return structured results

        Args:
            start_date: Optional start date (defaults to DEFAULT_BASELINE_DAYS ago)
            end_date: Optional end date (defaults to today)
            **kwargs: Product-specific parameters passed to subclass methods

        Returns:
            ComputationResult with signals_created, aggregates_created, and windows
        """
        # Track drift computation time
        product_name = self._get_product_name()
        with drift_computation_time.labels(product=product_name).time():
            # Step 1: Compute time windows
            baseline_window, current_window = self._compute_time_windows(
                start_date, end_date
            )

            logger.info(
                f"{self.__class__.__name__}: Computing drift for {self.customer.name} "
                f"(baseline: {baseline_window['start']} to {baseline_window['end']}, "
                f"current: {current_window['start']} to {current_window['end']})"
            )

            # Step 2-4: Transaction-wrapped computation
            with transaction.atomic():
                # Compute aggregates
                aggregates = self._compute_aggregates(
                    start_date=baseline_window['start'],
                    end_date=current_window['end'],
                    **kwargs
                )
                aggregates_created = len(aggregates) if isinstance(aggregates, list) else aggregates

                # Detect signals
                signals = self._detect_signals(
                    baseline_window=baseline_window,
                    current_window=current_window,
                    **kwargs
                )
                signals_created = len(signals) if isinstance(signals, list) else signals

                # Publish audit event
                self._publish_computation_event(
                    signals_created=signals_created,
                    aggregates_created=aggregates_created
                )

            # Step 5: Return structured results
            return ComputationResult(
                signals_created=signals_created,
                aggregates_created=aggregates_created,
                baseline_window=baseline_window,
                current_window=current_window,
                metadata=self._get_result_metadata(signals_created, aggregates_created)
            )

    def _compute_time_windows(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Tuple[TimeWindow, TimeWindow]:
        """
        Compute baseline and current time windows for comparison.

        Window strategy:
        - Current window: Most recent DEFAULT_CURRENT_DAYS
        - Baseline window: DEFAULT_BASELINE_DAYS before current window

        Args:
            start_date: Optional absolute start date (overrides defaults)
            end_date: Optional end date (defaults to today)

        Returns:
            Tuple of (baseline_window, current_window)
        """
        if end_date is None:
            end_date = timezone.now().date()

        if start_date is None:
            start_date = end_date - timedelta(
                days=self.DEFAULT_BASELINE_DAYS + self.DEFAULT_CURRENT_DAYS
            )

        # Current window: most recent period
        current_end = end_date
        current_start = max(
            start_date,
            current_end - timedelta(days=self.DEFAULT_CURRENT_DAYS)
        )

        # Baseline window: comparison period before current
        baseline_end = current_start
        baseline_start = max(
            start_date,
            baseline_end - timedelta(days=self.DEFAULT_BASELINE_DAYS)
        )

        baseline_window = TimeWindow(start=baseline_start, end=baseline_end)
        current_window = TimeWindow(start=current_start, end=current_end)

        return baseline_window, current_window

    @staticmethod
    def compute_percentage_change(
        baseline_value: float,
        current_value: float
    ) -> float:
        """
        Compute percentage change from baseline to current.

        Args:
            baseline_value: Baseline metric value
            current_value: Current metric value

        Returns:
            Percentage change (e.g., 0.15 for 15% increase)
            Returns 0.0 if baseline is 0 or None
        """
        if not baseline_value or baseline_value == 0:
            return 0.0
        return (current_value - baseline_value) / baseline_value

    @staticmethod
    def compute_z_score(
        value: float,
        mean: float,
        std_dev: float
    ) -> float:
        """
        Compute z-score for statistical significance testing.

        Args:
            value: Observed value
            mean: Population mean
            std_dev: Population standard deviation

        Returns:
            Z-score (number of standard deviations from mean)
            Returns 0.0 if std_dev is 0 or None
        """
        if not std_dev or std_dev == 0:
            return 0.0
        return (value - mean) / std_dev

    @staticmethod
    def categorize_severity(
        delta_magnitude: float,
        thresholds: Dict[str, float]
    ) -> str:
        """
        Categorize severity based on delta magnitude and thresholds.

        Args:
            delta_magnitude: Absolute magnitude of change
            thresholds: Dict with 'critical', 'high', 'medium', 'low' thresholds

        Returns:
            Severity category string: 'critical', 'high', 'medium', or 'low'
        """
        if delta_magnitude >= thresholds.get('critical', 0.30):
            return 'critical'
        elif delta_magnitude >= thresholds.get('high', 0.20):
            return 'high'
        elif delta_magnitude >= thresholds.get('medium', 0.10):
            return 'medium'
        else:
            return 'low'

    @staticmethod
    def compute_confidence_score(
        sample_size: int,
        z_score: float,
        min_sample_size: int = 20,
        significance_threshold: float = 0.05
    ) -> Decimal:
        """
        Compute confidence score for statistical significance.

        Combines sample size adequacy with statistical significance.

        Args:
            sample_size: Number of observations
            z_score: Z-score from statistical test
            min_sample_size: Minimum sample size threshold
            significance_threshold: P-value threshold (e.g., 0.05 for 95% confidence)

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Sample size adequacy (0.0 to 0.5)
        sample_factor = min(sample_size / (min_sample_size * 2), 1.0) * 0.5

        # Statistical significance (0.0 to 0.5)
        # Z-score > 1.96 indicates p < 0.05 (95% confidence)
        z_threshold = 1.96  # For 95% confidence (p < 0.05)
        significance_factor = min(abs(z_score) / z_threshold, 1.0) * 0.5

        confidence = Decimal(str(sample_factor + significance_factor))
        return min(confidence, Decimal('1.0'))

    def _publish_computation_event(
        self,
        signals_created: int,
        aggregates_created: int
    ) -> None:
        """
        Publish audit event for drift computation.

        Args:
            signals_created: Number of signals detected
            aggregates_created: Number of aggregates computed
        """
        publish_event(
            customer=self.customer,
            event_type=self._get_signal_type_name(),
            entity_type=self.__class__.__name__,
            entity_id=str(self.customer.id),
            payload={
                'signals_created': signals_created,
                'aggregates_created': aggregates_created,
                'product': self._get_product_name(),
            }
        )

    def _get_result_metadata(
        self,
        signals_created: int,
        aggregates_created: int
    ) -> Dict[str, Any]:
        """
        Get product-specific metadata for computation result.

        Subclasses can override to add custom metadata.

        Args:
            signals_created: Number of signals detected
            aggregates_created: Number of aggregates computed

        Returns:
            Dict of metadata to include in result
        """
        return {
            'product': self._get_product_name(),
            'customer': self.customer.name,
        }

    # Abstract methods that subclasses must implement

    @abstractmethod
    def _compute_aggregates(
        self,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> List[Any]:
        """
        Compute product-specific aggregates for the date range.

        This method should query ClaimRecord data and create aggregate
        records (e.g., PaymentDelayAggregate, DenialAggregate, etc.).

        Args:
            start_date: Start date for aggregation (inclusive)
            end_date: End date for aggregation (exclusive)
            **kwargs: Product-specific parameters

        Returns:
            List of aggregate model instances or count
        """
        pass

    @abstractmethod
    def _detect_signals(
        self,
        baseline_window: TimeWindow,
        current_window: TimeWindow,
        **kwargs
    ) -> List[Any]:
        """
        Detect meaningful drift signals by comparing windows.

        This method should compare baseline vs current aggregates
        and create signal records when meaningful drift is detected.

        Args:
            baseline_window: Baseline comparison window
            current_window: Current analysis window
            **kwargs: Product-specific parameters

        Returns:
            List of signal model instances or count
        """
        pass

    @abstractmethod
    def _get_signal_type_name(self) -> str:
        """
        Get product-specific signal type name for audit events.

        Returns:
            Signal type string (e.g., 'payment_delay_drift', 'denial_spike')
        """
        pass

    @abstractmethod
    def _get_product_name(self) -> str:
        """
        Get product name for logging and metadata.

        Returns:
            Product name string (e.g., 'DelayGuard', 'DriftWatch', 'DenialScope')
        """
        pass
