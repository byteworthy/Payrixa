---
phase: quick-030
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/migration-tests.yml
  - scripts/test_migrations.py
autonomous: true

must_haves:
  truths:
    - "Fresh migrations apply cleanly from scratch"
    - "Migrations can roll back without data loss"
    - "Migration tests run in CI before deployment"
  artifacts:
    - path: ".github/workflows/migration-tests.yml"
      provides: "CI job for migration validation"
      min_lines: 80
    - path: "scripts/test_migrations.py"
      provides: "Migration test script with forward/backward validation"
      min_lines: 100
  key_links:
    - from: ".github/workflows/migration-tests.yml"
      to: "scripts/test_migrations.py"
      via: "python scripts/test_migrations.py"
      pattern: "python scripts/test_migrations\\.py"
    - from: "scripts/test_migrations.py"
      to: "manage.py migrate"
      via: "subprocess calls"
      pattern: "subprocess.*manage\\.py migrate"
---

<objective>
Add automated migration testing to CI pipeline to validate forward/backward migration safety before deployment.

Purpose: Prevent migration failures in production by testing all migrations in isolated PostgreSQL environment with rollback validation.

Output: CI job that runs on every PR, catches migration issues early, validates data integrity through migration cycles.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@.github/workflows/ci.yml
@upstream/migrations/
</context>

<tasks>

<task type="auto">
  <name>Create migration test script</name>
  <files>scripts/test_migrations.py</files>
  <action>
    Create Python script that validates Django migrations:

    **Forward migration testing:**
    - Start with empty database
    - Apply all migrations: `python manage.py migrate --noinput`
    - Verify no errors, all apps migrated
    - Run system checks: `python manage.py check --deploy`

    **Backward migration testing (rollback validation):**
    - Record current migration state for each app
    - For each app with migrations:
      - Roll back one migration: `python manage.py migrate {app} {previous_migration}`
      - Verify rollback succeeded (exit code 0)
      - Re-apply: `python manage.py migrate {app}`
      - Verify forward migration still works

    **Implementation details:**
    - Use subprocess.run() to execute Django management commands
    - Set environment: DJANGO_SETTINGS_MODULE=hello_world.settings
    - Parse `python manage.py showmigrations --plan` to get migration list
    - Test only the last 5 migrations per app (avoid testing entire history)
    - Exit with code 0 on success, 1 on any failure
    - Verbose output showing each migration being tested
    - Skip apps with no migrations (django.contrib.* may not roll back cleanly)

    **Why test only last 5:** Production deployments only care about recent migrations. Testing all 24 upstream migrations adds CI time without benefit. Focus on migrations that could actually be deployed.

    **Why skip contrib apps:** Django's built-in apps (auth, contenttypes, admin) have complex dependencies and don't always support rollback. Our upstream app migrations are what we control and must validate.
  </action>
  <verify>
    python scripts/test_migrations.py --help (shows usage)
  </verify>
  <done>
    Script exists, has forward/backward test logic, exits with proper codes
  </done>
</task>

<task type="auto">
  <name>Add CI migration testing job</name>
  <files>.github/workflows/migration-tests.yml</files>
  <action>
    Create GitHub Actions workflow for migration testing:

    **Job structure:**
    - Name: "migration-tests"
    - Trigger: on push/PR to main and develop branches
    - Run on: ubuntu-latest
    - Depends on: nothing (runs in parallel with other CI jobs)

    **PostgreSQL service:**
    - Use postgres:15 service container (matches production)
    - Health checks: pg_isready with retries
    - Ports: map 5432:5432
    - Env: POSTGRES_PASSWORD=postgres, POSTGRES_DB=migration_test_db

    **Steps:**
    1. Checkout code
    2. Set up Python 3.12 with pip cache
    3. Install system dependencies (libcairo2, libpango for WeasyPrint)
    4. Install Python dependencies from requirements.txt
    5. Set up environment:
       - Copy .env.example to .env
       - Set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/migration_test_db  # pragma: allowlist secret
       - Set SECRET_KEY (generate with openssl rand -hex 32)
       - Set DEBUG=True
    6. Run migration test script: `python scripts/test_migrations.py --verbose`
    7. On failure: Print PostgreSQL logs for debugging

    **Why separate workflow file:** Migration testing is distinct from unit tests. Isolating in separate workflow allows:
    - Independent failure tracking (migration issues vs test failures)
    - Parallel execution with test job (faster CI)
    - Different PostgreSQL setup (test job uses SQLite)

    **Why PostgreSQL required:** SQLite has different migration behavior (no ALTER COLUMN support, different constraint handling). Must test against production database engine.
  </action>
  <verify>
    cat .github/workflows/migration-tests.yml (shows PostgreSQL service, test script execution)
  </verify>
  <done>
    Workflow exists, uses PostgreSQL service, runs migration test script on push/PR
  </done>
</task>

<task type="auto">
  <name>Update CI configuration to require migration tests</name>
  <files>.github/workflows/ci.yml</files>
  <action>
    Add migration-tests as required check for PR merge:

    **At end of ci.yml, add new job:**
    ```yaml
    all-checks:
      runs-on: ubuntu-latest
      needs: [test, performance, backup-verification]
      if: always()
      steps:
        - name: Check all jobs passed
          run: |
            if [[ "${{ needs.test.result }}" != "success" ]] || \
               [[ "${{ needs.performance.result }}" != "success" ]] || \
               [[ "${{ needs.backup-verification.result }}" != "success" ]]; then
              echo "One or more required checks failed"
              exit 1
            fi
            echo "All checks passed"
    ```

    This creates a single status check that GitHub can require, aggregating test + performance + backup-verification.

    **Note:** GitHub Actions automatically runs migration-tests.yml in parallel when it exists. No explicit dependency needed in ci.yml. The all-checks job just aggregates the three existing jobs in ci.yml.

    **Why all-checks job:** GitHub branch protection works better with single required check than multiple. All-checks aggregates existing jobs into one green/red signal.
  </action>
  <verify>
    cat .github/workflows/ci.yml (shows all-checks job at end)
  </verify>
  <done>
    CI has all-checks job that aggregates test, performance, backup-verification results
  </done>
</task>

</tasks>

<verification>
Run migration test script locally to validate it works:
```bash
python scripts/test_migrations.py --verbose
```

Trigger CI by pushing to branch:
```bash
git add .
git commit -m "test: validate migration testing in CI"
git push
```

Check GitHub Actions UI:
- migration-tests job appears
- PostgreSQL service starts
- Migration tests run
- Job passes with green checkmark
</verification>

<success_criteria>
- [ ] scripts/test_migrations.py exists with forward/backward migration testing
- [ ] Script tests last 5 migrations per app (skips full history)
- [ ] Script skips Django contrib apps (focuses on upstream app)
- [ ] .github/workflows/migration-tests.yml exists with PostgreSQL service
- [ ] Migration workflow runs on push/PR to main and develop
- [ ] CI job runs migrations from scratch and validates rollback capability
- [ ] .github/workflows/ci.yml has all-checks job aggregating existing jobs
- [ ] Local test run succeeds: python scripts/test_migrations.py
</success_criteria>

<output>
After completion, create `.planning/quick/030-add-database-migration-testing-autom/030-SUMMARY.md`
</output>
