"""Test Coverage Analyzer Command"""
import subprocess
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from upstream.models_agents import AgentRun, TestCoverageReport


class Command(BaseCommand):
    help = 'Analyze test coverage and identify gaps'

    def add_arguments(self, parser):
        parser.add_argument('--min-coverage', type=int, default=75)
        parser.add_argument('--html', action='store_true')

    def handle(self, *args, **options):
        agent_run = AgentRun.objects.create(
            agent_type='test_coverage',
            trigger='manual',
            status='running',
        )

        try:
            # Run pytest with coverage
            result = subprocess.run(
                ['pytest', '--cov=upstream', '--cov-report=json', '--cov-report=term'],
                capture_output=True,
                text=True,
                cwd=settings.BASE_DIR
            )

            # Parse coverage JSON
            coverage_file = settings.BASE_DIR / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                overall_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)

                # Store coverage reports
                for file_path, file_data in coverage_data.get('files', {}).items():
                    summary = file_data.get('summary', {})
                    TestCoverageReport.objects.create(
                        agent_run=agent_run,
                        file_path=file_path,
                        total_lines=summary.get('num_statements', 0),
                        covered_lines=summary.get('covered_lines', 0),
                        coverage_percentage=summary.get('percent_covered', 0),
                        missing_lines=file_data.get('missing_lines', []),
                    )

                agent_run.completed_at = timezone.now()
                agent_run.status = 'completed'
                agent_run.summary = f"Overall coverage: {overall_coverage:.1f}%"
                agent_run.save()

                self.stdout.write(self.style.SUCCESS(
                    f"✅ Coverage: {overall_coverage:.1f}%"
                ))

                if overall_coverage < options['min_coverage']:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Below minimum threshold of {options['min_coverage']}%"
                    ))

        except Exception as e:
            agent_run.status = 'failed'
            agent_run.completed_at = timezone.now()
            agent_run.summary = str(e)
            agent_run.save()
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
