#!/usr/bin/env python3
"""
Generate proper VAPID keys for web push notifications
"""

import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption

def generate_vapid_keys():
    """Generate VAPID keys for web push notifications"""
    try:
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize keys
        private_key_bytes = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        public_key_bytes = public_key.public_bytes(
            encoding=Encoding.DER,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        
        # Convert to base64 URL-safe strings
        private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
        public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        
        return public_key_b64, private_key_b64
        
    except Exception as e:
        print(f"Error generating VAPID keys: {e}")
        return None, None

def validate_vapid_key(key: str) -> bool:
    """Validate VAPID key format"""
    try:
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', key):
            return False
        
        # Check length (should be 87 characters for base64 URL-safe)
        if len(key) != 87:
            return False
            
        return True
    except:
        return False

if __name__ == "__main__":
    print("🔑 Generating VAPID keys for web push notifications...")
    
    public_key, private_key = generate_vapid_keys()
    
    if public_key and private_key:
        print("✅ VAPID keys generated successfully!")
        print(f"Public Key: {public_key}")
        print(f"Private Key: {private_key}")
        
        if validate_vapid_key(public_key):
            print("✅ Public key format is valid")
        else:
            print("❌ Public key format is invalid")
            
        print("\n📋 For use in your application:")
        print(f'VAPID_PUBLIC_KEY = "{public_key}"')
        print(f'VAPID_PRIVATE_KEY = "{private_key}"')
    else:
        print("❌ Failed to generate VAPID keys") 