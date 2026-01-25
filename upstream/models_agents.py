"""
Agent findings models for tracking code quality, security, and compliance issues.
"""
from django.db import models
from django.contrib.auth import get_user_model


class AgentRun(models.Model):
    """Record of an agent execution"""
    AGENT_TYPES = [
        ('code_quality', 'Code Quality Auditor'),
        ('db_performance', 'Database Performance Optimizer'),
        ('test_coverage', 'Test Coverage Analyzer'),
        ('migration_safety', 'Migration Safety Checker'),
        ('hipaa_compliance', 'HIPAA Compliance Monitor'),
    ]

    TRIGGER_TYPES = [
        ('manual', 'Manual Execution'),
        ('pre_commit', 'Pre-Commit Hook'),
        ('pre_deploy', 'Pre-Deploy Check'),
        ('scheduled', 'Scheduled Run'),
    ]

    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    trigger = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='running'
    )
    findings_count = models.IntegerField(default=0)
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    low_count = models.IntegerField(default=0)
    git_commit = models.CharField(max_length=40, blank=True)
    git_branch = models.CharField(max_length=255, blank=True)
    triggered_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    summary = models.TextField(blank=True)
    report_path = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'upstream_agent_run'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['agent_type', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]

    def __str__(self):
        return f"{self.get_agent_type_display()} - {self.started_at}"


class Finding(models.Model):
    """Individual finding from an agent run"""
    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('fixed', 'Fixed'),
        ('ignored', 'Ignored'),
    ]

    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='findings'
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    description = models.TextField()
    file_path = models.CharField(max_length=500, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    code_snippet = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_findings'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'upstream_finding'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent_run', 'severity']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'severity']),
        ]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"


class CodeQualityMetric(models.Model):
    """Code quality metrics over time"""
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='quality_metrics'
    )
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    threshold = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'upstream_code_quality_metric'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_name', '-created_at']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"


class DatabaseQueryAnalysis(models.Model):
    """Database query performance analysis"""
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='query_analyses'
    )
    query_pattern = models.TextField()
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField()
    issue_type = models.CharField(
        max_length=50,
        choices=[
            ('n_plus_one', 'N+1 Query'),
            ('missing_index', 'Missing Index'),
            ('unoptimized', 'Unoptimized Query'),
            ('cartesian_product', 'Cartesian Product'),
        ]
    )
    estimated_impact = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ]
    )
    suggestion = models.TextField()
    example_optimized = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'upstream_db_query_analysis'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.issue_type} in {self.file_path}:{self.line_number}"


class TestCoverageReport(models.Model):
    """Test coverage analysis"""
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='coverage_reports'
    )
    file_path = models.CharField(max_length=500)
    total_lines = models.IntegerField()
    covered_lines = models.IntegerField()
    coverage_percentage = models.FloatField()
    missing_lines = models.JSONField(default=list)  # List of line numbers
    untested_functions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'upstream_test_coverage_report'
        ordering = ['coverage_percentage']

    def __str__(self):
        return f"{self.file_path}: {self.coverage_percentage:.1f}%"


class MigrationAnalysis(models.Model):
    """Migration safety analysis"""
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='migration_analyses'
    )
    migration_file = models.CharField(max_length=500)
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('safe', 'Safe'),
            ('caution', 'Caution'),
            ('high_risk', 'High Risk'),
            ('destructive', 'Destructive'),
        ]
    )
    operations = models.JSONField(default=list)
    potential_issues = models.JSONField(default=list)
    rollback_possible = models.BooleanField(default=True)
    estimated_duration = models.CharField(max_length=100, blank=True)
    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'upstream_migration_analysis'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.migration_file}: {self.risk_level}"
