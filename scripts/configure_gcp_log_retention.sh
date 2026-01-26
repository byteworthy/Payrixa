#!/bin/bash
#
# GCP Cloud Logging Retention Configuration
#
# Configures HIPAA-compliant log retention policies for Google Cloud Logging
# including log buckets, sinks, and exclusion filters.
#
# Usage:
#   ./scripts/configure_gcp_log_retention.sh           # Apply configuration
#   ./scripts/configure_gcp_log_retention.sh --dry-run # Preview changes
#
# Environment Variables:
#   PROJECT_ID - GCP project ID (required)
#   LOCATION   - Log bucket location (default: global)
#
# Requirements:
#   - gcloud CLI installed
#   - Authenticated to GCP
#   - logging.admin IAM role
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
LOCATION="${LOCATION:-global}"
DRY_RUN=false

# Log retention periods (days)
APP_LOG_RETENTION=90
AUDIT_LOG_RETENTION=2555  # 7 years for HIPAA compliance

# Log bucket names
APP_BUCKET="upstream-app-logs"
AUDIT_BUCKET="upstream-audit-logs"

# Log sink names
APP_SINK="upstream-app-logs-sink"
AUDIT_SINK="upstream-audit-logs-sink"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat << EOF
GCP Cloud Logging Retention Configuration

Usage:
  $0 [options]

Options:
  --dry-run    Preview changes without applying
  --help, -h   Show this help message

Environment Variables:
  PROJECT_ID   GCP project ID (required)
  LOCATION     Log bucket location (default: global)

Example:
  export PROJECT_ID=my-project
  $0 --dry-run

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Prerequisites check
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not installed"
        echo "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # Check PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID environment variable not set"
        echo "Export it: export PROJECT_ID=your-project-id"
        exit 1
    fi

    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "Not authenticated to GCP"
        echo "Run: gcloud auth login"
        exit 1
    fi

    # Verify project exists
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Project '$PROJECT_ID' not found or not accessible"
        exit 1
    fi

    # Check IAM permissions
    local current_user
    current_user=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log_info "Authenticated as: $current_user"

    # Set project
    gcloud config set project "$PROJECT_ID" --quiet

    log_success "Prerequisites OK"
}

# Enable Cloud Logging API
enable_logging_api() {
    log_info "Enabling Cloud Logging API..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would enable logging.googleapis.com"
        return
    fi

    if gcloud services list --enabled --filter="name:logging.googleapis.com" --format="value(name)" | grep -q logging.googleapis.com; then
        log_info "Cloud Logging API already enabled"
    else
        gcloud services enable logging.googleapis.com
        log_success "Cloud Logging API enabled"
    fi
}

# Create log bucket with retention policy
create_log_bucket() {
    local bucket_name=$1
    local retention_days=$2
    local description=$3

    log_info "Creating log bucket: $bucket_name (${retention_days}-day retention)..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would create bucket: $bucket_name"
        log_info "[DRY RUN]   Location: $LOCATION"
        log_info "[DRY RUN]   Retention: $retention_days days"
        log_info "[DRY RUN]   Description: $description"
        return
    fi

    # Check if bucket exists
    if gcloud logging buckets describe "$bucket_name" --location="$LOCATION" &> /dev/null; then
        log_warning "Bucket '$bucket_name' already exists, updating retention..."
        gcloud logging buckets update "$bucket_name" \
            --location="$LOCATION" \
            --retention-days="$retention_days" \
            --description="$description"
        log_success "Updated bucket: $bucket_name"
    else
        gcloud logging buckets create "$bucket_name" \
            --location="$LOCATION" \
            --retention-days="$retention_days" \
            --description="$description" \
            --locked=false
        log_success "Created bucket: $bucket_name"
    fi
}

# Create log sink to route logs to bucket
create_log_sink() {
    local sink_name=$1
    local bucket_name=$2
    local filter=$3

    log_info "Creating log sink: $sink_name..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would create sink: $sink_name"
        log_info "[DRY RUN]   Destination: logging.googleapis.com/projects/$PROJECT_ID/locations/$LOCATION/buckets/$bucket_name"
        log_info "[DRY RUN]   Filter: $filter"
        return
    fi

    local destination="logging.googleapis.com/projects/$PROJECT_ID/locations/$LOCATION/buckets/$bucket_name"

    # Check if sink exists
    if gcloud logging sinks describe "$sink_name" &> /dev/null; then
        log_warning "Sink '$sink_name' already exists, updating..."
        gcloud logging sinks update "$sink_name" \
            "$destination" \
            --log-filter="$filter"
        log_success "Updated sink: $sink_name"
    else
        gcloud logging sinks create "$sink_name" \
            "$destination" \
            --log-filter="$filter"
        log_success "Created sink: $sink_name"
    fi
}

# Create exclusion filter to reduce costs
create_exclusion_filter() {
    local name=$1
    local description=$2
    local filter=$3

    log_info "Creating exclusion filter: $name..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would create exclusion: $name"
        log_info "[DRY RUN]   Filter: $filter"
        return
    fi

    # Check if exclusion exists
    if gcloud logging exclusions describe "$name" &> /dev/null; then
        log_warning "Exclusion '$name' already exists, updating..."
        gcloud logging exclusions update "$name" \
            --description="$description" \
            --log-filter="$filter"
        log_success "Updated exclusion: $name"
    else
        gcloud logging exclusions create "$name" \
            --description="$description" \
            --log-filter="$filter"
        log_success "Created exclusion: $name"
    fi
}

