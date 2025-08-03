#!/usr/bin/env python3
"""
Local AI Stock Dashboard
Run the dashboard locally without Kubernetes
"""

import uvicorn
import os
import sys

# Add the services directory to the path
sys.path.append('services/ai-stock-dashboard')

if __name__ == "__main__":
    print("🚀 Starting AI Stock Dashboard locally...")
    print("📊 Dashboard will be available at: http://localhost:11007")
    print("⏱️  Expected response times: 2-5 seconds")
    print("")
    print("💡 Features:")
    print("   • Interactive stock analysis")
    print("   • AI-powered buy/sell recommendations")
    print("   • Technical analysis with RSI, MACD, Moving Averages")
    print("   • News sentiment analysis")
    print("   • Risk assessment and confidence scoring")
    print("   • Target prices and stop losses")
    print("")
    print("🎯 Try analyzing stocks like: AAPL, TSLA, NVDA, MSFT, GOOGL")
    print("")
    
    # Change to the dashboard directory
    os.chdir('services/ai-stock-dashboard')
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=11007,
        reload=True,
        log_level="info"
    ) 