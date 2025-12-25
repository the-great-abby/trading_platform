# 🗄️ External Database Migration Guide

## 🎯 **Overview**

This guide walks you through migrating your trading system from the current TimescaleDB to new external databases:

- **TimescaleDB External**: Core trading data, market data, backtesting
- **Vector Storage External**: AI/ML data, vector embeddings, semantic search
- **Apache AGE External**: Graph analytics, relationship mapping
- **Regular PostgreSQL External**: Configuration, metadata, reference data

**All databases will use the unified name "trading" for easier management.**

## 🚀 **Quick Start**

### **1. Set Up Virtual Environment (First Time Only)**

```bash
# Create and activate virtual environment with dependencies
./scripts/activate-migration-env.sh

# Or use the wrapper script (recommended)
./run-migration.sh --help
```

### **2. Test Your Setup (Recommended First Step)**

```bash
# Test database connections without making changes
./run-migration.sh --dry-run migrate-all
```

### **3. Execute Complete Migration**

```bash
# Run the complete migration process
./run-migration.sh migrate-all
```

### **4. Execute Migration Phase by Phase**

```bash
# Set up external databases first
./run-migration.sh migrate-phase setup-external-databases

# Then migrate data
./run-migration.sh migrate-phase data-migration

# Continue with other phases...
```

## 📋 **Migration Phases**

### **Phase 1: Pre-migration Backup** ⚠️ **CRITICAL**
- Creates full database backup
- Backs up all service configurations
- **Never skip this phase!**

### **Phase 2: Setup External Databases**
- Creates new databases on external servers
- Sets up required extensions (TimescaleDB, pgvector, Apache AGE)
- Creates optimized table schemas

### **Phase 3: Data Migration**
- Migrates data from current database to external databases
- Preserves all data integrity
- Handles large datasets in batches

### **Phase 4: Service Configuration Update**
- Updates Kubernetes ConfigMaps
- Updates service environment variables
- Creates backup of old configurations

### **Phase 5: Service Restart**
- Applies updated configurations
- Restarts services with new database connections
- Monitors service health

### **Phase 6: Validation**
- Verifies data migration success
- Tests service connectivity
- Validates functionality

### **Phase 7: Post-migration Cleanup**
- Archives old configurations
- Creates migration completion summary
- Prepares for production use

## 🐍 **Virtual Environment Setup**

### **Why Virtual Environment?**
- **Isolated Dependencies**: Prevents conflicts with system Python packages
- **Reproducible Environment**: Ensures consistent behavior across different machines
- **Easy Cleanup**: Can be easily removed if needed
- **Dependency Management**: All required packages are installed automatically

### **Virtual Environment Files**
- **`migration-env/`**: Python virtual environment directory
- **`config/requirements/migration-requirements.txt`**: Required Python packages
- **`scripts/activate-migration-env.sh`**: Manual activation script
- **`run/run-migration.sh`**: Automatic wrapper script (recommended)

### **First Time Setup**
```bash
# Option 1: Use wrapper script (recommended)
./run-migration.sh --help

# Option 2: Manual setup
./scripts/activate-migration-env.sh
```

## 🛠️ **Available Scripts**

### **Main Migration Scripts**

#### **`run-migration.sh`** - **Main Wrapper (Recommended)**
```bash
# Complete migration (automatically activates virtual environment)
./run-migration.sh migrate-all

# Specific phase
./run-migration.sh migrate-phase data-migration

# Check status
./run-migration.sh status

# Rollback if needed
./run-migration.sh rollback
```

#### **`execute-migration.sh`** - **Direct Script (Advanced Users)**
```bash
# Requires manual virtual environment activation first
source migration-env/bin/activate
./scripts/execute-migration.sh migrate-all
```

#### **`setup-external-databases.sh`** - **Database Setup**
```bash
# Set up all external databases
./scripts/setup-external-databases.sh setup-all

# Set up specific database type
./scripts/setup-external-databases.sh setup-timescale

# Test connections
./scripts/setup-external-databases.sh validate
```

#### **`migrate-data-to-external.py`** - **Data Migration**
```bash
# Test connections only
python3 ./scripts/migrate-data-to-external.py --test-connections

# Dry run (see what would be migrated)
python3 ./scripts/migrate-data-to-external.py --dry-run

# Create tables only
python3 ./scripts/migrate-data-to-external.py --create-tables-only

# Full migration
python3 ./scripts/migrate-data-to-external.py

# Validate existing migration
python3 ./scripts/migrate-data-to-external.py --validate-only
```

