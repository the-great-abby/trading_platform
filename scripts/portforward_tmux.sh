#!/bin/bash

# Script to launch all Kubernetes port-forwards in a tmux session
# Usage: ./scripts/portforward_tmux.sh

SESSION="k8s-portforwards"
NAMESPACE="trading-system"

# List of services and ports (only services with running pods)
SERVICES=(
  "central-hub-dashboard 11080 80"
  "health-dashboard 11083 80"
  "performance-dashboard 11084 80"
  "rss-dashboard 11085 80"
  "trading-dashboard-service 11082 8000"
  "trading-ultra-service 11099 80"
)

# Start tmux session if it doesn't exist
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n "portforward"
fi

# For each service, create a window running the port-forward
for entry in "${SERVICES[@]}"; do
  set -- $entry
  NAME="$1"
  LOCAL_PORT="$2"
  REMOTE_PORT="$3"
  WINDOW_NAME="$NAME"

  # Check if window exists
  if ! tmux list-windows -t "$SESSION" | grep -q "^$WINDOW_NAME"; then
    echo "Creating window for $NAME..."
    tmux new-window -t "$SESSION" -n "$WINDOW_NAME" \
      "echo 'Starting port-forward for $NAME ($LOCAL_PORT -> $REMOTE_PORT)...'; \
      kubectl port-forward service/$NAME $LOCAL_PORT:$REMOTE_PORT -n $NAMESPACE || echo 'Failed to start port-forward for $NAME'"
  else
    echo "Window $WINDOW_NAME already exists in tmux session $SESSION. Skipping."
  fi

done

# Kill the default window if it's still there and unused
if tmux list-windows -t "$SESSION" | grep -q "portforward"; then
  if [ $(tmux list-windows -t "$SESSION" | grep -c "portforward") -eq 1 ]; then
    tmux kill-window -t "$SESSION":portforward
  fi
fi

# Print instructions
cat <<EOF

All port-forwards are running in tmux session: $SESSION
To attach: tmux attach-session -t $SESSION
To detach: Press Ctrl+b then d
To kill all port-forwards: tmux kill-session -t $SESSION
EOF 