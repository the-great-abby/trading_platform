# Always Applied Workspace Rules

These rules are automatically applied to all interactions in this workspace.

## 1. Grafana ConfigMap Consolidation Rule

### Overview
This rule ensures we maintain a single, consolidated Grafana ConfigMap to prevent conflicts and dashboard breakage. Multiple ConfigMaps with different names cause Grafana to fail to load dashboards properly.

### Current Problem
Multiple Grafana ConfigMaps exist with different names:
- `grafana-dashboards` (monitoring/)
- `grafana-dashboards` (k8s/)
- `grafana-dashboards-all-fixed`
- `grafana-dashboards-complete`
- `grafana-dashboards-fixed-v2`
- `grafana-dashboards-fixed-v3`

### Single ConfigMap Standard

#### Primary ConfigMap
**File**: `monitoring/grafana-dashboards-configmap.yaml`
**Name**: `grafana-dashboards`
**Namespace**: `trading-system`

#### Consolidation Process
When creating or updating Grafana dashboards:

1. **Use Only the Primary ConfigMap**
   - Always update `monitoring/grafana-dashboards-configmap.yaml`
   - Never create new ConfigMaps with different names
   - Never use names like `grafana-dashboards-fixed-v2` or `grafana-dashboards-complete`

2. **Clean Up Existing ConfigMaps**
   ```bash
   # Remove conflicting ConfigMaps
   kubectl delete configmap grafana-dashboards-all-fixed -n trading-system
   kubectl delete configmap grafana-dashboards-complete -n trading-system
   kubectl delete configmap grafana-dashboards-fixed-v2 -n trading-system
   kubectl delete configmap grafana-dashboards-fixed-v3 -n trading-system
   ```

3. **Update Process**
   - Edit `monitoring/grafana-dashboards-configmap.yaml`
   - Apply with: `kubectl apply -f monitoring/grafana-dashboards-configmap.yaml`
   - Restart Grafana: `kubectl rollout restart deployment/grafana -n trading-system`

### Dashboard Management

#### Adding New Dashboards
1. Add dashboard JSON to `monitoring/grafana/dashboards/`
2. Update `monitoring/grafana-dashboards-configmap.yaml` to include the new dashboard
3. Apply the ConfigMap
4. Restart Grafana deployment

#### Updating Existing Dashboards
1. Update the dashboard JSON in `monitoring/grafana/dashboards/`
2. Update the ConfigMap to reflect changes
3. Apply and restart

### Error Prevention

#### What NOT to Do
- ❌ Create new ConfigMaps with different names
- ❌ Use names like `grafana-dashboards-fixed-v2`
- ❌ Have multiple ConfigMaps in different namespaces
- ❌ Apply ConfigMaps without restarting Grafana

#### What TO Do
- ✅ Always use `grafana-dashboards` as the ConfigMap name
- ✅ Keep all dashboard definitions in `monitoring/grafana-dashboards-configmap.yaml`
- ✅ Restart Grafana after ConfigMap changes
- ✅ Test dashboard loading after updates

### Validation Commands
```bash
# Check current ConfigMaps
kubectl get configmaps -n trading-system | grep grafana

# Verify Grafana is using the correct ConfigMap
kubectl describe deployment grafana -n trading-system | grep -A 5 -B 5 grafana-dashboards

# Test dashboard loading
curl -s -u admin:admin http://localhost:11044/api/search | jq '.[].title'
```

### Troubleshooting
If dashboards don't load:
1. Check ConfigMap exists: `kubectl get configmap grafana-dashboards -n trading-system`
2. Verify ConfigMap content: `kubectl describe configmap grafana-dashboards -n trading-system`
3. Restart Grafana: `kubectl rollout restart deployment/grafana -n trading-system`
4. Check Grafana logs: `kubectl logs deployment/grafana -n trading-system`

## 2. Port Forwarding Command Rule

### Overview
This rule automatically checks and restarts port forwarding when the user uses specific command phrases. It ensures the trading system dashboards are always accessible.

### Trigger Phrases
When the user says any of these phrases, automatically check and restart port forwarding:
- "Shields are down!"
- "Forward the ports!"
- "Ports are down!"
- "Check the ports!"
- "Restart port forwarding!"
- "Port forwarding failed!"

### Automatic Grafana Update Actions
When Grafana dashboards are updated or Grafana is restarted, automatically restart port forwarding:

1. **After Grafana ConfigMap Updates**
   - When `kubectl apply -f monitoring/grafana-dashboards-configmap.yaml` is run
   - When `kubectl rollout restart deployment/grafana` is run
   - Automatically restart Grafana port forward after 5 seconds

2. **After Dashboard Updates**
   - When any Grafana dashboard is modified
   - When Grafana deployment is restarted
   - Ensure port forwarding is restored

### Automatic Port Forwarding Restart
After any Grafana-related operations, automatically:
```bash
# Wait for Grafana to restart
sleep 5

# Restart Grafana port forward
pkill -f "kubectl port-forward.*grafana"
kubectl port-forward service/grafana 11044:3000 -n trading-system &

# Test Grafana health
sleep 2
curl -s http://localhost:11044/api/health
```

