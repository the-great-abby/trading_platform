#!/usr/bin/env python3
"""
Test template access for unified analytics dashboard
"""

import sys
import os
import requests
import json

def test_template_access():
    """Test if templates are accessible"""
    print("🔍 Testing Template Access...")
    
    # Test different ports
    ports = [11115, 11125, 11135]
    
    for port in ports:
        print(f"\n📡 Testing port {port}...")
        
        try:
            # Test health endpoint
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Health endpoint working on port {port}")
                data = response.json()
                print(f"   Service: {data.get('service', 'Unknown')}")
                print(f"   Status: {data.get('status', 'Unknown')}")
                
                # Test template pages
                pages = ["/", "/ai-stock", "/central-hub", "/data-pipeline"]
                for page in pages:
                    try:
                        response = requests.get(f"http://localhost:{port}{page}", timeout=5)
                        if response.status_code == 200:
                            print(f"✅ {page} page working on port {port}")
                            content = response.text[:100]  # First 100 chars
                            if "html" in content.lower():
                                print(f"   ✅ Returns HTML content")
                            else:
                                print(f"   ⚠️ Content: {content}")
                        elif response.status_code == 500:
                            print(f"❌ {page} page returns 500 error on port {port}")
                            # Try to get error details
                            try:
                                error_response = requests.get(f"http://localhost:{port}{page}", timeout=5)
                                print(f"   Error content: {error_response.text[:200]}")
                            except:
                                pass
                        else:
                            print(f"❌ {page} page returns {response.status_code} on port {port}")
                    except Exception as e:
                        print(f"❌ {page} page error on port {port}: {e}")
                
                # Test API endpoints
                api_endpoints = [
                    "/api/analyze",
                    "/api/pipeline/status", 
                    "/api/central-hub/data",
                    "/api/symbols"
                ]
                
                for endpoint in api_endpoints:
                    try:
                        if endpoint == "/api/analyze":
                            # POST request for analyze
                            data = {
                                "symbol": "AAPL",
                                "current_price": 150.0,
                                "include_news": True,
                                "include_technical": True,
                                "include_sentiment": True
                            }
                            response = requests.post(f"http://localhost:{port}{endpoint}", 
                                                   json=data, timeout=5)
                        else:
                            # GET request for others
                            response = requests.get(f"http://localhost:{port}{endpoint}", timeout=5)
                        
                        if response.status_code == 200:
                            print(f"✅ {endpoint} API working on port {port}")
                            try:
                                data = response.json()
                                if isinstance(data, dict) and len(data) > 0:
                                    print(f"   Response keys: {list(data.keys())}")
                            except:
                                print(f"   Response: {response.text[:100]}")
                        else:
                            print(f"❌ {endpoint} API returns {response.status_code} on port {port}")
                    except Exception as e:
                        print(f"❌ {endpoint} API error on port {port}: {e}")
                
                break  # Found working port
                
            else:
                print(f"❌ Health endpoint failed on port {port}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Port {port} not accessible: {e}")
    
    print("\n📊 Template Access Summary:")
    print("   • Health endpoints should be working")
    print("   • Template pages should return HTML content")
    print("   • API endpoints should return JSON data")
    print("   • 500 errors indicate template issues")
    print("   • Connection errors indicate port forwarding issues")

if __name__ == "__main__":
    test_template_access() 