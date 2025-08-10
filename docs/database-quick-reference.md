# Database Quick Reference Guide

## 🚀 **Quick Commands**

### **Backup Database**
```bash
./scripts/database-backup.sh
```
**Output**: `backup/database/trading_db_backup_YYYYMMDD_HHMMSS.sql.gz`

### **Restore Database**
```bash
# List available backups
ls -lah backup/database/*.sql.gz

# Restore from specific backup
./scripts/database-restore.sh backup/database/trading_db_backup_20250808_065341.sql.gz

# Dry run (preview only)
./scripts/database-restore.sh --dry-run backup/database/trading_db_backup_20250808_065341.sql.gz

# Force restore (no confirmation)
./scripts/database-restore.sh --force backup/database/trading_db_backup_20250808_065341.sql.gz
```

### **Check Migration Status**
```bash
# Check current migration version
./scripts/database-migrate.sh current

# Check if migrations are up to date
./scripts/database-migrate.sh check

# Show migration history
./scripts/database-migrate.sh history
```

### **Run Migrations**
```bash
# Run all pending migrations
./scripts/database-migrate.sh upgrade

# Rollback to specific version
./scripts/database-migrate.sh downgrade 65a77fa65587

# Dry run migrations
./scripts/database-migrate.sh --dry-run upgrade
```

## 📊 **Database Status Commands**

### **Check Database Health**
```bash
# Check if database pod is running
kubectl get pods -n trading-system | grep timescaledb

# Check database logs
kubectl logs -n trading-system timescaledb-7968f6845d-nflhk

# Check database size
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT pg_size_pretty(pg_database_size('trading_bot'));"
```

### **Check Backup Status**
```bash
# List all backups
ls -lah backup/database/*.sql.gz

# Check backup age
find backup/database -name "*.sql.gz" -mtime +1 -exec ls -lah {} \;

# Check backup size
du -sh backup/database/
```

## 🚨 **Emergency Recovery**

### **Complete Database Loss**
```bash
# 1. Stop all applications
kubectl scale deployment --all -n trading-system --replicas=0

# 2. Restore from latest backup
./scripts/database-restore.sh backup/database/$(ls -t backup/database/*.sql.gz | head -1)

# 3. Restart applications
kubectl scale deployment --all -n trading-system --replicas=1
```

### **Schema Issues**
```bash
# 1. Check current migration status
./scripts/database-migrate.sh current

# 2. Run migrations
./scripts/database-migrate.sh upgrade

# 3. Verify database integrity
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT COUNT(*) FROM trades;"
```

### **Data Corruption**
```bash
# 1. Create backup before attempting recovery
./scripts/database-backup.sh

# 2. Identify corrupted data
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT * FROM trades WHERE id = 12345;"

# 3. Restore from clean backup
./scripts/database-restore.sh backup/database/trading_db_backup_20250808_065341.sql.gz
```

## 📋 **Monitoring Commands**

### **Check Backup Age**
```bash
# Find backups older than 24 hours
find backup/database -name "*.sql.gz" -mtime +1

# Check last backup time
ls -lah backup/database/*.sql.gz | tail -1
```

### **Check Database Size**
```bash
# Get database size
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### **Check Table Row Counts**
```bash
# Get row counts for all tables
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC;
"
```

## 🔧 **Troubleshooting**

### **Backup Issues**
```bash
# Check if database pod is accessible
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- pg_isready -U trading_user -d trading_bot

# Test database connection
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT 1;"
```

### **Restore Issues**
```bash
# Check backup file integrity
gunzip -t backup/database/trading_db_backup_20250808_065341.sql.gz

# Check backup file content
gunzip -c backup/database/trading_db_backup_20250808_065341.sql.gz | head -20
```

### **Migration Issues**
```bash
# Check alembic version table
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT * FROM alembic_version;"

# Check for migration conflicts
kubectl exec -n trading-system timescaledb-7968f6845d-nflhk -- psql -U trading_user -d trading_bot -c "SELECT * FROM information_schema.tables WHERE table_name LIKE '%alembic%';"
```

## 📝 **Log Files**

### **Backup Logs**
- **Location**: `backup/database/backup_manifest_YYYYMMDD_HHMMSS.json`
- **Content**: Backup metadata, file size, timestamp

### **Restore Logs**
- **Location**: `backup/restore_log_YYYYMMDD_HHMMSS.log`
- **Content**: Restore process details, errors, timestamps

### **Migration Logs**
- **Location**: `backup/migration_log_YYYYMMDD_HHMMSS.log`
- **Content**: Migration commands, status, errors

## ⚡ **Quick Recovery Checklist**

### **Before Recovery:**
- [ ] Check database pod status
- [ ] Verify backup file exists and is valid
- [ ] Stop all applications
- [ ] Create emergency backup if needed

### **During Recovery:**
- [ ] Run restore/migration command
- [ ] Monitor logs for errors
- [ ] Verify database connectivity
- [ ] Check data integrity

### **After Recovery:**
- [ ] Restart applications
- [ ] Verify all services are running
- [ ] Test critical functionality
- [ ] Update documentation

---

**Last Updated**: 2025-08-08  
**Version**: 1.0  
**Status**: ✅ ACTIVE


