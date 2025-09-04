#!/usr/bin/env python3
"""
Test script for AI IDE integration
Demonstrates how to use your local LLM and architecture database with Cursor IDE
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
AI_IDE_URL = "http://localhost:11050"
OLLAMA_URL = "http://localhost:11434"

def test_ai_ide_service():
    """Test the AI IDE service endpoints"""
    print("🧠 Testing AI IDE Integration")
    print("=" * 50)
    print("Using models: gpt-oss:20b (code analysis) and llama3.1:8b-instruct-q6_K (architecture)")
    
    # Test 1: Health Check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{AI_IDE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service is healthy")
            print(f"   Ollama URL: {health_data.get('ollama_url')}")
            print(f"   Vector Storage: {health_data.get('vector_storage_url')}")
            print(f"   Models: {health_data.get('models')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to AI IDE service: {e}")
        print("   Make sure the service is running: make -f Makefile.kubernetes k8s-ai-ide-port-forward")
        return False
    
    # Test 2: List Models
    print("\n2. Available Models:")
    try:
        response = requests.get(f"{AI_IDE_URL}/api/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            if 'models' in models_data:
                print("✅ Available models:")
                for model in models_data['models']:
                    print(f"   - {model}")
            else:
                print("❌ No models found")
        else:
            print(f"❌ Failed to get models: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting models: {e}")
    
    # Test 3: Code Analysis
    print("\n3. Code Analysis Test:")
    sample_code = """
def calculate_portfolio_value(positions):
    total = 0
    for position in positions:
        total += position["quantity"] * position["price"]
    return total
"""
    
    try:
        response = requests.post(
            f"{AI_IDE_URL}/api/analyze-code",
            json={
                "code": sample_code,
                "file_path": "src/portfolio/calculator.py",
                "analysis_type": "optimization"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            analysis_data = response.json()
            print(f"✅ Code analysis completed")
            print(f"   Confidence: {analysis_data.get('confidence', 0):.2f}")
            print(f"   Response length: {len(analysis_data.get('response', ''))}")
            print(f"   Suggestions: {len(analysis_data.get('suggestions', []))}")
            
            # Show first suggestion
            if analysis_data.get('suggestions'):
                print(f"   First suggestion: {analysis_data['suggestions'][0][:100]}...")
        else:
            print(f"❌ Code analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in code analysis: {e}")
    
    # Test 4: Architecture Query
    print("\n4. Architecture Query Test:")
    try:
        response = requests.post(
            f"{AI_IDE_URL}/api/query-architecture",
            json={
                "question": "How does our trading system handle database connections?",
                "include_code_examples": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            arch_data = response.json()
            print(f"✅ Architecture query completed")
            print(f"   Confidence: {arch_data.get('confidence', 0):.2f}")
            print(f"   Sources found: {len(arch_data.get('sources', []))}")
            print(f"   Response length: {len(arch_data.get('response', ''))}")
            
            # Show first part of response
            response_text = arch_data.get('response', '')
            if response_text:
                print(f"   Response preview: {response_text[:200]}...")
        else:
            print(f"❌ Architecture query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in architecture query: {e}")
    
    # Test 5: Code Generation
    print("\n5. Code Generation Test:")
    try:
        response = requests.post(
            f"{AI_IDE_URL}/api/generate-code",
            json={
                "prompt": "Create a function to calculate moving averages for stock data",
                "file_path": "src/indicators/moving_average.py",
                "language": "python"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            gen_data = response.json()
            print(f"✅ Code generation completed")
            print(f"   Confidence: {gen_data.get('confidence', 0):.2f}")
            print(f"   Response length: {len(gen_data.get('response', ''))}")
            
            # Show generated code
            generated_code = gen_data.get('response', '')
            if generated_code:
                print(f"   Generated code preview: {generated_code[:200]}...")
        else:
            print(f"❌ Code generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in code generation: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 AI IDE Integration Test Complete!")
    return True

def test_ollama_directly():
    """Test Ollama directly"""
    print("\n🤖 Testing Ollama Directly")
    print("=" * 30)
    
    # Test Ollama health
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            print("✅ Ollama is running")
            if 'models' in models_data and models_data['models']:
                print("Available models:")
                for model in models_data['models']:
                    print(f"   - {model['name']}")
            else:
                print("❌ No models found in Ollama")
        else:
            print(f"❌ Ollama health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")

def demonstrate_cursor_integration():
    """Demonstrate how to use with Cursor IDE"""
    print("\n🎯 Cursor IDE Integration Examples")
    print("=" * 40)
    
    print("""
To use this AI IDE integration with Cursor:

1. **Direct API Usage:**
   - Use the API endpoints in your code
   - Integrate with Cursor's extension system
   - Create custom commands

2. **Chat Integration:**
   - Ask architecture questions in Cursor's chat
   - Use context from your codebase
   - Get intelligent code suggestions

3. **Code Analysis:**
   - Right-click on code → "Analyze with AI"
   - Get architecture-aware suggestions
   - Understand code patterns

4. **Architecture Questions:**
   - "How does our trading system work?"
   - "What's the best way to add a new service?"
   - "How do I debug Kubernetes issues?"

5. **Code Generation:**
   - Ask for code generation with context
   - Get examples from your architecture
   - Follow your project patterns

Example Cursor Chat Questions:
- "How do I add a new trading strategy to our system?"
- "What's the architecture of our Kubernetes deployment?"
- "How do our services communicate with each other?"
- "What monitoring tools do we use?"
- "How do I debug a pod that's in CrashLoopBackOff?"
""")

def main():
    """Main test function"""
    print("🧠 AI IDE Integration Test Suite")
    print("=" * 50)
    
    # Test Ollama first
    test_ollama_directly()
    
    # Test AI IDE service
    if test_ai_ide_service():
        demonstrate_cursor_integration()
    
    print("\n🚀 Next Steps:")
    print("1. Open Cursor IDE")
    print("2. Use the AI IDE service at http://localhost:11050")
    print("3. Ask architecture questions in chat")
    print("4. Use API endpoints for code analysis")
    print("5. Read AI_IDE_INTEGRATION_GUIDE.md for detailed usage")

if __name__ == "__main__":
    main()
