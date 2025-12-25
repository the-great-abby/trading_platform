#!/bin/bash
# Quick Options Status Check
echo "📊 Quick Options Status"
echo "======================================"
make -f makefiles/Makefile.live-trading live-trading-options-status 2>&1 | tail -20
