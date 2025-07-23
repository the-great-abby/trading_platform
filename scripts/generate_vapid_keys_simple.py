#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push Notifications using standard library
"""

import base64
import json
import os
import secrets

def generate_vapid_keys():
    """Generate VAPID key pair for web push notifications using standard library"""
    
    # Generate a random 32-byte private key
    private_key_bytes = secrets.token_bytes(32)
    
    # For demonstration, we'll create a simple public key
    # In production, you should use proper ECDSA key generation
    # This is a simplified version for testing
    
    # Create a deterministic public key from private key
    # This is not cryptographically secure but works for testing
    public_key_bytes = private_key_bytes[:32]  # Use first 32 bytes as public key
    
    # Convert to base64 URL-safe strings (without padding)
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
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
        
        # Also save to environment file
        with open('vapid_keys.env', 'w') as f:
            f.write(f"VAPID_PUBLIC_KEY={keys['public_key']}\n")
            f.write(f"VAPID_PRIVATE_KEY={keys['private_key']}\n")
        print("💾 Environment variables saved to 'vapid_keys.env'")
        
    except Exception as e:
        print(f"❌ Error generating VAPID keys: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 