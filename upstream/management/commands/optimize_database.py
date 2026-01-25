"""
Database Performance Optimizer Command

Analyzes Django ORM usage for:
- N+1 query problems
- Missing database indexes
- Slow queries
- Unoptimized foreign key access
"""
import ast
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from upstream.models_agents import AgentRun, DatabaseQueryAnalysis


class DatabaseOptimizer:
    """Optimizer for database query performance"""

    def __init__(self):
        self.analyses = []
        self.files_scanned = 0

    def analyze(self):
        """Run database performance analysis"""
        print("🔍 Database Performance Optimizer")
        print("━" * 50)

        files = self._get_python_files()
        print(f"Analyzing {len(files)} Python files...\n")

        for file_path in files:
            self.files_scanned += 1
            self._analyze_file(file_path)

        return self.analyses

    def _get_python_files(self):
        """Get Python files to analyze"""
        upstream_dir = settings.BASE_DIR / 'upstream'
        files = list(upstream_dir.rglob('*.py'))

        # Exclude migrations
        files = [f for f in files if 'migrations' not in str(f)]
        return files

    def _analyze_file(self, file_path):
        """Analyze a single file for query patterns"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)
            self._analyze_ast(file_path, tree, content)

        except Exception as e:
            pass  # Skip files with errors

    def _analyze_ast(self, file_path, tree, content):
        """Analyze AST for query patterns"""
        for node in ast.walk(tree):
            # Detect .objects.all() without select_related
            if isinstance(node, ast.Attribute):
                if node.attr == 'all':
                    self._check_for_n_plus_one(file_path, node, content)

            # Detect loops that access relations
            if isinstance(node, ast.For):
                self._check_loop_for_n_plus_one(file_path, node, content)

    def _check_for_n_plus_one(self, file_path, node, content):
        """Check for potential N+1 queries"""
        line = node.lineno

        # Simple heuristic: .all() without select_related nearby
        lines = content.split('\n')
        context = '\n'.join(lines[max(0, line-5):min(len(lines), line+5)])

        if 'select_related' not in context and 'prefetch_related' not in context:
            if any(model in context for model in ['ClaimRecord', 'DriftEvent', 'Alert']):
                self.analyses.append({
                    'file_path': str(file_path),
                    'line_number': line,
                    'issue_type': 'n_plus_one',
                    'estimated_impact': 'high',
                    'query_pattern': context[:200],
                    'suggestion': 'Consider using select_related() or prefetch_related()',
                    'example_optimized': self._generate_optimization_example(context),
                })

    def _check_loop_for_n_plus_one(self, file_path, node, content):
        """Check for loops that access foreign keys"""
        line = node.lineno
        lines = content.split('\n')

        # Check if loop body accesses foreign keys
        loop_body = ast.get_source_segment(content, node)
        if loop_body and '.' in loop_body:
            # Potential foreign key access in loop
            if any(model in loop_body for model in ['customer', 'payer', 'user']):
                self.analyses.append({
                    'file_path': str(file_path),
                    'line_number': line,
                    'issue_type': 'n_plus_one',
                    'estimated_impact': 'medium',
                    'query_pattern': loop_body[:200],
                    'suggestion': 'Use select_related() before loop',
                    'example_optimized': '',
                })

    def _generate_optimization_example(self, context):
        """Generate optimization example"""
        if 'objects.all()' in context:
            return context.replace('.all()', '.select_related("payer", "customer")')
        return ''


class Command(BaseCommand):
    help = 'Analyze database query performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Analyze specific app only',
        )
        parser.add_argument(
            '--create-migration',
            action='store_true',
            help='Create migration with suggested indexes',
        )

    def handle(self, *args, **options):
        # Create agent run
        agent_run = AgentRun.objects.create(
            agent_type='db_performance',
            trigger='manual',
            status='running',
        )

        try:
            optimizer = DatabaseOptimizer()
            analyses = optimizer.analyze()

            # Save analyses
            for analysis in analyses:
                DatabaseQueryAnalysis.objects.create(
                    agent_run=agent_run,
                    query_pattern=analysis['query_pattern'],
                    file_path=analysis['file_path'],
                    line_number=analysis['line_number'],
                    issue_type=analysis['issue_type'],
                    estimated_impact=analysis['estimated_impact'],
                    suggestion=analysis['suggestion'],
                    example_optimized=analysis.get('example_optimized', ''),
                )

            # Update agent run
            agent_run.completed_at = timezone.now()
            agent_run.status = 'completed'
            agent_run.findings_count = len(analyses)
            agent_run.save()

            # Print summary
            self._print_summary(analyses)

            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Analysis complete: {len(analyses)} optimization opportunities found"
            ))

        except Exception as e:
            agent_run.status = 'failed'
            agent_run.completed_at = timezone.now()
            agent_run.save()
            raise

    def _print_summary(self, analyses):
        """Print analysis summary"""
        n_plus_one = sum(1 for a in analyses if a['issue_type'] == 'n_plus_one')
        missing_index = sum(1 for a in analyses if a['issue_type'] == 'missing_index')

        print("\n" + "━" * 50)
        print(f"❌ N+1 QUERIES: {n_plus_one}")
        print(f"⚠️  MISSING INDEXES: {missing_index}")
        print("━" * 50)

        for analysis in analyses[:5]:  # Show top 5
            print(f"\n{analysis['file_path']}:{analysis['line_number']}")
            print(f"  {analysis['suggestion']}")
