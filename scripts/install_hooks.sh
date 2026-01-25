#!/bin/bash
# Install pre-commit hooks for Upstream agents

set -e

echo "🔧 Installing Upstream Pre-Commit Hooks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Check if in git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Install pre-commit hooks
echo "⚙️  Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Create agent models migration if needed
echo "⚙️  Checking agent models migration..."
if [ ! -f upstream/migrations/*_agent_models.py ]; then
    echo "📝 Creating agent models migration..."
    python manage.py makemigrations --name agent_models
fi

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "Installed agents:"
echo "  1. Code Quality Auditor (runs on commit)"
echo "  2. Database Performance Optimizer (manual only)"
echo "  3. Test Coverage Analyzer (runs on commit, warns only)"
echo "  4. Migration Safety Checker (runs on commit if migrations detected)"
echo "  5. HIPAA Compliance Monitor (runs on push)"
echo ""
echo "Usage:"
echo "  • git commit    - Triggers agents 1, 3, 4"
echo "  • git push      - Triggers agent 5"
echo "  • Bypass hooks  - git commit --no-verify (use sparingly!)"
echo ""
echo "Manual commands:"
echo "  • python manage.py audit_code_quality"
echo "  • python manage.py optimize_database"
echo "  • python manage.py analyze_test_coverage"
echo "  • python manage.py check_migrations"
echo "  • python manage.py check_hipaa_compliance"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
