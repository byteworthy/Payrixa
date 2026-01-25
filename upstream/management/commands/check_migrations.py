"""Migration Safety Checker Command"""
from django.core.management.base import BaseCommand
from django.db.migrations.loader import MigrationLoader
from django.db import connection
from django.utils import timezone
from upstream.models_agents import AgentRun, MigrationAnalysis


class Command(BaseCommand):
    help = 'Check migration safety before running'

    def handle(self, *args, **options):
        agent_run = AgentRun.objects.create(
            agent_type='migration_safety',
            trigger='manual',
            status='running',
        )

        try:
            loader = MigrationLoader(connection)
            pending = []

            for app_name, migration_name in loader.graph.leaf_nodes():
                if (app_name, migration_name) not in loader.applied_migrations:
                    migration = loader.graph.nodes[(app_name, migration_name)]
                    pending.append((app_name, migration_name, migration))

            print(f"🔍 Migration Safety Checker")
            print("━" * 50)
            print(f"\nAnalyzing {len(pending)} pending migrations...\n")

            high_risk_count = 0

            for app_name, migration_name, migration in pending:
                risk = self._assess_risk(migration)
                operations = [op.__class__.__name__ for op in migration.operations]

                # Save analysis
                MigrationAnalysis.objects.create(
                    agent_run=agent_run,
                    migration_file=f"{app_name}/{migration_name}",
                    risk_level=risk,
                    operations=operations,
                    rollback_possible=self._check_reversible(migration),
                )

                # Print
                risk_icon = {'safe': '✅', 'caution': '⚠️', 'high_risk': '🔥', 'destructive': '☢️'}
                print(f"{risk_icon.get(risk, '?')} {app_name}.{migration_name} - {risk.upper()}")
                print(f"   Operations: {', '.join(operations)}")

                if risk in ['high_risk', 'destructive']:
                    high_risk_count += 1
                    print(f"   ⚠️  DATA LOSS RISK!")

            agent_run.completed_at = timezone.now()
            agent_run.status = 'completed'
            agent_run.findings_count = len(pending)
            agent_run.critical_count = high_risk_count
            agent_run.save()

            if high_risk_count > 0:
                self.stdout.write(self.style.ERROR(
                    f"\n❌ {high_risk_count} high-risk migrations detected"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n✅ All migrations are safe"
                ))

        except Exception as e:
            agent_run.status = 'failed'
            agent_run.completed_at = timezone.now()
            agent_run.save()
            raise

    def _assess_risk(self, migration):
        """Assess migration risk level"""
        operations = [op.__class__.__name__ for op in migration.operations]

        # Destructive operations
        if any(op in operations for op in ['DeleteModel', 'RunSQL']):
            return 'destructive'

        # High risk
        if any(op in operations for op in ['RemoveField', 'AlterField']):
            return 'high_risk'

        # Caution
        if any(op in operations for op in ['RenameField', 'AlterModelTable']):
            return 'caution'

        # Safe
        return 'safe'

    def _check_reversible(self, migration):
        """Check if migration is reversible"""
        for operation in migration.operations:
            if not operation.reversible:
                return False
        return True
