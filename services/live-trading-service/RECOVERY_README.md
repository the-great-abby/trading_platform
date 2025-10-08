# Trade Recovery Service - Consolidated Implementation

## **🎯 Overview**

The Trade Recovery Service has been **consolidated into the Live Trading Service** for resource efficiency. This implementation provides disaster recovery capabilities for active trades while minimizing resource usage on your constrained system.

## **📊 Resource Impact**

### **Before Consolidation**:
- Live Trading Service: 128Mi RAM, 100m CPU
- Trade Recovery Service: 256Mi RAM, 200m CPU
- **Total**: 384Mi RAM, 300m CPU, 2 pods

### **After Consolidation**:
- Live Trading Service (with recovery): 256Mi RAM, 200m CPU
- **Total**: 256Mi RAM, 200m CPU, 1 pod
- **Savings**: 128Mi RAM, 100m CPU, 1 pod (33% reduction)

## **🔧 Architecture**

### **Consolidated Service Structure**
```
services/live-trading-service/
├── routes/
│   ├── trading.py          # Existing trading endpoints
│   ├── recovery.py         # NEW: Recovery endpoints
│   └── strategies.py       # Existing strategy endpoints
├── src/services/live_trading/
│   ├── recovery_service.py  # NEW: Recovery logic
│   ├── recovery_models.py  # NEW: Recovery data models
│   └── public_api_client.py # Existing broker integration
├── cli_recovery.py         # NEW: CLI tool for emergency recovery
└── main.py                # Updated to include recovery routes
```

### **API Endpoints**
All recovery endpoints are now available under `/api/v1/recovery/`:

- `POST /api/v1/recovery/sessions` - Create recovery session
- `GET /api/v1/recovery/sessions/{session_id}` - Get session details
- `GET /api/v1/recovery/sessions/{session_id}/status` - Get session status
- `PUT /api/v1/recovery/sessions/{session_id}` - Update session
- `GET /api/v1/recovery/sessions` - List sessions
- `POST /api/v1/recovery/trades/active` - Detect active trades
- `GET /api/v1/recovery/strategies/available` - Get available strategies
- `POST /api/v1/recovery/strategies/match` - Match strategies for trade
- `POST /api/v1/recovery/assign-strategy` - Assign strategy to trade
- `POST /api/v1/recovery/assign-strategy/{id}/confirm` - Confirm assignment
- `POST /api/v1/recovery/assign-strategy/{id}/reject` - Reject assignment
- `GET /api/v1/recovery/sessions/{session_id}/assignments` - Get assignments
- `GET /api/v1/recovery/sessions/{session_id}/logs` - Get recovery logs
- `POST /api/v1/recovery/bulk-assign` - Bulk assign strategies

## **🚀 Usage**

### **1. API Usage**

#### **Create Recovery Session**
```bash
curl -X POST "http://localhost:11120/api/v1/recovery/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acc_123",
    "recovery_type": "DATABASE_FAILURE",
    "description": "Recovery after database loss"
  }'
```

#### **Detect Active Trades**
```bash
curl -X POST "http://localhost:11120/api/v1/recovery/trades/active" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acc_123",
    "include_closed": false
  }'
```

#### **Match Strategies**
```bash
curl -X POST "http://localhost:11120/api/v1/recovery/strategies/match" \
  -H "Content-Type: application/json" \
  -d '{
    "trade_id": "trade_456",
    "session_id": "session_789"
  }'
```

#### **Assign Strategy**
```bash
curl -X POST "http://localhost:11120/api/v1/recovery/assign-strategy" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_789",
    "trade_id": "trade_456",
    "strategy_id": "strategy_1",
    "strategy_name": "Elliott Wave Strategy",
    "confidence_score": 0.85,
    "assignment_reason": "HIGH_CONFIDENCE_MATCH",
    "auto_assigned": true
  }'
```

### **2. CLI Tool Usage**

The CLI tool provides zero-resource emergency recovery capabilities:

#### **Interactive Recovery Mode**
```bash
cd services/live-trading-service
python cli_recovery.py interactive --account acc_123
```

#### **Full Recovery Workflow**
```bash
python cli_recovery.py recover --account acc_123 --auto-assign
```

#### **Individual Operations**
```bash
# Detect trades
python cli_recovery.py detect --account acc_123 --output trades.json

# Create session
python cli_recovery.py session --account acc_123 --type MANUAL_RECOVERY

# Match strategies
python cli_recovery.py match --trade-id trade_456 --session-id session_789

# Assign strategy
python cli_recovery.py assign --session-id session_789 --trade-id trade_456 \
  --strategy-id strategy_1 --strategy-name "Elliott Wave" --confidence 0.85

# Bulk assign
python cli_recovery.py bulk --session-id session_789 --auto-assign

# Check status
python cli_recovery.py status --session-id session_789
```

