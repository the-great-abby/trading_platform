#!/bin/bash

# AI Stock Dashboard Container Management Script

DASHBOARD_NAME="ai-stock-dashboard"
DASHBOARD_PORT="11007"
DASHBOARD_URL="http://localhost:11007"

case "$1" in
    "start")
        echo "🚀 Starting AI Stock Dashboard..."
        
        # Check if container already exists
        if docker ps -a --format "table {{.Names}}" | grep -q "^${DASHBOARD_NAME}$"; then
            echo "📦 Container exists, removing old version..."
            docker stop ${DASHBOARD_NAME} 2>/dev/null
            docker rm ${DASHBOARD_NAME} 2>/dev/null
        fi
        
        # Build and start the container
        echo "🔨 Building dashboard container..."
        docker build -t ai-stock-dashboard:latest services/ai-stock-dashboard/
        
        echo "🚀 Starting container..."
        docker run -d --name ${DASHBOARD_NAME} -p ${DASHBOARD_PORT}:8000 ai-stock-dashboard:latest
        
        echo "⏳ Waiting for dashboard to start..."
        sleep 5
        
        # Test the dashboard
        if curl -s ${DASHBOARD_URL}/api/health > /dev/null; then
            echo "✅ Dashboard is running!"
            echo "🌐 Open your browser to: ${DASHBOARD_URL}"
            echo ""
            echo "💡 Try analyzing stocks like:"
            echo "   • AAPL at $150.25"
            echo "   • TSLA at $245.80"
            echo "   • NVDA at $850.00"
            echo ""
            echo "⏱️  Expected response times: 2-5 seconds"
        else
            echo "❌ Dashboard failed to start properly"
            exit 1
        fi
        ;;
        
    "stop")
        echo "🛑 Stopping AI Stock Dashboard..."
        docker stop ${DASHBOARD_NAME} 2>/dev/null
        docker rm ${DASHBOARD_NAME} 2>/dev/null
        echo "✅ Dashboard stopped"
        ;;
        
    "restart")
        echo "🔄 Restarting AI Stock Dashboard..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    "status")
        echo "📊 AI Stock Dashboard Status"
        echo "=========================="
        
        if docker ps --format "table {{.Names}}" | grep -q "^${DASHBOARD_NAME}$"; then
            echo "✅ Dashboard is running"
            echo "🌐 URL: ${DASHBOARD_URL}"
            echo "📦 Container: ${DASHBOARD_NAME}"
            echo "🔌 Port: ${DASHBOARD_PORT}"
            
            # Test API
            if curl -s ${DASHBOARD_URL}/api/health > /dev/null; then
                echo "🔗 API: Healthy"
            else
                echo "🔗 API: Unhealthy"
            fi
        else
            echo "❌ Dashboard is not running"
            echo "💡 Run '$0 start' to start the dashboard"
        fi
        ;;
        
    "logs")
        echo "📋 Dashboard Logs"
        echo "================"
        docker logs ${DASHBOARD_NAME}
        ;;
        
    "test")
        echo "🧪 Testing Dashboard API..."
        
        if curl -s ${DASHBOARD_URL}/api/health > /dev/null; then
            echo "✅ Health check passed"
            
            echo "📊 Testing stock analysis..."
            response=$(curl -s -X POST ${DASHBOARD_URL}/api/analyze \
                -H "Content-Type: application/json" \
                -d '{"symbol": "AAPL", "current_price": 150.25, "include_news": true, "include_technical": true, "include_sentiment": true}')
            
            if echo "$response" | grep -q "recommendation"; then
                echo "✅ Analysis test passed"
                echo "📈 Sample result:"
                echo "$response" | jq '.symbol, .recommendation, .confidence, .risk_level' 2>/dev/null || echo "$response"
            else
                echo "❌ Analysis test failed"
                echo "Response: $response"
            fi
        else
            echo "❌ Health check failed"
        fi
        ;;
        
    *)
        echo "🤖 AI Stock Dashboard Management"
        echo "=============================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Build and start the dashboard"
        echo "  stop    - Stop the dashboard"
        echo "  restart - Restart the dashboard"
        echo "  status  - Show dashboard status"
        echo "  logs    - Show dashboard logs"
        echo "  test    - Test dashboard functionality"
        echo ""
        echo "🌐 Dashboard URL: ${DASHBOARD_URL}"
        echo "⏱️  Expected response times: 2-5 seconds"
        ;;
esac 