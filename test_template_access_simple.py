#!/usr/bin/env python3
"""
Test template access for unified analytics dashboard (simple version)
"""

import sys
import os
import json
import urllib.request
import urllib.parse

def make_request(url, method="GET", data=None, timeout=5):
    """Make HTTP request using urllib"""
    try:
        if method == "POST" and data:
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

def test_template_access():
    """Test if templates are accessible"""
    print("🔍 Testing Template Access...")
    
    # Test the correct port where unified-analytics-dashboard is running
    port = 11155
    
    print(f"\n📡 Testing port {port}...")
    
    try:
        # Test health endpoint
        status, response_text = make_request(f"http://localhost:{port}/health")
        if status == 200:
            print(f"✅ Health endpoint working on port {port}")
            data = json.loads(response_text)
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            
            # Test template pages
            pages = ["/", "/ai-stock", "/central-hub", "/data-pipeline"]
            for page in pages:
                try:
                    status, response_text = make_request(f"http://localhost:{port}{page}")
                    if status == 200:
                        print(f"✅ {page} page working on port {port}")
                        content = response_text[:100]  # First 100 chars
                        if "html" in content.lower():
                            print(f"   ✅ Returns HTML content")
                        else:
                            print(f"   ⚠️ Content: {content}")
                    elif status == 500:
                        print(f"❌ {page} page returns 500 error on port {port}")
                        print(f"   Error content: {response_text[:200]}")
                    else:
                        print(f"❌ {page} page returns {status} on port {port}")
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
                        status, response_text = make_request(f"http://localhost:{port}{endpoint}", 
                                                          method="POST", data=data)
                    else:
                        # GET request for others
                        status, response_text = make_request(f"http://localhost:{port}{endpoint}")
                    
                    if status == 200:
                        print(f"✅ {endpoint} API working on port {port}")
                        try:
                            data = json.loads(response_text)
                            if isinstance(data, dict) and len(data) > 0:
                                print(f"   Response keys: {list(data.keys())}")
                        except:
                            print(f"   Response: {response_text[:100]}")
                    else:
                        print(f"❌ {endpoint} API returns {status} on port {port}")
                except Exception as e:
                    print(f"❌ {endpoint} API error on port {port}: {e}")
            
        else:
            print(f"❌ Health endpoint failed on port {port}: {status}")
            
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