#!/usr/bin/env python3
import json
import subprocess

def fix_dashboard_format(dashboard_json):
    data = json.loads(dashboard_json)
    if 'dashboard' in data:
        return json.dumps(data['dashboard'], indent=2)
    else:
        return dashboard_json

# Get the working ConfigMap
result = subprocess.run([
    'kubectl', 'get', 'configmap', 'grafana-dashboards-working', 
    '-n', 'trading-system', '-o', 'json'
], capture_output=True, text=True)

configmap = json.loads(result.stdout)

# Fix each dashboard
for key, value in configmap['data'].items():
    if key.endswith('.json'):
        try:
            fixed_json = fix_dashboard_format(value)
            configmap['data'][key] = fixed_json
            print(f"Fixed {key}")
        except Exception as e:
            print(f"Error fixing {key}: {e}")

# Create new ConfigMap
configmap['metadata']['name'] = 'grafana-dashboards-fixed'
if 'annotations' in configmap['metadata']:
    del configmap['metadata']['annotations']
if 'resourceVersion' in configmap['metadata']:
    del configmap['metadata']['resourceVersion']
if 'uid' in configmap['metadata']:
    del configmap['metadata']['uid']
if 'creationTimestamp' in configmap['metadata']:
    del configmap['metadata']['creationTimestamp']

# Apply the new ConfigMap
result = subprocess.run([
    'kubectl', 'apply', '-f', '-'
], input=json.dumps(configmap), text=True, capture_output=True)

if result.returncode == 0:
    print("Successfully created fixed ConfigMap: grafana-dashboards-fixed")
else:
    print("Error creating ConfigMap:", result.stderr)
