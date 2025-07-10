#!/usr/bin/env python3
"""
Ollama Model Verification Script
Verifies which model is being used and tests responses
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any

async def verify_ollama_setup():
    """Verify Ollama setup and model availability"""
    
    # Configuration
    base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    target_model = os.getenv("OLLAMA_MODEL", "smollm2")
    
    print(f"🔧 Ollama Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Target Model: {target_model}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # 1. Check if Ollama is running
        try:
            async with session.get(f"{base_url}/api/tags", timeout=10) as response:
                if response.status == 200:
                    print("✅ Ollama server is running")
                else:
                    print(f"❌ Ollama server error: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            return
        
        # 2. Get available models
        try:
            async with session.get(f"{base_url}/api/tags") as response:
                models_data = await response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                print(f"📋 Available Models ({len(available_models)}):")
                for model in available_models:
                    print(f"   - {model}")
                print()
                
                # Check if target model is available
                target_available = any(target_model in model for model in available_models)
                print(f"🎯 Target model '{target_model}' available: {target_available}")
                print()
                
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return
        
        # 3. Test model with simple prompt
        print("🧪 Testing model response...")
        try:
            test_payload = {
                "model": target_model,
                "prompt": "Respond with exactly: 'OK'",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 50
                }
            }
            
            async with session.post(
                f"{base_url}/api/generate",
                json=test_payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get('response', '')
                    used_model = result.get('model', 'unknown')
                    
                    print(f"✅ Test successful!")
                    print(f"   Model used: {used_model}")
                    print(f"   Response: '{response_text}'")
                    print(f"   Response length: {len(response_text)} characters")
                    
                    # Verify model matches
                    if used_model == target_model:
                        print(f"✅ Model verification passed - using {target_model}")
                    else:
                        print(f"⚠️ Model mismatch! Expected: {target_model}, Got: {used_model}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Test failed - Status: {response.status}")
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        # 4. Test with actual trading prompt
        print("\n🧪 Testing with trading prompt...")
        try:
            trading_payload = {
                "model": target_model,
                "prompt": """Analyze this trade signal and respond in JSON format:
                Symbol: AAPL
                Action: BUY
                Price: $171.10
                Strategy: BollingerBandsStrategy
                
                Respond with: {"approved": true, "confidence": 0.8, "reasoning": "test"}""",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2000
                }
            }
            
            async with session.post(
                f"{base_url}/api/generate",
                json=trading_payload,
                timeout=120
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get('response', '')
                    used_model = result.get('model', 'unknown')
                    
                    print(f"✅ Trading test successful!")
                    print(f"   Model used: {used_model}")
                    print(f"   Response length: {len(response_text)} characters")
                    print(f"   Response preview: {response_text[:200]}...")
                    
                    # Try to parse JSON
                    try:
                        json_data = json.loads(response_text)
                        print(f"✅ JSON parsing successful")
                        print(f"   Keys: {list(json_data.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing failed: {e}")
                        print(f"   Raw response: {response_text}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Trading test failed - Status: {response.status}")
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Trading test error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_ollama_setup()) 