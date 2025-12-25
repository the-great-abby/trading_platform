# Database Port Forward Guide

## Quick Reference

### Start Database Port Forward
```bash
# Option 1: Using database Makefile
make -f makefiles/Makefile.database db-port-forward

# Option 2: Using generic port-forward command
make -f makefiles/Makefile.port-forward port-forward SERVICE=database

# Option 3: Direct kubectl (manual)
kubectl port-forward -n postgres-infra svc/postgres-timescale-external 5432:5432 &
```

### Check Status
```bash
# Check if port forward is active
make -f makefiles/Makefile.database db-port-check

# Check environment (includes database status)
make -f makefiles/Makefile.demo env-info

# Check all active port forwards
ps aux | grep "kubectl port-forward" | grep postgres
```

### Stop Port Forward
```bash
# Stop database port forward
make -f makefiles/Makefile.database db-port-stop

# Or manually
pkill -f "kubectl port-forward.*postgres"
```

## Connection Information

Once port-forwarded, connect using:

**Python (psycopg2/SQLAlchemy):**
```python
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/trading_bot"
```

**psql Command:**
```bash
psql -h localhost -p 5432 -U postgres -d trading_bot
# Password: postgres
```

**Environment Variable:**
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trading_bot
```

## Common Issues & Solutions

### Issue: "Port 5432 already in use"

**Cause:** Another process is using port 5432 (local PostgreSQL or existing port-forward)

**Solution:**
```bash
# Check what's using the port
lsof -i:5432

# Stop existing port forward
make -f makefiles/Makefile.database db-port-stop

# Or kill local PostgreSQL if running
brew services stop postgresql@14  # or your version
```

### Issue: "Connection refused"

**Cause:** Port forward not started or died

**Solution:**
```bash
# Start port forward
make -f makefiles/Makefile.database db-port-forward

# Verify it's running
make -f makefiles/Makefile.database db-port-check

# Check process is active
ps aux | grep "kubectl port-forward.*postgres" | grep -v grep
```

### Issue: Port forward keeps dying

**Cause:** Port forwards can die when the parent process exits

**Solution:**
```bash
# Use screen or tmux for persistent sessions
screen -S db-forward
kubectl port-forward -n postgres-infra svc/postgres-timescale-external 5432:5432
# Ctrl+A, D to detach

# Or use nohup with explicit background
nohup kubectl port-forward -n postgres-infra svc/postgres-timescale-external 5432:5432 > /dev/null 2>&1 &
```

### Issue: "Cannot connect to Kubernetes cluster"

**Cause:** kubectl not configured or cluster not accessible

**Solution:**
```bash
# Check kubectl configuration
kubectl config current-context

# Test cluster access
kubectl get pods -n postgres-infra

# If using minikube
minikube status
```

## Auto-Start with Demos

The demo Makefiles now automatically check for database connectivity:

```bash
# Automatically checks database before running
make -f makefiles/Makefile.demo options-demo

# If database isn't available, you'll see:
# ❌ ERROR: Cannot connect to database on localhost:5432
# 
# 💡 Solution: Start database port forward
#    make -f makefiles/Makefile.database db-port-forward
```

## Integration with Environment Loading

### Using Makefile.demo

The `Makefile.demo` automatically:
1. ✅ Loads `POLYGON_API_KEY` from Kubernetes secrets
2. ✅ Checks database connectivity on port 5432
3. ✅ Provides helpful error messages if database isn't available
4. ✅ Sets `DATABASE_URL` environment variable

```bash
# Shows all environment status including database
make -f makefiles/Makefile.demo env-info
```

### Using direnv (Optional)

If you've installed direnv (from `.envrc.example`):

```bash
cd /Users/abby/code/trading
# direnv auto-loads environment variables
# But you still need to manually start port-forward
make -f makefiles/Makefile.database db-port-forward
```

## Best Practices

### For Quick Tasks
```bash
# Start port-forward, run demo, stop port-forward
make -f makefiles/Makefile.database db-port-forward
make -f makefiles/Makefile.demo options-demo
make -f makefiles/Makefile.database db-port-stop
```

### For Development Sessions
```bash
# Start port-forward at beginning of day
make -f makefiles/Makefile.database db-port-forward

# Run multiple demos/scripts
make -f makefiles/Makefile.demo options-demo
make -f makefiles/Makefile.demo comparison-demo
python3 demo/demo_stock_recommendations.py

# Stop at end of day
make -f makefiles/Makefile.database db-port-stop
```

### For Background Work
```bash
# Use screen/tmux for persistent port-forwards
screen -S db-forward
make -f makefiles/Makefile.database db-port-forward
# Ctrl+A, D to detach

# Reattach anytime
screen -r db-forward
```

## Database Details

### TimescaleDB (trading_bot)
- **Kubernetes Service:** `postgres-timescale-external.postgres-infra.svc.cluster.local`
- **Namespace:** `postgres-infra`
- **Port:** 5432
- **Database:** `trading_bot`
- **Username:** `postgres`
- **Password:** `postgres`
- **Use Case:** Market data, options data, backtests

### PostgreSQL Vector (trading)
- **Kubernetes Service:** `postgres-vector`
- **Namespace:** `postgres-infra`  
- **Database:** `trading`
- **Use Case:** Vector embeddings, AI analysis

## Makefile Targets Summary

### Database Makefile (`makefiles/Makefile.database`)
- `db-port-forward` - Start port forward to localhost:5432
- `db-port-check` - Verify port forward is working
- `db-port-stop` - Stop port forward
- `db-shell-timescale` - Open psql shell (requires port forward)
- `db-backup-timescale` - Backup trading_bot database
- `db-restore-timescale BACKUP=file` - Restore from backup

### Port Forward Makefile (`makefiles/Makefile.port-forward`)
- `port-forward SERVICE=database` - Generic port forward command
- `port-list` - List all available services including database
- `port-status` - Show all active port forwards

### Demo Makefile (`Makefile.demo`)
- `env-info` - Show environment including database status
- `options-demo` - Run options demo (checks database first)
- `comprehensive-demo` - Run comprehensive comparison (checks database first)

## Testing Database Connection

### Quick Test (nc)
```bash
nc -zv localhost 5432
# Connection to localhost port 5432 [tcp/postgresql] succeeded!
```

### Full Test (psql)
```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d trading_bot \
  -c "SELECT 'Connected!' as status, current_database(), current_timestamp;"
```

### Python Test
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="trading_bot",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()
cur.execute("SELECT 'Connected!', current_database(), now();")
print(cur.fetchone())
conn.close()
```

## Troubleshooting Checklist

- [ ] Kubernetes cluster is accessible (`kubectl get pods`)
- [ ] Pod is running in postgres-infra namespace (`kubectl get pods -n postgres-infra`)
- [ ] Port 5432 is not already in use (`lsof -i:5432`)
- [ ] Port forward command ran successfully
- [ ] Process is still running (`ps aux | grep port-forward`)
- [ ] Connection succeeds (`nc -zv localhost 5432`)
- [ ] Credentials are correct (`postgres/postgres`)

## Related Documentation

- `docs/ENVIRONMENT_SETUP.md` - Environment variable auto-loading
- `makefiles/Makefile.database` - Database management commands
- `makefiles/Makefile.port-forward` - Port forwarding commands
- `PORT_MAP.md` - Complete port mapping reference












