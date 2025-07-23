#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push Notifications - Proper ECDSA Version
This script generates proper ECDSA P-256 keys for VAPID using the cryptography library
"""

import base64
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption

def generate_vapid_keys():
    """Generate VAPID key pair for web push notifications using proper ECDSA"""
    
    # Generate a proper ECDSA P-256 key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Get the public key in uncompressed format (0x04 + X + Y)
    public_bytes = public_key.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint
    )
    
    # Get the private key bytes
    private_bytes = private_key.private_bytes(
        encoding=Encoding.DER,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    
    # Convert to base64 URL-safe strings (without padding)
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    
    return {
        'public_key': public_key_b64,
        'private_key': private_key_b64
    }

def main():
    """Generate and display VAPID keys"""
    print("🔑 Generating VAPID keys for Web Push Notifications...")
    
    try:
        keys = generate_vapid_keys()
        
        print("\n✅ VAPID Keys Generated Successfully!")
        print("\n📋 Public Key (applicationServerKey):")
        print(f"'{keys['public_key']}'")
        
        print("\n🔒 Private Key (for server-side):")
        print(f"'{keys['private_key']}'")
        
        print("\n📝 Environment Variables:")
        print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
        print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
        
        print("\n💡 Usage Instructions:")
        print("1. Copy the public key to your JavaScript code")
        print("2. Store the private key securely in your environment variables")
        print("3. Use the private key in your server-side push notification code")
        
        # Save to file
        os.makedirs('/tmp/vapid_keys', exist_ok=True)
        with open('/tmp/vapid_keys/vapid_keys.json', 'w') as f:
            json.dump(keys, f, indent=2)
        print("\n💾 Keys saved to '/tmp/vapid_keys/vapid_keys.json'")
        
        # Also save to environment file
        with open('/tmp/vapid_keys/vapid_keys.env', 'w') as f:
            f.write(f"VAPID_PUBLIC_KEY={keys['public_key']}\n")
            f.write(f"VAPID_PRIVATE_KEY={keys['private_key']}\n")
        print("💾 Environment variables saved to '/tmp/vapid_keys/vapid_keys.env'")
        
        # Print the keys in a format that can be easily copied to Kubernetes secrets
        print("\n🔐 Kubernetes Secret Format:")
        print("apiVersion: v1")
        print("kind: Secret")
        print("metadata:")
        print("  name: vapid-keys")
        print("  namespace: trading-system")
        print("type: Opaque")
        print("data:")
        print(f"  vapid-public-key: {base64.b64encode(keys['public_key'].encode()).decode()}")
        print(f"  vapid-private-key: {base64.b64encode(keys['private_key'].encode()).decode()}")
        
    except Exception as e:
        print(f"❌ Error generating VAPID keys: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 