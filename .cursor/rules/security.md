# Security Rules for Container-First Development

## 🔒 Container Security

### Never Execute Code on Host
- **NEVER** run Python scripts directly on the host system
- **NEVER** install packages directly on the host system
- **ALWAYS** use containers for code execution
- **ALWAYS** use containers for package management

### Container Isolation
- All code runs in isolated containers
- No direct access to host file system from Python code
- Network access controlled through Docker networking
- Process isolation prevents host system contamination

## 🔐 Environment Variables

### Secure Configuration
- **NEVER** hardcode API keys, passwords, or secrets
- **ALWAYS** use `.env` files for configuration
- **ALWAYS** use Docker secrets for production
- **NEVER** commit `.env` files to version control

### Environment Variable Usage
```bash
# ✅ Correct - Use .env file
docker-compose --env-file .env up

# ✅ Correct - Pass environment variables
docker-compose run -e API_KEY=your_key trading-cli python script.py

# ❌ WRONG - Hardcode secrets
docker-compose run trading-cli python -c "print('API_KEY=secret123')"
```

## 🗄️ Database Security

### Database Access
- **NEVER** connect to databases from host system
- **ALWAYS** use containers for database operations
- **ALWAYS** use proper authentication
- **NEVER** expose database ports to host unnecessarily

### Secure Database Commands
```bash
# ✅ Correct - Database access through container
docker-compose exec postgres-dev psql -U trading_user -d trading_bot

# ✅ Correct - Migrations in container
docker-compose exec trading-service alembic upgrade head

# ✅ Correct - Backup through container
docker-compose exec postgres-dev pg_dump -U trading_user trading_bot > backup.sql

# ❌ WRONG - Direct database access
psql -h localhost -U trading_user -d trading_bot
```

## 🌐 Network Security

### Container Networking
- Use Docker's internal networking
- **NEVER** expose unnecessary ports to host
- Use reverse proxies for external access
- Implement proper firewall rules

### Service Communication
```bash
# ✅ Correct - Service-to-service communication
docker-compose exec trading-service curl http://market-data-service:8000/data

# ✅ Correct - External access through gateway
curl http://localhost:8080/api/v1/trading

# ❌ WRONG - Direct external access to services
curl http://localhost:8000/api/v1/trading
```

## 📁 File System Security

### Volume Mounting
- **NEVER** mount entire host directories unnecessarily
- **ALWAYS** use specific volume mounts
- **NEVER** give containers root access to host
- **ALWAYS** use read-only mounts when possible

### Secure Volume Usage
```bash
# ✅ Correct - Specific volume mount
docker-compose run -v $(pwd)/data:/app/data trading-cli python script.py

# ✅ Correct - Read-only mount
docker-compose run -v $(pwd)/config:/app/config:ro trading-cli python script.py

# ❌ WRONG - Mount entire host
docker-compose run -v /:/host trading-cli python script.py
```

## 🔑 API Key Management

### Secure API Key Usage
- **NEVER** hardcode API keys in scripts
- **ALWAYS** use environment variables
- **ALWAYS** rotate API keys regularly
- **NEVER** log API keys or secrets

### API Key Patterns
```python
# ✅ Correct - Use environment variables
import os
api_key = os.getenv('POLYGON_API_KEY')
if not api_key:
    raise ValueError("POLYGON_API_KEY not set")

# ❌ WRONG - Hardcode API key
api_key = "your_secret_api_key_here"
```

## 🚨 Incident Response

### Security Breach Response
1. **Immediately stop affected containers**
2. **Rotate all API keys and secrets**
3. **Check container logs for suspicious activity**
4. **Review container configurations**
5. **Update security policies**

### Monitoring and Logging
```bash
# ✅ Correct - Monitor container logs
docker-compose logs -f trading-service

# ✅ Correct - Check container status
docker-compose ps

# ✅ Correct - Inspect container processes
docker-compose exec trading-service ps aux
```

## 📋 Security Checklist

### Development Environment
- [ ] All Python code runs in containers
- [ ] No direct host system access
- [ ] Environment variables used for secrets
- [ ] Database access through containers only
- [ ] Network ports properly configured
- [ ] File permissions set correctly

### Production Environment
- [ ] Docker secrets used for sensitive data
- [ ] Containers run as non-root users
- [ ] Multi-stage builds implemented
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Logging and monitoring enabled

### Code Review
- [ ] No hardcoded secrets in code
- [ ] Environment variables used properly
- [ ] Container configurations reviewed
- [ ] Security best practices followed
- [ ] No direct host system calls

## 🛡️ Security Best Practices

1. **Principle of Least Privilege**
   - Containers should have minimal required permissions
   - Use non-root users in containers
   - Limit file system access

2. **Defense in Depth**
   - Multiple layers of security
   - Container isolation
   - Network segmentation
   - Access controls

3. **Regular Updates**
   - Keep base images updated
   - Update dependencies regularly
   - Patch security vulnerabilities

4. **Monitoring and Auditing**
   - Monitor container activity
   - Log all access attempts
   - Regular security audits
   - Incident response procedures 