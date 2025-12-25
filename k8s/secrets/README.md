# Kubernetes Secrets Management

This directory contains Kubernetes Secret manifests for the trading system.

## ⚠️ Security Notice

**DO NOT commit actual secret values to git!**

The files in this directory use placeholder values or are meant for documentation purposes only. Real secrets should be:
1. Generated securely
2. Stored in a secrets management system (e.g., HashiCorp Vault, AWS Secrets Manager)
3. Applied directly to the cluster without committing to version control

## Secrets Overview

### 1. `live-trading-encryption.yaml`
**Purpose**: Encryption key for encrypting/decrypting Public.com API credentials

**Usage**: 
- Used by live-trading-service to encrypt sensitive data before storing in database
- Required for decrypting stored API credentials

**Generation**:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

**Referenced by**:
- `paper-trading-k8s` deployment (environment variable `ENCRYPTION_KEY`)

### 2. `api-keys.yaml`
**Purpose**: External API keys (Polygon, etc.)

### 3. `database.yaml`
**Purpose**: Database credentials

## Applying Secrets

```bash
# Apply all secrets
kubectl apply -f k8s/secrets/

# Apply specific secret
kubectl apply -f k8s/secrets/live-trading-encryption.yaml

# Verify secret was created
kubectl get secrets -n trading-system | grep live-trading-encryption-key
```

## Rotating Secrets

### Encryption Key Rotation

**⚠️ Important**: Rotating the encryption key requires re-encrypting all existing credentials in the database.

Steps:
1. Generate new encryption key
2. Update the secret in Kubernetes
3. Re-authenticate with Public.com API to create new encrypted credentials
4. Update deployment to use new key
5. Verify services can decrypt credentials

```bash
# Update secret
kubectl create secret generic live-trading-encryption-key \
  --from-literal=encryption-key='NEW_KEY_HERE' \
  -n trading-system \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up new secret
kubectl rollout restart deployment/paper-trading-k8s -n trading-system
```

## Best Practices

1. **Never commit real secrets** to version control
2. **Use RBAC** to restrict access to secrets
3. **Rotate secrets regularly** (quarterly or after any suspected compromise)
4. **Monitor secret access** through audit logs
5. **Use sealed secrets** or external secrets operators for GitOps workflows

## Production Recommendations

For production environments, consider:

### Option 1: Sealed Secrets
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubeseal --format=yaml < live-trading-encryption.yaml > live-trading-encryption-sealed.yaml
```

### Option 2: External Secrets Operator
```bash
# Install external-secrets
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# Create SecretStore pointing to your secrets backend (Vault, AWS, etc.)
```

### Option 3: HashiCorp Vault
```bash
# Store secret in Vault
vault kv put secret/trading/encryption-key value='<key>'

# Configure Vault agent injector
```

## Troubleshooting

### Secret not found
```bash
# Check if secret exists
kubectl get secret live-trading-encryption-key -n trading-system

# Describe secret
kubectl describe secret live-trading-encryption-key -n trading-system
```

### Service can't read secret
```bash
# Check service account permissions
kubectl get serviceaccount -n trading-system
kubectl describe rolebinding -n trading-system
```

### Wrong encryption key
Symptoms: "Invalid token" or decryption errors in logs

Solution: Verify the encryption key matches what was used to encrypt credentials, or re-authenticate to create new encrypted credentials.

## Related Documentation

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [External Secrets Operator](https://external-secrets.io/)












