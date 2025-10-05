# Quickstart: Kubernetes Secrets Management

## Overview
This guide walks through setting up and using the Kubernetes secrets management system via Makefile targets. The system automatically reads from your `.env` file and updates Kubernetes secrets with proper naming conventions.

## Prerequisites

1. **Kubernetes Cluster Access**
   ```bash
   kubectl cluster-info
   kubectl config current-context
   ```

2. **Environment File Setup**
   ```bash
   # Create .env file with your secrets
   cp .env.example .env
   chmod 600 .env  # Restrict permissions
   ```

3. **Required Tools**
   - `kubectl` (configured for your cluster)
   - `make`
   - `bash` (version 4.0+)

## Quick Start Steps

### Step 1: Prepare Your Environment File

Create a `.env` file with your secret values:

```bash
# API Keys (for trading data providers)
POLYGON_API_KEY=your_polygon_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Database Credentials
DB_HOST=your_database_host
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=trading_system
```

**Important**: 
- Use underscores in variable names (they'll be converted to hyphens in Kubernetes)
- Never commit the `.env` file to version control
- Set restrictive file permissions: `chmod 600 .env`

### Step 2: Validate Your Configuration

Before updating secrets, validate your setup:

```bash
make secrets-validate
```

**Expected Output**:
```
✅ Validating .env file...
✅ Found 5 secret configurations
✅ All validations passed
✅ Ready to update secrets
```

**If validation fails**:
```
❌ Validation Error: POLYGON_API_KEY is empty
Next steps:
  1. Check .env file contains required values
  2. Verify file permissions: ls -la .env
  3. Re-run: make secrets-validate
```

### Step 3: Update Kubernetes Secrets

Update your cluster with the secrets from the `.env` file:

```bash
make secrets-update
```

**Expected Output**:
```
✅ Updating Kubernetes secrets from .env file...
✅ Created/updated secret: polygon-api-key
✅ Created/updated secret: alpha-vantage-api-key
✅ Created/updated secret: db-credentials
✅ All secrets updated successfully!

Next steps:
  1. Verify secrets: kubectl get secrets
  2. Check specific secret: kubectl describe secret polygon-api-key
  3. Restart affected services: kubectl rollout restart deployment/strategy-service
  4. Monitor logs: kubectl logs -f deployment/strategy-service
```

### Step 4: Verify Secrets in Cluster

Confirm your secrets are properly created:

```bash
make secrets-list
```

**Expected Output**:
```
✅ Listing Kubernetes secrets...
📋 Managed secrets in namespace 'default':

Name: polygon-api-key
Type: api-key
Created: 2025-01-02T10:30:00Z
Keys: [api-key]

Name: alpha-vantage-api-key  
Type: api-key
Created: 2025-01-02T10:30:00Z
Keys: [api-key]

Name: db-credentials
Type: database
Created: 2025-01-02T10:30:00Z
Keys: [host, username, password, database]
```

## Common Operations

### Update a Single Secret Type

To update only API keys:
```bash
make secrets-update-api-keys
```

To update only database credentials:
```bash
make secrets-update-database
```

### Update Secrets in Specific Namespace

```bash
NAMESPACE=trading make secrets-update
```

### Validate Without Updating

```bash
make secrets-validate
```

### List Secrets in Specific Namespace

```bash
NAMESPACE=trading make secrets-list
```

## Troubleshooting

### Error: Cannot Connect to Kubernetes Cluster

```bash
❌ Error: Cannot connect to Kubernetes cluster
Next steps:
  1. Check cluster connectivity: kubectl cluster-info
  2. Verify kubeconfig: kubectl config current-context
  3. Switch context if needed: kubectl config use-context your-context
```

**Solution**: Ensure kubectl is configured and your cluster is accessible.

### Error: .env File Not Found

```bash
❌ Error: .env file not found
Next steps:
  1. Create .env file: cp .env.example .env
  2. Add your secret values to .env
  3. Set permissions: chmod 600 .env
```

**Solution**: Create the `.env` file with your secret values.

### Error: Validation Failed

```bash
❌ Validation Error: POLYGON_API_KEY is empty
❌ Validation Error: DB_PASSWORD format invalid
Next steps:
  1. Check .env file contains all required values
  2. Verify no empty lines or comments in .env
  3. Re-run validation: make secrets-validate
```

**Solution**: Ensure all required variables have values and follow the correct format.

### Error: Permission Denied

```bash
❌ Error: Permission denied creating secret
Next steps:
  1. Check cluster permissions: kubectl auth can-i create secrets
  2. Verify namespace access: kubectl auth can-i create secrets --namespace=default
  3. Contact cluster administrator for access
```

**Solution**: Ensure you have the necessary Kubernetes permissions.

## Advanced Usage

### Custom Secret Mappings

The system automatically maps `.env` variables to Kubernetes secrets:

| .env Variable | Kubernetes Secret | Type |
|---------------|-------------------|------|
| `POLYGON_API_KEY` | `polygon-api-key` | api-key |
| `DB_HOST` | `db-credentials` | database |
| `DB_USERNAME` | `db-credentials` | database |
| `DB_PASSWORD` | `db-credentials` | database |
| `DB_NAME` | `db-credentials` | database |

### Environment-Specific Configurations

For different environments, use different `.env` files:

```bash
# Development
make secrets-update ENV_FILE=.env.dev

# Staging  
make secrets-update ENV_FILE=.env.staging

# Production
make secrets-update ENV_FILE=.env.prod
```

### Integration with CI/CD

```bash
# In your CI pipeline
make secrets-validate
if [ $? -eq 0 ]; then
    make secrets-update
    echo "✅ Secrets updated successfully"
else
    echo "❌ Secret validation failed"
    exit 1
fi
```

## Security Best Practices

1. **File Permissions**: Always set `.env` files to `600` (readable only by owner)
2. **Version Control**: Never commit `.env` files - add to `.gitignore`
3. **Audit Logging**: All secret operations are logged (without exposing values)
4. **Namespace Isolation**: Use appropriate namespaces for different environments
5. **Regular Rotation**: Update secrets regularly for security

## Next Steps

After successfully updating your secrets:

1. **Restart Services**: Restart any services that use these secrets
2. **Verify Access**: Test that services can access the updated secrets
3. **Monitor Logs**: Check service logs for any secret-related errors
4. **Update Documentation**: Document any new secret requirements

For more detailed information, see the full documentation in the `docs/` directory.

