# Database Backup & Restore Guide

Complete guide for backing up and restoring trading databases.

## Overview

The trading platform uses **two PostgreSQL databases** in the `postgres-infra` namespace:

1. **`trading`** (postgres-vector) - Primary trading database with vector storage (7.6 MB)
2. **`trading_bot`** (postgres-timescale) - TimescaleDB with time-series data (62 MB)

## Quick Reference

```bash
# Backup all databases (recommended)
make db-backup-all

# Restore a database (smart detection)
make db-restore BACKUP=backups/database/trading_vector_20241008_063136.sql.gz

# List all backups
make db-list-backups

# Show database status
make db-status-all
```

## Backup Operations

### 1. Backup All Databases (Recommended)

```bash
make db-backup-all
```

This creates backups of both:
- `trading_vector_YYYYMMDD_HHMMSS.sql.gz` (postgres-vector)
- `trading_bot_timescale_YYYYMMDD_HHMMSS.sql.gz` (postgres-timescale)

### 2. Backup Individual Databases

```bash
# Backup trading database (postgres-vector)
make db-backup

# Backup trading_bot database (postgres-timescale)
make db-backup-timescale

# Backup schema only (no data)
make db-backup-schema
```

### 3. List Backups

```bash
make db-list-backups
```

Shows:
- All full backups with timestamps
- Schema-only backups
- Total backup directory size

## Restore Operations

### Smart Restore (Auto-Detects Database)

```bash
make db-restore BACKUP=backups/database/trading_vector_20241008_063136.sql.gz
```

The system automatically detects which database to restore to based on the filename:
- Files with `vector` → restores to `trading` database
- Files with `timescale` → restores to `trading_bot` database

### Manual Restore (Specific Database)

If you want to explicitly choose the target database:

```bash
# Restore to trading database (postgres-vector)
make db-restore-vector BACKUP=backups/database/trading_vector_20241008_063136.sql.gz

# Restore to trading_bot database (postgres-timescale)
make db-restore-timescale BACKUP=backups/database/trading_bot_timescale_20241008_063137.sql.gz
```

### Safety Features

All restore operations require confirmation:
```
⚠️  WARNING: Database Restore
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This will OVERWRITE the trading database!
Database: trading (postgres-vector)
Backup: backups/database/trading_vector_20241008_063136.sql.gz
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Type 'yes' to confirm:
```

## Database Access

### Open Database Shell

```bash
# Trading database (postgres-vector)
make db-shell

# Trading_bot database (postgres-timescale)
make db-shell-timescale
```

Once in the shell, you can run SQL commands:
```sql
-- View tables
\dt

-- View table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Exit shell
\q
```

## Monitoring

### Database Status

```bash
# Show all databases
make db-status-all

# Show specific database status
make db-status
```

Output shows:
- Pod names
- Database sizes
- Active connections
- Recent backups

### Check Backup Files

```bash
# List all backups
ls -lh backups/database/

# View backup details
gunzip -c backups/database/trading_vector_20241008_063136.sql.gz | head -20
```

## Maintenance

### Clean Old Backups

```bash
# Remove backups older than 30 days
make db-clean-old-backups
```

This automatically removes:
- Full backups older than 30 days
- Schema backups older than 30 days
- Keeps recent backups safe

### Manual Cleanup

```bash
# View old backups
find backups/database/ -name "*.sql.gz" -mtime +7

# Remove specific backup
rm backups/database/old_backup_20240101_120000.sql.gz
```

## Backup Schedule Recommendations

### Development
- **Weekly backups** before major changes
- Keep last 4 backups (1 month)

### Production
- **Daily backups** (automate with cron)
- Keep last 30 backups (1 month)
- Monthly backups kept for 1 year

### Critical Changes
- **Backup before**: Migrations, schema changes, major deployments
- **Backup after**: Successful migrations (for rollback point)

## Disaster Recovery

### Scenario 1: Corrupted Database

```bash
# 1. Check current status
make db-status-all

# 2. List recent backups
make db-list-backups

# 3. Restore from most recent backup
make db-restore BACKUP=backups/database/trading_vector_20241008_063136.sql.gz
```

### Scenario 2: Failed Migration

```bash
# 1. Identify backup before migration
ls -lt backups/database/

# 2. Restore pre-migration state
make db-restore-timescale BACKUP=backups/database/trading_bot_timescale_20241007_120000.sql.gz

# 3. Verify restoration
make db-status-all
```

### Scenario 3: Need to Copy Production to Development

```bash
# 1. Create production backup
make db-backup-all

# 2. Download backup (if needed)
scp server:/path/backups/database/trading_*.sql.gz backups/database/

# 3. Restore to development database
make db-restore BACKUP=backups/database/trading_vector_prod.sql.gz
```

## Automated Backups

### Add to Cron (Recommended)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /Users/abby/code/trading && make db-backup-all >> logs/db-backup.log 2>&1
```

### Kubernetes CronJob (Production)

Create `k8s/database-backup-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: postgres-infra
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -U postgres -h postgres-vector trading | gzip > /backups/trading_vector_$(date +%Y%m%d_%H%M%S).sql.gz
              pg_dump -U postgres -h postgres-timescale trading_bot | gzip > /backups/trading_bot_$(date +%Y%m%d_%H%M%S).sql.gz
              # Clean old backups
              find /backups -name "*.sql.gz" -mtime +30 -delete
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

## Testing Backups

### Verify Backup Integrity

