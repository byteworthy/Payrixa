#!/usr/bin/env python3
"""
Performance Regression Detection Script

Compares current Locust test results against historical baseline and fails
if performance degrades significantly.

Thresholds:
- p50 regression > 20%: WARNING
- p95 regression > 20%: FAIL
- p99 regression > 25%: WARNING
- Error rate increase > 2%: FAIL
- Throughput decrease > 30%: WARNING

Usage:
    # Normal CI check (fails on regression)
    python scripts/check_performance_regression.py \
        perf_results_stats.csv

    # Bootstrap initial baseline
    python scripts/check_performance_regression.py \
        perf_results_stats.csv --update-baseline

    # Strict mode (treat warnings as failures)
    python scripts/check_performance_regression.py \
        perf_results_stats.csv --strict
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def load_baseline(baseline_path: str) -> Optional[Dict]:
    """Load baseline metrics from JSON file.

    Returns:
        Baseline data dict or None if file doesn't exist.
    """
    path = Path(baseline_path)
    if not path.exists():
        return None

    with open(path, "r") as f:
        return json.load(f)


def save_baseline(
    baseline_path: str,
    metrics: Dict,
    commit: str = "unknown",
    notes: str = "",
) -> None:
    """Save baseline metrics to JSON file.

    Args:
        baseline_path: Path to baseline JSON file
        metrics: Performance metrics dict
        commit: Git commit hash
        notes: Optional notes about this baseline
    """
    baseline = {
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "metrics": metrics,
        "notes": notes,
    }

    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"✓ Baseline saved to {baseline_path}")


def parse_locust_csv(csv_path: str) -> Dict[str, float]:
    """Parse Locust CSV output and extract performance metrics.

    Args:
        csv_path: Path to Locust stats CSV file

    Returns:
        Dict with performance metrics (p50, p95, p99, etc.)
    """
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Find the aggregated row
            if row["Name"] == "Aggregated":
                total_requests = float(row["Request Count"])
                failure_count = float(row["Failure Count"])

                return {
                    "p50": float(row["50%"]),
                    "p95": float(row["95%"]),
                    "p99": float(row["99%"]),
                    "avg_response_time": float(row["Average Response Time"]),
                    "requests_per_sec": float(row["Requests/s"]),
                    "error_rate": ((failure_count / max(total_requests, 1)) * 100),
                    "total_requests": int(total_requests),
                    "failure_count": int(failure_count),
                }

    raise ValueError(f"No 'Aggregated' row found in {csv_path}")


def calculate_change_percent(current: float, baseline: float) -> float:
    """Calculate percentage change from baseline to current."""
    if baseline == 0:
        return 0.0
    return ((current - baseline) / baseline) * 100


def check_regression(current: Dict, baseline: Dict, strict: bool = False) -> Dict:
    """Check if current metrics show regression from baseline.

    Args:
        current: Current performance metrics
        baseline: Historical baseline data (with 'metrics' key)
        strict: If True, treat warnings as failures

    Returns:
        Dict with 'passed', 'failures', 'warnings' keys
    """
    baseline_metrics = baseline["metrics"]
    failures = []
    warnings = []

    # Check p95 latency (FAIL threshold: >20%)
    p95_change = calculate_change_percent(current["p95"], baseline_metrics["p95"])
    if p95_change > 20:
        failures.append(
            {
                "metric": "p95",
                "current": current["p95"],
                "baseline": baseline_metrics["p95"],
                "change_pct": p95_change,
                "threshold": 20,
                "reason": (
                    f"p95 latency regressed by {p95_change:.1f}% " "(threshold: 20%)"
                ),
            }
        )

    # Check p50 latency (WARNING threshold: >20%)
    p50_change = calculate_change_percent(current["p50"], baseline_metrics["p50"])
    if p50_change > 20:
        warnings.append(
            {
                "metric": "p50",
                "current": current["p50"],
                "baseline": baseline_metrics["p50"],
                "change_pct": p50_change,
                "threshold": 20,
                "reason": (
                    f"p50 latency regressed by {p50_change:.1f}% " "(threshold: 20%)"
                ),
            }
        )

    # Check p99 latency (WARNING threshold: >25%)
    p99_change = calculate_change_percent(current["p99"], baseline_metrics["p99"])
    if p99_change > 25:
        warnings.append(
            {
                "metric": "p99",
                "current": current["p99"],
                "baseline": baseline_metrics["p99"],
                "change_pct": p99_change,
                "threshold": 25,
                "reason": (
                    f"p99 latency regressed by {p99_change:.1f}% " "(threshold: 25%)"
                ),
            }
        )

    # Check error rate (FAIL threshold: >2% absolute increase)
    error_rate_increase = current["error_rate"] - baseline_metrics["error_rate"]
    if error_rate_increase > 2:
        failures.append(
            {
                "metric": "error_rate",
                "current": current["error_rate"],
                "baseline": baseline_metrics["error_rate"],
                "change_pct": error_rate_increase,
                "threshold": 2,
                "reason": (
                    f"Error rate increased by {error_rate_increase:.1f}% "
                    "(threshold: 2%)"
                ),
            }
        )

    # Check throughput (WARNING threshold: >30% decrease)
    throughput_change = calculate_change_percent(
        current["requests_per_sec"], baseline_metrics["requests_per_sec"]
    )
    if throughput_change < -30:
        warnings.append(
            {
                "metric": "requests_per_sec",
                "current": current["requests_per_sec"],
                "baseline": baseline_metrics["requests_per_sec"],
                "change_pct": throughput_change,
                "threshold": -30,
                "reason": (
                    f"Throughput decreased by "
                    f"{abs(throughput_change):.1f}% (threshold: 30%)"
                ),
            }
        )

    # In strict mode, convert warnings to failures
    if strict and warnings:
        failures.extend(warnings)
        warnings = []

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "warnings": warnings,
    }


def format_comparison_table(current: Dict, baseline: Optional[Dict]) -> str:
    """Format a comparison table showing current vs baseline metrics."""
    if baseline is None:
        return "No baseline available for comparison."

    baseline_metrics = baseline["metrics"]

    lines = []
    lines.append("\nPerformance Comparison:")
    lines.append("=" * 80)
    lines.append(
        f"{'Metric':<20} {'Current':>12} {'Baseline':>12} "
        f"{'Change':>12} {'Status':<15}"
    )
    lines.append("-" * 80)

    # Helper function to format row
    def add_row(
        label: str,
        current_val: float,
        baseline_val: float,
        unit: str,
        threshold: float,
        reverse: bool = False,
    ):
        change_pct = calculate_change_percent(current_val, baseline_val)

        # Determine status
        if reverse:
            # For throughput, negative change is bad
            if change_pct < threshold:
                status = "⚠ WARNING"
            elif change_pct < 0:
                status = "↓ Slower"
            else:
                status = "✓ OK"
        else:
            # For latency/errors, positive change is bad
            if change_pct > threshold:
                status = "✗ FAIL" if label in ["p95", "Error Rate"] else "⚠ WARNING"
            elif change_pct > 0:
                status = "↑ Worse"
            else:
                status = "✓ OK"

        lines.append(
            f"{label:<20} {current_val:>11.1f}{unit} "
            f"{baseline_val:>11.1f}{unit} "
            f"{change_pct:>+10.1f}% {status:<15}"
        )

    # Add metrics
    add_row("p50", current["p50"], baseline_metrics["p50"], "ms", 20)
    add_row("p95", current["p95"], baseline_metrics["p95"], "ms", 20)
    add_row("p99", current["p99"], baseline_metrics["p99"], "ms", 25)
    add_row(
        "Avg Response",
        current["avg_response_time"],
        baseline_metrics["avg_response_time"],
        "ms",
        20,
    )
    add_row(
        "Throughput",
        current["requests_per_sec"],
        baseline_metrics["requests_per_sec"],
        "/s",
        -30,
        reverse=True,
    )

    # Error rate (absolute change, not percentage)
    error_change = current["error_rate"] - baseline_metrics["error_rate"]
    error_status = (
        "✗ FAIL" if error_change > 2 else "✓ OK" if error_change <= 0 else "↑ Worse"
    )
    lines.append(
        f"{'Error Rate':<20} {current['error_rate']:>11.1f}% "
        f"{baseline_metrics['error_rate']:>11.1f}% "
        f"{error_change:>+10.1f}% {error_status:<15}"
    )

    lines.append("=" * 80)
    baseline_time = baseline["timestamp"]
    baseline_commit = baseline["commit"][:7]
    lines.append(f"\nBaseline from: {baseline_time} (commit: {baseline_commit})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check for performance regressions against baseline"
    )
    parser.add_argument(
        "csv_file",
        help=("Path to Locust CSV stats file " "(e.g., perf_results_stats.csv)"),
    )
    parser.add_argument(
        "--baseline",
        default="perf_baseline.json",
        help="Path to baseline JSON file (default: perf_baseline.json)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help=(
            "Update baseline with current results "
            "(use after legitimate performance changes)"
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--commit",
        default="unknown",
        help="Git commit hash for baseline metadata",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed comparison table",
    )

    args = parser.parse_args()

    # Parse current results
    try:
        current_metrics = parse_locust_csv(args.csv_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    print("📊 Current Performance Metrics:")
    print(f"  - p50: {current_metrics['p50']:.0f}ms")
    print(f"  - p95: {current_metrics['p95']:.0f}ms")
    print(f"  - p99: {current_metrics['p99']:.0f}ms")
    print(f"  - Throughput: {current_metrics['requests_per_sec']:.1f} req/s")
    print(f"  - Error rate: {current_metrics['error_rate']:.1f}%")
    print(f"  - Total requests: {current_metrics['total_requests']}")

    # Load baseline
    baseline = load_baseline(args.baseline)

    # Update baseline mode
    if args.update_baseline:
        save_baseline(
            args.baseline,
            current_metrics,
            commit=args.commit,
            notes="Updated baseline",
        )
        return 0

    # Bootstrap mode (no baseline exists)
    if baseline is None:
        print(f"\n⚠ No baseline found at {args.baseline}")
        print("Creating initial baseline from current run...")
        save_baseline(
            args.baseline,
            current_metrics,
            commit=args.commit,
            notes="Initial baseline from Phase 5 completion",
        )
        print("✓ Bootstrap complete. " "Next run will compare against this baseline.")
        return 0

    # Regression check
    result = check_regression(current_metrics, baseline, strict=args.strict)

    # Show comparison table if verbose or if there are issues
    if args.verbose or not result["passed"] or result["warnings"]:
        print(format_comparison_table(current_metrics, baseline))

    # Report results
    if result["failures"]:
        print(
            f"\n✗ Performance regression detected "
            f"({len(result['failures'])} failures):"
        )
        for failure in result["failures"]:
            print(f"  - {failure['reason']}")

        if result["warnings"]:
            print(f"\n⚠ Additional warnings " f"({len(result['warnings'])} warnings):")
            for warning in result["warnings"]:
                print(f"  - {warning['reason']}")

        return 1

    if result["warnings"]:
        print(
            f"\n⚠ Performance warnings detected "
            f"({len(result['warnings'])} warnings):"
        )
        for warning in result["warnings"]:
            print(f"  - {warning['reason']}")
        print("\nCI will pass, but consider investigating these regressions.")

    if not result["warnings"]:
        print("\n✓ Performance check PASSED - no regressions detected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