## **📋 Recovery Workflow**

### **1. Disaster Recovery Scenario**
1. **Detect Issue**: Database loss or system restart
2. **Create Session**: Start recovery session for affected account
3. **Detect Trades**: Query broker API for active positions
4. **Match Strategies**: Find best strategies for each trade
5. **Assign Strategies**: Auto-assign or manual assignment
6. **Confirm**: User confirms assignments
7. **Monitor**: Track recovery progress

### **2. Manual Recovery Scenario**
1. **User Initiates**: Manual recovery request
2. **Interactive Mode**: CLI tool guides through process
3. **Strategy Selection**: User chooses strategies
4. **Assignment**: Strategies assigned to trades
5. **Validation**: User validates assignments

## **🗄️ Database Schema**

### **New Tables Added**
- `active_trades` - Detected active trades
- `recovery_sessions` - Recovery session management
- `strategy_assignments` - Strategy assignments to trades
- `recovery_logs` - Recovery operation logs

### **Migration**
```bash
cd services/live-trading-service
alembic upgrade head
```

## **🔧 Configuration**

### **Environment Variables**
The service uses existing Live Trading Service configuration:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@timescaledb:5432/trading_db

# Redis
REDIS_URL=redis://redis:6379

# Broker API
PUBLIC_API_BASE_URL=https://api.public.com/userapigateway
PUBLIC_API_SECRET=your_secret_key

# Recovery Settings
TRADE_RECOVERY_AUTO_ASSIGN=true
TRADE_RECOVERY_MIN_CONFIDENCE=0.7
TRADE_RECOVERY_MAX_TRADES=100
```

## **📊 Monitoring**

### **Health Checks**
- `/health` - Basic health check
- `/ready` - Readiness check (database, Redis, broker API)
- `/metrics` - Prometheus metrics

### **Recovery Metrics**
- Active recovery sessions
- Trades detected per session
- Strategy assignments completed
- Recovery success rate
- Average recovery time

## **🚨 Emergency Procedures**

### **Database Loss Recovery**
1. **Stop Trading**: Halt all trading operations
2. **Run CLI Tool**: `python cli_recovery.py recover --account acc_123 --auto-assign`
3. **Verify Trades**: Check detected trades against broker
4. **Assign Strategies**: Confirm or modify strategy assignments
5. **Resume Trading**: Restart trading with recovered state

### **System Restart Recovery**
1. **Auto-Detection**: System detects active trades on startup
2. **User Notification**: Alert user of detected trades
3. **Recovery Session**: Create automatic recovery session
4. **Strategy Assignment**: Auto-assign based on previous assignments
5. **User Confirmation**: User confirms or modifies assignments

## **🔒 Security**

### **Authentication**
- JWT token validation
- API key authentication
- Rate limiting (100 requests/minute)

### **Data Protection**
- Encrypted sensitive data
- Audit logging
- Session isolation

## **📈 Performance**

### **Resource Usage**
- **Memory**: 256Mi (vs 384Mi for separate services)
- **CPU**: 200m (vs 300m for separate services)
- **Pods**: 1 (vs 2 for separate services)

### **Optimization**
- Shared database connections
- Shared Redis connections
- Reused broker API client
- Efficient SQL queries with proper indexing

## **🔄 Backup Strategy**

### **CLI Tool as Backup**
- Zero persistent resources
- Can run on any machine with database access
- Emergency recovery capability
- Manual intervention when needed

### **Data Persistence**
- All recovery data stored in PostgreSQL
- Redis for session state (optional)
- Comprehensive audit logs

## **🎯 Benefits**

### **Resource Efficiency**
- ✅ 33% reduction in memory usage
- ✅ 33% reduction in CPU usage
- ✅ 50% reduction in pod count
- ✅ Shared infrastructure components

### **Operational Simplicity**
- ✅ Single service to manage
- ✅ Unified monitoring
- ✅ Simplified deployment
- ✅ Consistent configuration

### **Disaster Recovery**
- ✅ Always-available recovery API
- ✅ Emergency CLI tool
- ✅ Comprehensive logging
- ✅ User-friendly interfaces

## **🚀 Next Steps**

1. **Deploy**: Update Live Trading Service with recovery functionality
2. **Test**: Run recovery scenarios in development
3. **Monitor**: Track resource usage and performance
4. **Document**: Update team documentation
5. **Train**: Train team on recovery procedures

The consolidated Trade Recovery Service provides robust disaster recovery capabilities while maintaining resource efficiency for your constrained system! 🎯




