```bash
# 1. Create test backup
make db-backup

# 2. Check file is not empty
ls -lh backups/database/trading_vector_*.sql.gz

# 3. View backup contents (first 20 lines)
gunzip -c backups/database/trading_vector_*.sql.gz | head -20

# 4. Verify SQL is valid
gunzip -c backups/database/trading_vector_*.sql.gz | grep -c "CREATE TABLE"
```

### Test Restore (Safe Method)

**Option 1**: Restore to test database

```bash
# 1. Create test database
kubectl exec -n postgres-infra <pod> -- psql -U postgres -c "CREATE DATABASE trading_test;"

# 2. Modify backup to restore to test database
gunzip -c backups/database/trading_vector_20241008_063136.sql.gz | \
  kubectl exec -i -n postgres-infra <pod> -- psql -U postgres trading_test

# 3. Verify data
kubectl exec -n postgres-infra <pod> -- psql -U postgres trading_test -c "\dt"

# 4. Drop test database
kubectl exec -n postgres-infra <pod> -- psql -U postgres -c "DROP DATABASE trading_test;"
```

**Option 2**: Test in separate environment

```bash
# Restore to local PostgreSQL for testing
gunzip -c backups/database/trading_vector_20241008_063136.sql.gz | \
  psql -U postgres -h localhost trading_test
```

## Troubleshooting

### Error: Pod Not Found

```bash
# Check if pods are running
kubectl get pods -n postgres-infra | grep postgres

# Verify pod labels
kubectl get pods -n postgres-infra -l app=postgres-vector
kubectl get pods -n postgres-infra -l app=postgres-timescale
```

### Error: Permission Denied

```bash
# Ensure using postgres user (superuser)
# All commands use: -U postgres

# Check user permissions
kubectl exec -n postgres-infra <pod> -- psql -U postgres -c "\du"
```

### Error: Backup File Corrupted

```bash
# Test gzip integrity
gunzip -t backups/database/trading_vector_20241008_063136.sql.gz

# If corrupted, use a different backup
make db-list-backups
```

### Restore Fails Midway

```bash
# The restore process is transactional for most operations
# Check database state
make db-status-all

# If needed, try restoring from a different backup
make db-list-backups
make db-restore BACKUP=<earlier_backup>
```

## Best Practices

### Before Major Changes

```bash
# 1. Create backup
make db-backup-all

# 2. Verify backup created
make db-list-backups

# 3. Make your changes

# 4. If something goes wrong, restore
make db-restore BACKUP=backups/database/trading_vector_YYYYMMDD_HHMMSS.sql.gz
```

### Regular Maintenance

```bash
# Weekly: Check backup status
make db-status-all
make db-list-backups

# Monthly: Clean old backups
make db-clean-old-backups

# Quarterly: Test restore procedure
```

### Backup Rotation

Keep:
- **Last 7 daily backups** (1 week)
- **Last 4 weekly backups** (1 month)
- **Last 12 monthly backups** (1 year)

## File Naming Convention

Backups use descriptive timestamps:
```
trading_vector_YYYYMMDD_HHMMSS.sql.gz
trading_bot_timescale_YYYYMMDD_HHMMSS.sql.gz
schema_backup_YYYYMMDD_HHMMSS.sql
```

Example:
```
trading_vector_20241008_063136.sql.gz
trading_bot_timescale_20241008_063137.sql.gz
```

## Storage Locations

| File | Location | Purpose |
|------|----------|---------|
| Full backups | `backups/database/*.sql.gz` | Complete database dumps |
| Schema backups | `backups/database/schema_*.sql` | Schema-only (no data) |
| Root compatibility | `schema_backup.dump` | Symlink to latest schema |
| Old backups | `archive/backup-*/database/` | Historical backups |

## Advanced Operations

### Export Specific Tables

```bash
# Backup specific tables only
kubectl exec -n postgres-infra postgres-vector-... -- \
  pg_dump -U postgres -t trades -t orders trading | gzip > specific_tables.sql.gz
```

### Backup with Custom Options

```bash
# Backup with inserts instead of COPY
kubectl exec -n postgres-infra postgres-vector-... -- \
  pg_dump -U postgres --column-inserts trading | gzip > backup_inserts.sql.gz

# Backup excluding specific tables
kubectl exec -n postgres-infra postgres-vector-... -- \
  pg_dump -U postgres --exclude-table=logs trading | gzip > backup_no_logs.sql.gz
```

### Restore to Different Database Name

```bash
# Create new database
kubectl exec -n postgres-infra postgres-vector-... -- \
  psql -U postgres -c "CREATE DATABASE trading_copy;"

# Restore to new database
gunzip -c backups/database/trading_vector_20241008_063136.sql.gz | \
  kubectl exec -i -n postgres-infra postgres-vector-... -- \
  psql -U postgres trading_copy
```

## Security Considerations

### Backup Security

- ✅ Backups are stored locally (not transmitted)
- ✅ Contains sensitive trading data - protect accordingly
- ✅ Use encryption for remote storage
- ⚠️  Don't commit backups to git (already in .gitignore)

### Access Control

- Backups use `postgres` superuser (required for full dump)
- Only users with kubectl access can create/restore backups
- Consider restricting kubectl access to production

## Summary

**Backup**: Simple and automated
```bash
make db-backup-all  # Backs up everything
```

**Restore**: Safe with confirmation
```bash
make db-restore BACKUP=backups/database/trading_vector_20241008_063136.sql.gz
# Requires typing 'yes' to confirm
```

**Monitor**: Always know your status
```bash
make db-status-all  # Shows both databases
```

All backups are saved to `backups/database/` and automatically cleaned after 30 days.

