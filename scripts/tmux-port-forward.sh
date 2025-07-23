#!/bin/bash

# Tmux Port Forward Management Script
SESSION_NAME="trading-pf"
SERVICE_NAME="trading-ultra-service"
NAMESPACE="trading-system"
LOCAL_PORT="11100"
REMOTE_PORT="80"

case "$1" in
    start)
        echo "🚀 Starting tmux port forward session..."
        
        # Create new session if it doesn't exist
        if ! tmux has-session -t $SESSION_NAME 2>/dev/null; then
            tmux new-session -d -s $SESSION_NAME
            tmux send-keys -t $SESSION_NAME "cd $(pwd)" Enter
        fi
        
        # Start persistent port forwarding
        tmux send-keys -t $SESSION_NAME "echo '🔄 Starting persistent port forward for $SERVICE_NAME...'" Enter
        tmux send-keys -t $SESSION_NAME "while true; do echo '📡 Port forwarding $LOCAL_PORT -> $SERVICE_NAME:$REMOTE_PORT'; kubectl port-forward service/$SERVICE_NAME $LOCAL_PORT:$REMOTE_PORT -n $NAMESPACE --address=0.0.0.0; echo '⚠️ Port forward died, restarting in 5 seconds...'; sleep 5; done" Enter
        
        echo "✅ Tmux session '$SESSION_NAME' started"
        echo "🌐 Dashboard: http://localhost:$LOCAL_PORT"
        echo "🔑 VAPID API: http://localhost:$LOCAL_PORT/api/notifications/vapid-public-key"
        echo "📋 Attach to session: tmux attach -t $SESSION_NAME"
        ;;
        
    stop)
        echo "🛑 Stopping tmux port forward session..."
        tmux kill-session -t $SESSION_NAME 2>/dev/null
        echo "✅ Session '$SESSION_NAME' stopped"
        ;;
        
    restart)
        echo "🔄 Restarting tmux port forward session..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if tmux has-session -t $SESSION_NAME 2>/dev/null; then
            echo "✅ Session '$SESSION_NAME' is running"
            echo "📋 Attach: tmux attach -t $SESSION_NAME"
            echo "🛑 Stop: $0 stop"
        else
            echo "❌ Session '$SESSION_NAME' is not running"
            echo "🚀 Start: $0 start"
        fi
        ;;
        
    attach)
        echo "📋 Attaching to tmux session..."
        tmux attach -t $SESSION_NAME
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|attach}"
        echo ""
        echo "Commands:"
        echo "  start   - Start persistent port forwarding in tmux"
        echo "  stop    - Stop the tmux session"
        echo "  restart - Restart the tmux session"
        echo "  status  - Check if session is running"
        echo "  attach  - Attach to the tmux session"
        echo ""
        echo "Port Forward Details:"
        echo "  Service: $SERVICE_NAME"
        echo "  Local Port: $LOCAL_PORT"
        echo "  Remote Port: $REMOTE_PORT"
        echo "  Namespace: $NAMESPACE"
        ;;
esac 