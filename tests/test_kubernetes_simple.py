#!/usr/bin/env python3
"""
Simple Kubernetes Test - No external dependencies
Tests basic Kubernetes cluster connectivity and configuration
"""

import subprocess
import json
import sys

def run_kubectl_command(command, namespace="trading-system"):
    """Run a kubectl command and return JSON output"""
    try:
        result = subprocess.run(
            f"kubectl {command} -n {namespace} -o json",
            shell=True, capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Kubectl command failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse kubectl output: {e}")
        return None

def test_namespace_exists():
    """Test that the trading-system namespace exists"""
    print("🔍 Testing namespace existence...")
    try:
        result = subprocess.run(
            "kubectl get namespace trading-system",
            shell=True, capture_output=True, text=True, check=True
        )
        if "trading-system" in result.stdout:
            print("✅ Namespace trading-system exists")
            return True
        else:
            print("❌ Namespace trading-system not found")
            return False
    except subprocess.CmdProcessError:
        print("❌ Cannot access namespace trading-system")
        return False

def test_pods_status():
    """Test that pods are running"""
    print("🔍 Testing pod status...")
    pods = run_kubectl_command("get pods")
    if not pods:
        return False
    
    running_pods = 0
    total_pods = len(pods["items"])
    
    for pod in pods["items"]:
        status = pod["status"]["phase"]
        if status == "Running":
            running_pods += 1
        else:
            print(f"⚠️  Pod {pod['metadata']['name']} status: {status}")
    
    print(f"✅ {running_pods}/{total_pods} pods are running")
    return running_pods > 0

def test_services_status():
    """Test that services exist"""
    print("🔍 Testing services...")
    services = run_kubectl_command("get services")
    if not services:
        return False
    
    total_services = len(services["items"])
    print(f"✅ Found {total_services} services")
    
    # Check for key services
    key_services = ["unified-analytics-dashboard", "unified-trading-dashboard", "unified-news-dashboard"]
    for service_name in key_services:
        found = any(s["metadata"]["name"] == service_name for s in services["items"])
        if found:
            print(f"✅ Service {service_name} exists")
        else:
            print(f"⚠️  Service {service_name} not found")
    
    return True

def test_deployments_status():
    """Test that deployments are available"""
    print("🔍 Testing deployments...")
    deployments = run_kubectl_command("get deployments")
    if not deployments:
        return False
    
    available_deployments = 0
    total_deployments = len(deployments["items"])
    
    for deployment in deployments["items"]:
        conditions = deployment["status"].get("conditions", [])
        available_condition = next((c for c in conditions if c["type"] == "Available"), None)
        
        if available_condition and available_condition["status"] == "True":
            available_deployments += 1
        else:
            print(f"⚠️  Deployment {deployment['metadata']['name']} not available")
    
    print(f"✅ {available_deployments}/{total_deployments} deployments are available")
    return available_deployments > 0

def test_port_forwards():
    """Test current port forwarding status"""
    print("🔍 Testing port forwarding status...")
    
    # Check for existing port forwards
    try:
        result = subprocess.run(
            "ps aux | grep 'kubectl port-forward' | grep -v grep",
            shell=True, capture_output=True, text=True
        )
        
        if result.stdout.strip():
            print("📡 Active port forwards found:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"   {line}")
        else:
            print("⚠️  No active port forwards found")
        
        # Check specific ports
        ports_to_check = [11113, 11114, 11115, 11044]
        for port in ports_to_check:
            try:
                result = subprocess.run(
                    f"lsof -i :{port}",
                    shell=True, capture_output=True, text=True
                )
                if result.stdout.strip():
                    print(f"✅ Port {port} is in use")
                else:
                    print(f"❌ Port {port} is not in use")
            except:
                print(f"❌ Could not check port {port}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking port forwards: {e}")
        return False

def test_service_connectivity():
    """Test basic service connectivity"""
    print("🔍 Testing service connectivity...")
    
    # Try to get service endpoints
    services = run_kubectl_command("get endpoints")
    if not services:
        return False
    
    connected_services = 0
    total_services = len(services["items"])
    
    for service in services["items"]:
        subsets = service["subsets"]
        if subsets and len(subsets) > 0:
            addresses = subsets[0].get("addresses", [])
            if addresses:
                connected_services += 1
            else:
                print(f"⚠️  Service {service['metadata']['name']} has no endpoints")
        else:
            print(f"⚠️  Service {service['metadata']['name']} has no subsets")
    
    print(f"✅ {connected_services}/{total_services} services have endpoints")
    return connected_services > 0

def main():
    """Run all tests"""
    print("🧪 Kubernetes Simple Test Suite")
    print("================================")
    print()
    
    tests = [
        ("Namespace Existence", test_namespace_exists),
        ("Pod Status", test_pods_status),
        ("Service Status", test_services_status),
        ("Deployment Status", test_deployments_status),
        ("Port Forwarding", test_port_forwards),
        ("Service Connectivity", test_service_connectivity),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        
        print()
    
    print("📊 Test Summary")
    print("===============")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())



