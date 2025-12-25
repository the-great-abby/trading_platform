# Database Credentials Reference

## TimescaleDB (postgres-infra namespace)

### Production (Kubernetes)
```
Host: postgres-timescale-external.postgres-infra.svc.cluster.local
Port: 5432
Database: trading_bot
Username: postgres
Password: postgres
```

**Connection String:**
```
postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot
```

### Local Development (Port-Forwarded)
```
Host: localhost
Port: 5432
Database: trading_bot
Username: postgres
Password: postgres
```

**Connection String:**
```
postgresql://postgres:postgres@localhost:5432/trading_bot
```

**Environment Variable:**
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trading_bot
```

---

## PostgreSQL Vector (postgres-infra namespace)

### Production (Kubernetes)
```
Host: postgres-vector.postgres-infra.svc.cluster.local
Port: 5432
Database: trading
Username: postgres
Password: postgres
```

**Connection String:**
```
postgresql://postgres:postgres@postgres-vector.postgres-infra.svc.cluster.local:5432/trading
```

---

## Usage Examples

### Python (psycopg2)
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",  # or K8s service name
    port=5432,
    database="trading_bot",
    user="postgres",
    password="postgres"
)
```

### Python (SQLAlchemy)
```python
from sqlalchemy import create_engine

# Local (port-forwarded)
engine = create_engine("postgresql://postgres:postgres@localhost:5432/trading_bot")

# Kubernetes
engine = create_engine("postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot")
```

### psql CLI
```bash
# Local (port-forwarded)
psql -h localhost -p 5432 -U postgres -d trading_bot
# Password: postgres

# Or with PGPASSWORD
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d trading_bot
```

### Environment Variables
```bash
# For local development with port-forward
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trading_bot

# For scripts running in Kubernetes
export DATABASE_URL=postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot
```

---

## Common Mistakes ❌

### Wrong Credentials
```bash
# ❌ WRONG - These credentials don't exist
postgresql://trading_user:trading_pass@localhost:5432/trading_bot

# ✅ CORRECT - Use postgres:postgres
postgresql://postgres:postgres@localhost:5432/trading_bot
```

### Wrong Database Name
```bash
# ❌ WRONG - "trading" is the Vector DB, not TimescaleDB
postgresql://postgres:postgres@localhost:5432/trading

# ✅ CORRECT - "trading_bot" is the TimescaleDB database
postgresql://postgres:postgres@localhost:5432/trading_bot
```

### Wrong Host (Local Dev)
```bash
# ❌ WRONG - K8s service name won't work locally
postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot

# ✅ CORRECT - Use localhost when port-forwarded
postgresql://postgres:postgres@localhost:5432/trading_bot
```

---

## Which Database for What?

### TimescaleDB (`trading_bot`)
**Use for:**
- ✅ Market data storage (OHLCV, ticks)
- ✅ Options data and Greeks
- ✅ Backtest results
- ✅ Performance metrics
- ✅ Time-series data

**Connection:**
```bash
# Local
postgresql://postgres:postgres@localhost:5432/trading_bot

# K8s
postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot
```

### PostgreSQL Vector (`trading`)
**Use for:**
- ✅ Vector embeddings
- ✅ Semantic search
- ✅ AI/ML features
- ✅ Document storage with pgvector

**Connection:**
```bash
# K8s only (not typically port-forwarded)
postgresql://postgres:postgres@postgres-vector.postgres-infra.svc.cluster.local:5432/trading
```

---

## Verifying Credentials

### Test Connection
```bash
# Make sure port-forward is active
make -f makefiles/Makefile.database db-port-forward

# Test connection
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d trading_bot -c "SELECT current_database(), current_user, now();"
```

**Expected output:**
```
 current_database | current_user |              now              
------------------+--------------+-------------------------------
 trading_bot      | postgres     | 2025-10-10 13:00:00.123456+00
```

### Check in Code
```python
import os
import psycopg2

# This should work with the Makefile.demo environment
db_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {db_url}")

# Should print: postgresql://postgres:postgres@localhost:5432/trading_bot

# Test connection
conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("SELECT current_database(), current_user;")
print(cur.fetchone())
conn.close()
```

---

## Security Notes

⚠️ **These credentials are for development/testing only!**

In production Kubernetes:
- Credentials are stored in Kubernetes secrets
- Services connect using internal cluster DNS
- Network policies restrict access
- Passwords should be rotated regularly

For local development:
- Port-forwarding provides secure tunnel through kubectl
- No direct database exposure
- Requires valid kubectl context and permissions

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ TimescaleDB (trading_bot) - Default Database                │
├─────────────────────────────────────────────────────────────┤
│ Local:  postgresql://postgres:postgres@localhost:5432/trading_bot
│ K8s:    postgres-timescale-external.postgres-infra.svc.cluster.local:5432
│ User:   postgres / postgres                                 │
│ Shell:  make -f makefiles/Makefile.database db-shell-timescale
└─────────────────────────────────────────────────────────────┘
```