### Automatic Actions
When triggered, perform these steps in order:

1. **Check Current Port Forwards**
   ```bash
   ps aux | grep "kubectl port-forward" | grep -v grep
   ```

2. **Stop All Existing Port Forwards**
   ```bash
   pkill -f "kubectl port-forward"
   ```

3. **Wait for Cleanup**
   ```bash
   sleep 2
   ```

4. **Check Port Availability**
   ```bash
   lsof -i :11113 && lsof -i :11114 && lsof -i :11115 && lsof -i :11044
   ```

5. **Restart Essential Port Forwards**
   ```bash
   # Unified Analytics Dashboard
   kubectl port-forward service/unified-analytics-dashboard 11114:80 -n trading-system &
   
   # Unified Trading Dashboard  
   kubectl port-forward service/unified-trading-dashboard 11115:80 -n trading-system &
   
   # Unified News Dashboard
   kubectl port-forward service/unified-news-dashboard 11113:80 -n trading-system &
   
   # Grafana Monitoring Dashboard
   kubectl port-forward service/grafana 11044:3000 -n trading-system &
   ```

6. **Wait for Startup**
   ```bash
   sleep 3
   ```

7. **Test All Ports**
   ```bash
   curl -s http://localhost:11113/health
   curl -s http://localhost:11114/health  
   curl -s http://localhost:11115/health
   curl -s http://localhost:11044/api/health
   ```

8. **Report Status**
   - Show which ports are working
   - List any failed ports
   - Provide URLs for working dashboards

### Dashboard URLs
- **Unified Analytics Dashboard**: http://localhost:11114/
- **Unified Trading Dashboard**: http://localhost:11115/
- **Unified News Dashboard**: http://localhost:11113/
- **Grafana Monitoring Dashboard**: http://localhost:11044/

### Error Handling
- If a port is already in use, kill existing processes first
- If a service is not running, report which service needs to be started
- If health checks fail, provide troubleshooting steps

### Success Message
When all ports are working:
```
✅ All shields are up! Port forwarding restored:
- Analytics Dashboard: http://localhost:11114/ ✅
- Trading Dashboard: http://localhost:11115/ ✅  
- News Dashboard: http://localhost:11113/ ✅
- Grafana Monitoring: http://localhost:11044/ ✅

🔄 Automatic Updates: Port forwarding will be automatically restarted after Grafana updates
```

### Failure Message
When some ports fail:
```
⚠️ Some shields are still down:
- Working: [list working ports]
- Failed: [list failed ports]
- Troubleshooting: [next steps]
```

## 3. LLM Proxy Service Decommissioned Rule

### Overview
The internal LLM proxy service has been decommissioned and should not be used. All LLM-related functionality should reference the external resource on port 12001.

### Current Status
- ❌ **Internal LLM Proxy Service**: Decommissioned (not running)
- ✅ **External LLM Resource**: Available on port 12001
- 🔄 **Migration Required**: Update all services to use external endpoint

### External LLM Resource
**URL**: `http://localhost:12001` (local development) or `http://host.docker.internal:12001` (Docker containers)

### Services Affected
The following services need to use the external LLM resource:

1. **Unified Analytics Dashboard** - `services/unified-analytics-dashboard/main.py`
2. **Kubernetes RAG Chat** - `services/kubernetes-rag-chat/main.py`
3. **AI Stock Dashboard** - `services/ai-stock-dashboard/main.py`
4. **Other AI Services** - AI Analysis Service, AI Decision Engine, Trading Ultra Service, Vector Database Service

### Environment Variable Configuration
```bash
# For Local Development
export LLM_PROXY_URL=http://localhost:12001

# For Docker Containers
export LLM_PROXY_URL=http://host.docker.internal:12001

# For Kubernetes
env:
- name: LLM_PROXY_URL
  value: "http://host.docker.internal:12001"
```

### API Endpoints
The external LLM resource provides these endpoints:
- **Generate**: `POST /api/generate`
- **Chat**: `POST /api/chat`
- **High Priority**: `POST /api/high-priority/chat`
- **Embed**: `POST /api/embed`
- **Health**: `GET /api/health`
- **Status**: `GET /api/status/{request_id}`

### Migration Steps
1. **Update Environment Variables** to use external resource
2. **Update Kubernetes Manifests** to reference external endpoint
3. **Remove Internal Service** references

### Compliance
- ✅ **All new services** must use external LLM resource
- ✅ **Existing services** must be migrated to external resource
- ❌ **No new services** should reference internal LLM proxy
- ❌ **No fallback** to internal LLM proxy allowed

### Testing External LLM Resource
```bash
# Health Check
curl -s http://localhost:12001/api/health

# Test Generation
curl -X POST http://localhost:12001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

This rule ensures consistent use of the external LLM resource and prevents confusion with the decommissioned internal service.

---

These rules ensure consistent, reliable operation of the trading system infrastructure and prevent common configuration errors.

