#!/bin/bash
# Run all Upstream agents manually

set -e

echo "🤖 Running All Upstream Agents"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Agent 1: Code Quality Auditor
echo "1️⃣  Code Quality Auditor"
python manage.py audit_code_quality --fail-on critical || { echo "❌ Failed"; exit 1; }
echo ""

# Agent 2: Database Performance Optimizer
echo "2️⃣  Database Performance Optimizer"
python manage.py optimize_database || { echo "❌ Failed"; exit 1; }
echo ""

# Agent 3: Test Coverage Analyzer
echo "3️⃣  Test Coverage Analyzer"
python manage.py analyze_test_coverage --min-coverage 70 || { echo "⚠️  Coverage below threshold"; }
echo ""

# Agent 4: Migration Safety Checker
echo "4️⃣  Migration Safety Checker"
python manage.py check_migrations || { echo "❌ Failed"; exit 1; }
echo ""

# Agent 5: HIPAA Compliance Monitor
echo "5️⃣  HIPAA Compliance Monitor"
python manage.py check_hipaa_compliance --fail-on critical || { echo "❌ Failed"; exit 1; }
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All agents completed successfully!"
echo ""
echo "📊 View detailed results:"
echo "   • Database: Query AgentRun and Finding models"
echo "   • Web: Visit /portal/admin/agents/"
echo ""
