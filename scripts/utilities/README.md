# Utility Scripts

This directory contains utility scripts for system maintenance and operations.

## Scripts

- `refresh_public_token.py` - Refresh Public.com API access token
- `clear_encrypted_credentials.py` - Clear encrypted credentials from database
- `update_order_helper.py` - Helper for updating orders
- `cli_recovery.py` - CLI recovery utilities

## Usage

```bash
# Refresh API token
python scripts/utilities/refresh_public_token.py

# Clear credentials
python scripts/utilities/clear_encrypted_credentials.py
```

## Makefile Integration

These scripts are integrated into Makefile targets:

```bash
# Via Makefile
make live-trading-refresh-token
make live-trading-fix-credentials
```

