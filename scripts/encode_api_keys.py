#!/usr/bin/env python3
"""
Script to encode API keys for Kubernetes secrets.

This script helps you encode your PUBLIC_API_KEY and PUBLIC_API_SECRET
for use in the live-trading-service Kubernetes secret.
"""

import base64
import sys
import os
from dotenv import load_dotenv

def encode_string(text: str) -> str:
    """Encode a string to base64."""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def main():
    """Main function to encode API key."""
    print("🔐 Personal Access Token Encoder for Live Trading Service")
    print("=" * 60)
    print("Note: Public.com uses personal access tokens (Bearer tokens)")
    print("instead of separate API key + secret combinations.")
    print("=" * 60)
    
    # Load .env file if it exists
    env_file = ".env"
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  No {env_file} file found, using environment variables")
    
    # Get access token from environment or prompt user
    access_token = os.getenv("PUBLIC_API_KEY")
    
    if not access_token:
        access_token = input("Enter your Public.com personal access token: ").strip()
    
    if not access_token:
        print("❌ Personal access token is required")
        print("💡 Get your token from: https://public.com/api")
        sys.exit(1)
    
    # Encode the token
    encoded_token = encode_string(access_token)
    
    print("\n📋 Encoded Value for Kubernetes Secret:")
    print("-" * 50)
    print(f"public-api-key: {encoded_token}")
    
    print("\n🔧 To update your Kubernetes secret, run:")
    print("-" * 50)
    print("kubectl create secret generic live-trading-service-secrets \\")
    print("  --from-literal=public-api-key='<your-encoded-token>' \\")
    print("  --dry-run=client -o yaml | kubectl apply -f -")
    
    print("\n📝 Or update the existing secret:")
    print("-" * 50)
    print(f"kubectl patch secret live-trading-service-secrets -p='{{\"data\":{{\"public-api-key\":\"{encoded_token}\"}}}}'")
    
    print("\n✅ Done! Your personal access token is ready for the live trading service.")
    print("💡 The service will now use Bearer token authentication with Public.com.")

if __name__ == "__main__":
    main()
