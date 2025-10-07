#!/bin/bash
# Quick script to update the Public.com access token

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <new_access_token>"
    echo ""
    echo "Example:"
    echo "  $0 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    exit 1
fi

NEW_TOKEN="$1"
ACCOUNT_ID="19c25392-8b61-4b71-a344-0eb04d275528"

echo "🔄 Updating access token in database..."

POD=$(kubectl get pods -n default -l app=live-trading-service -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n default $POD -- python3 << PYTHON
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

async def update_token():
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Update the most recent credential
        await session.execute(text('''
            UPDATE api_credentials
            SET access_token = :token,
                token_expires_at = NOW() + INTERVAL '24 hours',
                updated_at = NOW()
            WHERE account_id = :account_id
            AND credential_id = (
                SELECT credential_id 
                FROM api_credentials 
                WHERE account_id = :account_id 
                ORDER BY created_at DESC 
                LIMIT 1
            )
        '''), {'token': '${NEW_TOKEN}', 'account_id': '${ACCOUNT_ID}'})
        
        await session.commit()
        print("✅ Access token updated successfully!")
        print("   Expires: 24 hours from now")

asyncio.run(update_token())
PYTHON

echo ""
echo "🔄 Restarting live-trading-service to pick up new token..."
kubectl rollout restart deployment/live-trading-service -n default

echo ""
echo "✅ Done! The new token is active."
echo "   You can test it with: make -f Makefile.live-trading test-execution"
