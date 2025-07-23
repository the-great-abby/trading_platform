#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push Notifications
"""

import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption

def generate_vapid_keys():
    """Generate VAPID key pair for web push notifications"""
    
    # Generate private key
    private_key = ec.generate_private_key(
        ec.SECP256R1()  # P-256 curve
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize public key to bytes
    public_key_bytes = public_key.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.CompressedPoint
    )
    
    # Convert to base64 URL-safe string (without padding)
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    # Serialize private key to bytes
    private_key_bytes = private_key.private_bytes(
        encoding=Encoding.DER,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    
    # Convert to base64 URL-safe string
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
    
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
        with open('vapid_keys.json', 'w') as f:
            json.dump(keys, f, indent=2)
        print("\n💾 Keys saved to 'vapid_keys.json'")
        
    except Exception as e:
        print(f"❌ Error generating VAPID keys: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 