# 🗄️ Database Migration Plan: Current → External Databases

## 📊 **Current Database State**

### **Source Database**: `timescaledb.trading-system.svc.cluster.local:5432`
- **Database**: `trading_bot`
- **User**: `trading_user`
- **Tables**: 26 tables (trading, backtesting, news, options, vectors)

## 🎯 **Target External Databases**

### 1. **TimescaleDB External** (`localhost:11150/trading`)
- **Purpose**: Core trading data, market data, backtesting results
- **Tables**: `trades`, `orders`, `positions`, `historical_prices`, `backtest_*`, `signals`

### 2. **Vector Storage External** (`localhost:11151/trading`)
- **Purpose**: Vector embeddings, AI/ML data, semantic search
- **Tables**: `vector_embeddings`, `vectorization_*`, `news_*` (for semantic search)

### 3. **Apache AGE External** (`localhost:11152/trading`)
- **Purpose**: Graph analytics, relationship mapping, network analysis
- **Tables**: `trading_relationships`, `market_correlations`, `news_networks`

### 4. **Regular PostgreSQL External** (`localhost:11153/trading`)
- **Purpose**: Configuration, metadata, reference data
- **Tables**: `trading_config`, `popular_symbols`, `report_jobs`, `risk_metrics`

## 🔄 **Migration Strategy**

### **Phase 1: Schema Setup & Validation**
1. Create new databases on external servers
2. Set up proper extensions (TimescaleDB, pgvector, Apache AGE)
3. Create tables with optimized schemas
4. Validate connectivity and permissions

### **Phase 2: Data Migration**
1. **Core Trading Data** → TimescaleDB External
2. **Vector Data** → Vector Storage External  
3. **Configuration Data** → Regular PostgreSQL External
4. **Graph Data** → Apache AGE External

### **Phase 3: Service Updates**
1. Update Kubernetes ConfigMaps with new database URLs
2. Update service environment variables
3. Test connectivity and functionality
4. Rollback plan ready

### **Phase 4: Cutover & Cleanup**
1. Switch services to new databases
2. Verify data integrity
3. Remove old database connections
4. Monitor performance

## 📋 **Migration Scripts**

### **1. Database Setup Scripts**
- `setup-external-databases.sh` - Create databases and extensions
- `validate-connectivity.sh` - Test all database connections
- `create-migration-schemas.sh` - Set up target schemas

### **2. Data Migration Scripts**
- `migrate-trading-data.py` - Core trading data migration
- `migrate-vector-data.py` - Vector embeddings migration
- `migrate-config-data.py` - Configuration data migration
- `migrate-graph-data.py` - Graph data for Apache AGE

### **3. Service Update Scripts**
- `update-service-configs.sh` - Update Kubernetes ConfigMaps
- `update-service-envs.py` - Update service environment variables
- `test-migration.py` - Validate migration success

### **4. Rollback Scripts**
- `rollback-migration.sh` - Emergency rollback to old databases
- `restore-service-configs.sh` - Restore old service configurations

## 🚨 **Risk Mitigation**

### **Before Migration**
- ✅ Full database backup
- ✅ Service-by-service migration (not all at once)
- ✅ Rollback procedures tested
- ✅ Monitoring and alerting in place

### **During Migration**
- ✅ Data validation at each step
- ✅ Service health checks
- ✅ Performance monitoring
- ✅ Rollback capability at any point

### **After Migration**
- ✅ Data integrity verification
- ✅ Performance benchmarking
- ✅ Service functionality testing
- ✅ Old database cleanup (after validation period)

## 📊 **Migration Timeline**

### **Day 1**: Setup & Validation
- Set up external databases
- Test connectivity
- Create target schemas

### **Day 2**: Data Migration
- Migrate core trading data
- Migrate vector data
- Migrate configuration data

### **Day 3**: Service Updates
- Update service configurations
- Test functionality
- Performance validation

### **Day 4**: Cutover
- Switch services to new databases
- Monitor performance
- Validate data integrity

### **Day 5**: Cleanup
- Remove old connections
- Archive old databases
- Documentation updates

## 🔍 **Success Criteria**

### **Data Integrity**
- ✅ All data successfully migrated
- ✅ No data loss or corruption
- ✅ Referential integrity maintained
- ✅ Indexes and constraints preserved

### **Performance**
- ✅ Query performance maintained or improved
- ✅ Connection pooling working correctly
- ✅ No timeout or connection issues
- ✅ Resource usage within expected ranges

### **Functionality**
- ✅ All services working correctly
- ✅ Dashboards displaying data
- ✅ Backtesting functionality intact
- ✅ API endpoints responding correctly

## 📞 **Emergency Contacts**

### **Rollback Triggers**
- Data corruption detected
- Performance degradation >20%
- Service failures >5%
- Data loss of any kind

### **Rollback Procedure**
1. Stop all services
2. Restore old database connections
3. Restart services with old configs
4. Investigate migration issues
5. Plan and execute corrected migration

---

**Next Steps**: Run `./scripts/setup-external-databases.sh` to begin the migration process.