#### **`update-service-configs.py`** - **Service Updates**
```bash
# Dry run (see what would be changed)
python3 ./scripts/update-service-configs.py --dry-run

# Create backup only
python3 ./scripts/update-service-configs.py --backup-only

# Update all configurations
python3 ./scripts/update-service-configs.py

# Generate kubectl commands
python3 ./scripts/update-service-configs.py --generate-commands
```

## 🔍 **Monitoring & Troubleshooting**

### **Check Migration Status**
```bash
# Overall status
./scripts/execute-migration.sh status

# Service health
make -f Makefile.simple status

# Kubernetes status
kubectl get pods -n trading-system
```

### **View Logs**
```bash
# Migration execution logs
tail -f logs/migration-execution_*.log

# Database setup logs
tail -f logs/external-db-setup_*.log

# Data migration logs
tail -f logs/data-migration_*.log

# Service config update logs
tail -f logs/service-config-update_*.log
```

### **Common Issues & Solutions**

#### **Database Connection Failures**
```bash
# Test external database connectivity
./scripts/setup-external-databases.sh validate

# Check if external databases are running
kubectl get pods -n postgres-infra
```

#### **Migration Failures**
```bash
# Check migration state
./scripts/execute-migration.sh status

# Resume from specific phase
./scripts/execute-migration.sh migrate-phase data-migration

# Force continue (use with caution)
./scripts/execute-migration.sh --force migrate-all
```

#### **Service Issues After Migration**
```bash
# Check service configurations
kubectl describe configmap trading-config -n trading-system

# Restart specific service
kubectl rollout restart deployment/unified-analytics-dashboard -n trading-system

# View service logs
kubectl logs deployment/unified-analytics-dashboard -n trading-system
```

## 🔄 **Rollback Procedures**

### **Emergency Rollback**
```bash
# Quick rollback
./scripts/execute-migration.sh rollback

# Manual rollback (if script fails)
# 1. Restore service configurations from backup
# 2. Restart services
kubectl rollout restart deployment -n trading-system
```

### **Partial Rollback**
```bash
# Rollback specific services
kubectl apply -f backup/service-configs-*/unified-analytics-dashboard.yaml.backup
kubectl rollout restart deployment/unified-analytics-dashboard -n trading-system
```

## 📊 **Migration Timeline**

### **Estimated Duration**
- **Setup & Backup**: 15-30 minutes
- **Data Migration**: 1-4 hours (depends on data size)
- **Service Updates**: 30-60 minutes
- **Validation**: 15-30 minutes
- **Total**: 2-6 hours

### **Critical Checkpoints**
1. **After Phase 2**: Verify external databases are accessible
2. **After Phase 3**: Validate data integrity
3. **After Phase 5**: Confirm services are healthy
4. **After Phase 6**: Final validation before cleanup

## 🚨 **Safety Measures**

### **Before Starting**
- ✅ Ensure you have sufficient disk space for backups
- ✅ Verify external database servers are accessible
- ✅ Confirm you have admin access to Kubernetes cluster
- ✅ Schedule migration during low-traffic period

### **During Migration**
- ✅ Monitor logs continuously
- ✅ Don't interrupt running processes
- ✅ Keep backup of current state
- ✅ Test functionality after each phase

### **After Migration**
- ✅ Monitor service performance
- ✅ Verify all dashboards are working
- ✅ Check data integrity
- ✅ Update monitoring configurations

## 📞 **Support & Troubleshooting**

### **If Migration Fails**
1. **Don't panic** - All data is backed up
2. **Check logs** - Look for specific error messages
3. **Use rollback** - Return to previous working state
4. **Investigate** - Fix the issue and retry

### **Getting Help**
- Check the logs in `logs/` directory
- Review this guide for common solutions
- Use `--dry-run` to test without making changes
- Execute phases individually to isolate issues

## 🎉 **Success Criteria**

### **Migration is Successful When**
- ✅ All external databases are accessible
- ✅ All data has been migrated successfully
- ✅ All services are running with new configurations
- ✅ All dashboards are displaying data correctly
- ✅ Performance is maintained or improved
- ✅ No data loss or corruption

### **Next Steps After Success**
1. Monitor system performance for 24-48 hours
2. Update monitoring and alerting configurations
3. Consider removing old database deployments
4. Update documentation and runbooks
5. Plan future database maintenance procedures

---

## 🚀 **Ready to Start?**

```bash
# 1. Set up virtual environment (first time only)
./run-migration.sh --help

# 2. Test your setup first
./run-migration.sh --dry-run migrate-all

# 3. If everything looks good, start the migration
./run-migration.sh migrate-all

# 4. Monitor progress
./run-migration.sh status
```

**Good luck with your migration! 🎯**