# Verify configuration
verify_configuration() {
    log_info "Verifying configuration..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would verify bucket and sink configuration"
        return
    fi

    # List buckets
    log_info "Log buckets in project $PROJECT_ID:"
    gcloud logging buckets list --location="$LOCATION" \
        --format="table(name,retentionDays,description)"

    # List sinks
    log_info "Log sinks in project $PROJECT_ID:"
    gcloud logging sinks list \
        --format="table(name,destination,filter)"

    # List exclusions
    log_info "Log exclusions in project $PROJECT_ID:"
    gcloud logging exclusions list \
        --format="table(name,description,filter)" || log_info "No exclusions configured"

    log_success "Configuration verified"
}

# Calculate estimated monthly cost
calculate_cost() {
    log_info "Estimating monthly costs..."

    # GCP Cloud Logging pricing (as of 2024):
    # - Ingestion: $0.50/GB after 50GB/month free tier
    # - Storage: $0.01/GB/month

    # Estimated log volumes (conservative):
    local app_logs_gb_month=10  # Application logs
    local audit_logs_gb_month=2  # Audit logs (less frequent)

    # Calculate storage costs
    local app_storage_gb=$(echo "scale=2; $app_logs_gb_month * ($APP_LOG_RETENTION / 30)" | bc)
    local audit_storage_gb=$(echo "scale=2; $audit_logs_gb_month * ($AUDIT_LOG_RETENTION / 30)" | bc)
    local total_storage_gb=$(echo "scale=2; $app_storage_gb + $audit_storage_gb" | bc)

    # Calculate monthly costs
    local ingestion_cost=$(echo "scale=2; ($app_logs_gb_month + $audit_logs_gb_month - 50) * 0.50" | bc)
    if (( $(echo "$ingestion_cost < 0" | bc -l) )); then
        ingestion_cost=0
    fi

    local storage_cost=$(echo "scale=2; $total_storage_gb * 0.01" | bc)
    local total_cost=$(echo "scale=2; $ingestion_cost + $storage_cost" | bc)

    echo ""
    echo "========================================="
    echo "Estimated Monthly Costs"
    echo "========================================="
    echo "Assumptions:"
    echo "  - Application logs: ${app_logs_gb_month}GB/month"
    echo "  - Audit logs: ${audit_logs_gb_month}GB/month"
    echo ""
    echo "Storage:"
    echo "  - App logs (${APP_LOG_RETENTION} days): ${app_storage_gb}GB"
    echo "  - Audit logs (${AUDIT_LOG_RETENTION} days): ${audit_storage_gb}GB"
    echo "  - Total storage: ${total_storage_gb}GB"
    echo ""
    echo "Costs:"
    echo "  - Ingestion: \$${ingestion_cost}/month"
    echo "  - Storage: \$${storage_cost}/month"
    echo "  - Total: \$${total_cost}/month"
    echo ""
    echo "Note: Actual costs depend on log volume"
    echo "========================================="
}

# Main execution
main() {
    echo "========================================="
    echo "GCP Log Retention Configuration"
    echo "========================================="
    echo "Project: $PROJECT_ID"
    echo "Location: $LOCATION"
    echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "APPLY")"
    echo "========================================="
    echo ""

    check_prerequisites
    enable_logging_api

    echo ""
    log_info "Configuring log buckets..."
    echo ""

    # Create application logs bucket (90-day retention)
    create_log_bucket \
        "$APP_BUCKET" \
        "$APP_LOG_RETENTION" \
        "Application logs with 90-day retention for operational troubleshooting"

    # Create audit logs bucket (7-year retention for HIPAA)
    create_log_bucket \
        "$AUDIT_BUCKET" \
        "$AUDIT_LOG_RETENTION" \
        "Audit logs with 7-year retention for HIPAA compliance"

    echo ""
    log_info "Configuring log sinks..."
    echo ""

    # Create sink for application logs
    # Routes INFO/WARNING/ERROR logs from upstream.* loggers
    create_log_sink \
        "$APP_SINK" \
        "$APP_BUCKET" \
        'jsonPayload.logger=~"upstream.*" AND severity>=INFO'

    # Create sink for audit logs
    # Routes all audit trail logs
    create_log_sink \
        "$AUDIT_SINK" \
        "$AUDIT_BUCKET" \
        'jsonPayload.logger="auditlog" OR jsonPayload.audit=true'

    echo ""
    log_info "Configuring exclusion filters..."
    echo ""

    # Exclude DEBUG logs in production (reduce costs)
    create_exclusion_filter \
        "exclude-debug-logs" \
        "Exclude DEBUG logs to reduce ingestion costs" \
        'severity=DEBUG'

    # Exclude health check pings from load balancer
    create_exclusion_filter \
        "exclude-health-checks" \
        "Exclude health check requests from load balancer" \
        'httpRequest.requestUrl=~"/health/" AND httpRequest.userAgent=~"GoogleHC"'

    # Exclude static file requests (already captured by CDN)
    create_exclusion_filter \
        "exclude-static-files" \
        "Exclude static file requests already logged by CDN" \
        'httpRequest.requestUrl=~"/static/"'

    echo ""
    verify_configuration

    if [ "$DRY_RUN" = false ]; then
        echo ""
        calculate_cost
    fi

    echo ""
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN complete - no changes applied"
        log_info "Run without --dry-run to apply configuration"
    else
        log_success "Configuration complete!"
        echo ""
        echo "Next steps:"
        echo "  1. Deploy application with Cloud Logging enabled"
        echo "  2. Verify logs appearing: gcloud logging read --limit=10"
        echo "  3. Monitor costs: https://console.cloud.google.com/logs/usage"
    fi
}

# Run main function
main
