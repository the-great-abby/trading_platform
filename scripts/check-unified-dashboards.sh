#!/bin/bash

# Unified Dashboard Status Check Script
# This script checks the status of unified dashboards and identifies issues

echo "🔍 Unified Dashboard Status Check"
echo "=================================="

# Check if unified dashboard pods are running
echo "📊 Pod Status:"
kubectl get pods -n trading-system | grep unified

echo ""
echo "🌐 Service Status:"
kubectl get services -n trading-system | grep unified

echo ""
echo "🔗 Port Forwarding Status:"
ps aux | grep "kubectl port-forward" | grep unified

echo ""
echo "🧪 Health Check Tests:"

# Test unified trading dashboard
echo "Testing Unified Trading Dashboard (11114)..."
if curl -s http://localhost:11114/health > /dev/null; then
    echo "✅ Unified Trading Dashboard: HEALTHY"
else
    echo "❌ Unified Trading Dashboard: UNHEALTHY"
fi

# Test unified analytics dashboard
echo "Testing Unified Analytics Dashboard (11115)..."
if curl -s http://localhost:11115/health > /dev/null; then
    echo "✅ Unified Analytics Dashboard: HEALTHY"
else
    echo "❌ Unified Analytics Dashboard: UNHEALTHY"
fi

# Test unified news dashboard
echo "Testing Unified News Dashboard (11116)..."
if curl -s http://localhost:11116/health > /dev/null; then
    echo "✅ Unified News Dashboard: HEALTHY"
else
    echo "❌ Unified News Dashboard: UNHEALTHY"
fi

echo ""
echo "🔍 Functionality Tests:"

# Test database integration (if implemented)
echo "Testing Database Integration..."
if curl -s http://localhost:11114/api/portfolio/summary > /dev/null 2>&1; then
    echo "✅ Database Integration: WORKING"
else
    echo "❌ Database Integration: MISSING"
fi

# Test RSS feed generation (if implemented)
echo "Testing RSS Feed Generation..."
if curl -s http://localhost:11116/api/rss/trades > /dev/null 2>&1; then
    echo "✅ RSS Feed Generation: WORKING"
else
    echo "❌ RSS Feed Generation: MISSING"
fi

# Test strategy events (if implemented)
echo "Testing Strategy Events..."
if curl -s http://localhost:11114/api/strategy/events > /dev/null 2>&1; then
    echo "✅ Strategy Events: WORKING"
else
    echo "❌ Strategy Events: MISSING"
fi

echo ""
echo "📈 Resource Usage:"
kubectl top pods -n trading-system | grep unified

echo ""
echo "🚨 Known Issues:"
echo "1. Database Integration: Missing direct PostgreSQL connections"
echo "2. RSS Feed Generation: Missing RSS XML generation"
echo "3. Portfolio Management: No real portfolio data integration"
echo "4. Strategy Event Tracking: Missing strategy event system"
echo "5. Resource Allocation: May need increased resources"

echo ""
echo "📋 Next Steps:"
echo "1. Implement database integration in unified dashboards"
echo "2. Add RSS feed generation to unified news dashboard"
echo "3. Implement strategy event tracking in unified trading dashboard"
echo "4. Update resource allocations for better performance"
echo "5. Test all functionality thoroughly"

echo ""
echo "📚 Documentation:"
echo "See docs/UNIFIED_DASHBOARD_MIGRATION_GUIDE.md for detailed implementation guide" 