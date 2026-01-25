"""HIPAA Compliance Monitor Command"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from upstream.models_agents import AgentRun, Finding
from upstream.utils import detect_phi


class HIPAAComplianceChecker:
    """Check HIPAA compliance across the application"""

    def __init__(self):
        self.violations = []

    def check_all(self):
        """Run all compliance checks"""
        print("🔍 HIPAA Compliance Monitor")
        print("━" * 50)

        self.check_session_security()
        self.check_audit_logging()
        self.check_phi_detection()
        self.check_encryption()

        return self.violations

    def check_session_security(self):
        """Check session security settings"""
        print("\n✓ Checking session security...")

        if settings.SESSION_COOKIE_AGE != 1800:
            self.violations.append({
                'severity': 'critical',
                'category': 'session_security',
                'title': 'Session timeout not 30 minutes',
                'description': f'SESSION_COOKIE_AGE is {settings.SESSION_COOKIE_AGE}, should be 1800',
                'recommendation': 'Set SESSION_COOKIE_AGE = 1800 in settings',
            })

        if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
            self.violations.append({
                'severity': 'critical',
                'category': 'session_security',
                'title': 'HTTPOnly cookies not enabled',
                'description': 'SESSION_COOKIE_HTTPONLY is False',
                'recommendation': 'Set SESSION_COOKIE_HTTPONLY = True',
            })

    def check_audit_logging(self):
        """Check audit logging configuration"""
        print("✓ Checking audit logging...")

        try:
            from auditlog.models import LogEntry
            recent_logs = LogEntry.objects.count()
            if recent_logs == 0:
                self.violations.append({
                    'severity': 'high',
                    'category': 'audit_logging',
                    'title': 'No audit logs found',
                    'description': 'Audit logging may not be configured',
                    'recommendation': 'Register models with auditlog',
                })
        except ImportError:
            self.violations.append({
                'severity': 'critical',
                'category': 'audit_logging',
                'title': 'Auditlog not installed',
                'description': 'django-auditlog is required for HIPAA compliance',
                'recommendation': 'Install django-auditlog',
            })

    def check_phi_detection(self):
        """Check PHI detection is active"""
        print("✓ Checking PHI detection...")

        # Test PHI detection works
        has_phi, msg = detect_phi("Patient John Smith")
        if not has_phi:
            self.violations.append({
                'severity': 'critical',
                'category': 'phi_detection',
                'title': 'PHI detection not working',
                'description': 'detect_phi() failed to detect obvious PHI',
                'recommendation': 'Check upstream.utils.detect_phi implementation',
            })

    def check_encryption(self):
        """Check field encryption"""
        print("✓ Checking field encryption...")

        # Check FIELD_ENCRYPTION_KEY exists
        if not hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            self.violations.append({
                'severity': 'high',
                'category': 'encryption',
                'title': 'Field encryption key not configured',
                'description': 'FIELD_ENCRYPTION_KEY not found in settings',
                'recommendation': 'Generate and set FIELD_ENCRYPTION_KEY',
            })


class Command(BaseCommand):
    help = 'Check HIPAA compliance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on',
            choices=['critical', 'high', 'medium'],
            default='critical',
        )

    def handle(self, *args, **options):
        agent_run = AgentRun.objects.create(
            agent_type='hipaa_compliance',
            trigger='manual',
            status='running',
        )

        try:
            checker = HIPAAComplianceChecker()
            violations = checker.check_all()

            # Save violations
            critical_count = 0
            for violation in violations:
                if violation['severity'] == 'critical':
                    critical_count += 1

                Finding.objects.create(
                    agent_run=agent_run,
                    severity=violation['severity'],
                    category=violation['category'],
                    title=violation['title'],
                    description=violation['description'],
                    recommendation=violation['recommendation'],
                )

            agent_run.completed_at = timezone.now()
            agent_run.status = 'completed'
            agent_run.findings_count = len(violations)
            agent_run.critical_count = critical_count
            agent_run.save()

            # Print summary
            print("\n" + "━" * 50)
            if critical_count == 0:
                self.stdout.write(self.style.SUCCESS(
                    "✅ HIPAA Compliance: PASSED"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ {critical_count} critical violations found"
                ))
                print("\nViolations:")
                for v in violations:
                    if v['severity'] == 'critical':
                        print(f"  • {v['title']}")

        except Exception as e:
            agent_run.status = 'failed'
            agent_run.completed_at = timezone.now()
            agent_run.save()
            raise
