#!/bin/bash

# K8S Files Cleanup Script
# This script helps clean up unnecessary k8s job files

set -e

K8S_DIR="k8s"
BACKUP_DIR="k8s/backup_$(date +%Y%m%d_%H%M%S)"

echo "=== K8S FILES CLEANUP SCRIPT ==="
echo "Current directory: $(pwd)"
echo "K8S directory: $K8S_DIR"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to safely move files to backup
move_to_backup() {
    local file="$1"
    local reason="$2"
    echo "Moving $file to backup (reason: $reason)"
    mv "$K8S_DIR/$file" "$BACKUP_DIR/"
}

# Function to safely delete files
delete_file() {
    local file="$1"
    local reason="$2"
    echo "Deleting $file (reason: $reason)"
    rm "$K8S_DIR/$file"
}

echo "=== STEP 1: REMOVING BACKUP FILES ==="
# Remove all .bak files (these are safe to delete)
for file in "$K8S_DIR"/*.bak; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        delete_file "$filename" "backup file"
    fi
done

echo ""
echo "=== STEP 2: REMOVING COMPLETED MIGRATION JOBS ==="
# These migration jobs are likely completed and can be removed
MIGRATION_JOBS_TO_REMOVE=(
    "apply-merge-migration-job.yaml"
    "apply-news-migration-job.yaml"
    "check-alembic-version-job.yaml"
    "check-migration-status-job.yaml"
    "fix-alembic-heads-job.yaml"
    "fix-alembic-version-column-job.yaml"
    "fix-llm-column-migration-job.yaml"
    "news-migration-job.yaml"
    "options-cache-migration-job.yaml"
    "show-migration-history-job.yaml"
    "stamp-migration-job.yaml"
)

for job in "${MIGRATION_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "completed migration job"
    fi
done

echo ""
echo "=== STEP 3: REMOVING TEST JOBS ==="
# These test jobs are likely one-time tests
TEST_JOBS_TO_REMOVE=(
    "test-alembic-final-job.yaml"
    "test-alembic-fixed-job.yaml"
    "test-alembic-job.yaml"
    "test-database-storage.yaml"
    "test-db-connection-job.yaml"
    "test-final-alembic-job.yaml"
    "test-historical-greeks-direct.yaml"
    "test-polygon-options-access.yaml"
)

for job in "${TEST_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "test job"
    fi
done

echo ""
echo "=== STEP 4: REMOVING ANALYSIS JOBS ==="
# These analysis jobs are likely one-time analysis
ANALYSIS_JOBS_TO_REMOVE=(
    "analyze-fixed-portfolio-performance.yaml"
    "analyze-portfolio-performance.yaml"
    "analyze-real-portfolio-performance.yaml"
)

for job in "${ANALYSIS_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "one-time analysis job"
    fi
done

echo ""
echo "=== STEP 5: REMOVING OLDER BACKTEST JOBS ==="
# These backtest jobs are likely outdated versions
OLD_BACKTEST_JOBS_TO_REMOVE=(
    "backtest-advanced-strategies.yaml"  # Keep the working/real-data versions
    "backtest-comprehensive-2year.yaml"  # Keep the enhanced version
    "backtest-comprehensive-historical.yaml"
    "backtest-scanner-2year.yaml"  # Keep the deployment version
    "backtest-scanner-alpha-vantage.yaml"
    "backtest-scanner-polygon-priority.yaml"
    "backtest-scanner-recent.yaml"
    "backtest-scanner-single.yaml"
    "backtest-scanner-sequential.yaml"
    "backtest-scanner-job.yaml"  # Keep the deployment version
)

for job in "${OLD_BACKTEST_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "older backtest job version"
    fi
done

echo ""
echo "=== STEP 6: REMOVING ONE-TIME DATA POPULATION JOBS ==="
# These data population jobs are likely completed
DATA_JOBS_TO_REMOVE=(
    "populate-2year-data-full.yaml"
    "store-2year-data-job.yaml"
)

for job in "${DATA_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "completed data population job"
    fi
done

echo ""
echo "=== STEP 7: REMOVING OTHER ONE-TIME JOBS ==="
# These are likely one-time setup/debug jobs
OTHER_JOBS_TO_REMOVE=(
    "add-missing-symbols-job.yaml"
    "ai-strategies-demo-job.yaml"
    "data-ingestion-job.yaml"
    "db-setup-job.yaml"
    "debug-config-job.yaml"
    "inspect-schema-job.yaml"
    "llm-demo-job.yaml"
)

for job in "${OTHER_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "one-time setup/debug job"
    fi
done

echo ""
echo "=== STEP 8: REMOVING DUPLICATE DEPLOYMENTS ==="
# Remove duplicate/simple versions
DEPLOYMENT_JOBS_TO_REMOVE=(
    "rabbitmq-deployment-simple.yaml"  # Keep the workers version
)

for job in "${DEPLOYMENT_JOBS_TO_REMOVE[@]}"; do
    if [ -f "$K8S_DIR/$job" ]; then
        move_to_backup "$job" "duplicate deployment"
    fi
done

echo ""
echo "=== CLEANUP SUMMARY ==="
echo "Backup directory: $BACKUP_DIR"
echo "Files moved to backup: $(ls -1 "$BACKUP_DIR" | wc -l)"
echo "Files remaining in k8s: $(ls -1 "$K8S_DIR"/*.yaml 2>/dev/null | wc -l || echo 0)"

echo ""
echo "=== REMAINING FILES ==="
echo "These files are kept as they are likely still needed:"
echo ""

# Show remaining files by category
echo "CORE SERVICES:"
ls -1 "$K8S_DIR"/*service*.yaml 2>/dev/null || echo "  (none)"
echo ""

echo "DEPLOYMENTS:"
ls -1 "$K8S_DIR"/*deployment*.yaml 2>/dev/null || echo "  (none)"
echo ""

echo "ACTIVE BACKTEST JOBS:"
ls -1 "$K8S_DIR"/backtest-*.yaml 2>/dev/null | grep -v "scanner" || echo "  (none)"
echo ""

echo "SCANNER COMPONENTS:"
ls -1 "$K8S_DIR"/*scanner*.yaml 2>/dev/null || echo "  (none)"
echo ""

echo "STORAGE & INGRESS:"
ls -1 "$K8S_DIR"/*pvc*.yaml "$K8S_DIR"/ingress.yaml "$K8S_DIR"/secrets.yaml 2>/dev/null || echo "  (none)"
echo ""

echo "CRONJOBS:"
ls -1 "$K8S_DIR"/*cronjob*.yaml 2>/dev/null || echo "  (none)"
echo ""

echo "OTHER:"
ls -1 "$K8S_DIR"/*.yaml 2>/dev/null | grep -v -E "(service|deployment|backtest|scanner|pvc|ingress|secrets|cronjob)" || echo "  (none)"

echo ""
echo "=== NEXT STEPS ==="
echo "1. Review the backup directory: $BACKUP_DIR"
echo "2. If you're satisfied with the cleanup, you can delete the backup directory"
echo "3. If you need to restore any files, copy them from the backup directory"
echo ""
echo "To delete the backup directory: rm -rf $BACKUP_DIR" 