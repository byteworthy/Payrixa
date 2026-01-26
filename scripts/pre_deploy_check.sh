#!/bin/bash
#
# Pre-deployment validation script for Upstream
#
# This script runs comprehensive checks before deploying to production:
# - Monitoring configuration validation
# - Security checks
# - Database migrations
# - Static files collection
#
# Usage:
#   ./scripts/pre_deploy_check.sh
#
# Exit codes:
#   0: All checks passed
#   1: Critical checks failed
#   2: Warnings found (non-critical)
#
# Related: Phase 3 - DevOps Monitoring & Metrics (Task #5)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Upstream Pre-Deployment Checks${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Track overall status
ERRORS=0
WARNINGS=0

# Function to print section header
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "----------------------------------------"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# 1. Check Python environment
print_section "Python Environment"
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    print_success "Python: $PYTHON_VERSION"
else
    print_error "Python not found"
fi

# 2. Check required environment variables
print_section "Environment Variables"

# Production-critical variables
if [ -z "$SECRET_KEY" ]; then
    print_error "SECRET_KEY not set"
else
    print_success "SECRET_KEY configured"
fi

if [ -z "$ALLOWED_HOSTS" ]; then
    print_error "ALLOWED_HOSTS not set"
else
    print_success "ALLOWED_HOSTS: $ALLOWED_HOSTS"
fi

if [ -z "$PORTAL_BASE_URL" ]; then
    print_error "PORTAL_BASE_URL not set"
else
    print_success "PORTAL_BASE_URL: $PORTAL_BASE_URL"
fi

# Database
if [ -z "$DATABASE_URL" ]; then
    print_warning "DATABASE_URL not set (using individual DB_* variables)"
else
    print_success "DATABASE_URL configured"
fi

# Redis
if [ -z "$REDIS_URL" ]; then
    print_warning "REDIS_URL not set (using default: redis://localhost:6379)"
else
    print_success "REDIS_URL configured"
fi

# Monitoring (optional but recommended)
if [ -z "$SENTRY_DSN" ]; then
    print_warning "SENTRY_DSN not set (error tracking disabled)"
else
    print_success "SENTRY_DSN configured"
fi

# 3. Run Django system checks
print_section "Django System Checks"
if python manage.py check --deploy --fail-level ERROR 2>&1; then
    print_success "Django checks passed"
else
    print_error "Django checks failed"
fi

# 4. Validate monitoring configuration
print_section "Monitoring Configuration"
if python manage.py validate_monitoring 2>&1; then
    print_success "Monitoring configuration valid"
else
    print_error "Monitoring configuration invalid"
fi

# 5. Check database connectivity
print_section "Database Connectivity"
if python manage.py migrate --check 2>&1 | grep -q "No migrations to apply"; then
    print_success "Database migrations up to date"
elif python manage.py migrate --check 2>&1 | grep -q "unapplied migration"; then
    print_warning "Database migrations need to be applied"
else
    if python manage.py migrate --check 2>&1; then
        print_success "Database connection OK"
    else
        print_error "Cannot connect to database"
    fi
fi

# 6. Check static files
print_section "Static Files"
if [ -d "hello_world/staticfiles" ]; then
    FILE_COUNT=$(find hello_world/staticfiles -type f | wc -l)
    if [ $FILE_COUNT -gt 0 ]; then
        print_success "Static files collected ($FILE_COUNT files)"
    else
        print_warning "Static files directory empty - run collectstatic"
    fi
else
    print_warning "Static files not collected - run collectstatic"
fi

# 7. Check Celery configuration (if enabled)
print_section "Celery Background Jobs"
if [ "$CELERY_ENABLED" = "true" ]; then
    if python manage.py celery_health 2>&1 | grep -q "HEALTHY"; then
        print_success "Celery workers running"
    else
        print_warning "Celery workers not running (will start after deployment)"
    fi
else
    print_warning "Celery disabled (CELERY_ENABLED=false)"
fi

# 8. Test metrics endpoint
print_section "Metrics Endpoint"
if python -c "from upstream.metrics import alert_created; print('OK')" 2>&1 | grep -q "OK"; then
    print_success "Prometheus metrics available"
else
    print_error "Cannot import Prometheus metrics"
fi

# 9. Security checks
print_section "Security Configuration"
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ]; then
    print_error "DEBUG is enabled (must be False in production)"
else
    print_success "DEBUG disabled"
fi

if [ "$SECRET_KEY" = "django-insecure-dev-key-change-in-production" ]; then
    print_error "Using default SECRET_KEY (must be changed)"
else
    print_success "Custom SECRET_KEY configured"
fi

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Errors:   ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

# Exit with appropriate code
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ Pre-deployment checks FAILED${NC}"
    echo -e "Fix the errors above before deploying to production."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Pre-deployment checks passed with warnings${NC}"
    echo -e "Review the warnings above before deploying."
    exit 2
else
    echo -e "${GREEN}✓ All pre-deployment checks PASSED${NC}"
    echo -e "Ready to deploy to production."
    exit 0
fi
