"""
Backtest Request Service - Web interface for submitting backtest requests
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import subprocess
from datetime import datetime, timedelta
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backtest Request Service", version="1.0.0")

# Configuration
KUBERNETES_NAMESPACE = os.getenv("KUBERNETES_NAMESPACE", "trading-system")

class BacktestRequest(BaseModel):
    """Backtest request model"""
    symbols: List[str]
    strategies: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 1000.0
    risk_profile: str = "moderate"
    use_llm: bool = False
    parallel_execution: bool = True
    database_only: bool = True
    user_email: Optional[str] = None
    enable_notifications: bool = False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "backtest-request-service"}

@app.get("/", response_class=HTMLResponse)
async def backtest_form():
    """Main backtest request form"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Backtest Request Form</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #667eea;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.8;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-item input[type="checkbox"] {
            width: auto;
        }
        
        .submit-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 18px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .preset-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .preset-btn {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .preset-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .preset-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .preset-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Backtest Request Form</h1>
            <p>Configure and submit your trading strategy backtest</p>
        </div>
        
        <div id="alert-container"></div>
        
        <form id="backtest-form">
            <!-- Preset Buttons -->
            <div class="preset-buttons">
                <button type="button" class="preset-btn" onclick="loadPreset('quick')">Quick Test</button>
                <button type="button" class="preset-btn" onclick="loadPreset('comprehensive')">Comprehensive</button>
                <button type="button" class="preset-btn" onclick="loadPreset('options')">Options Strategies</button>
                <button type="button" class="preset-btn" onclick="loadPreset('advanced')">Advanced AI</button>
            </div>
            
            <!-- Symbols -->
            <div class="form-group">
                <label for="symbols">Trading Symbols (comma-separated)</label>
                <input type="text" id="symbols" name="symbols" value="AAPL,GOOGL,MSFT,TSLA,NVDA" required>
            </div>
            
            <!-- Date Range -->
            <div class="form-row">
                <div class="form-group">
                    <label for="start_date">Start Date</label>
                    <input type="date" id="start_date" name="start_date" value="2023-01-01" required>
                </div>
                <div class="form-group">
                    <label for="end_date">End Date</label>
                    <input type="date" id="end_date" name="end_date" value="2025-01-01" required>
                </div>
            </div>
            
            <!-- Capital and Risk -->
            <div class="form-row">
                <div class="form-group">
                    <label for="initial_capital">Initial Capital ($)</label>
                    <input type="number" id="initial_capital" name="initial_capital" value="100000" min="1000" step="1000" required>
                </div>
                <div class="form-group">
                    <label for="risk_profile">Risk Profile</label>
                    <select id="risk_profile" name="risk_profile">
                        <option value="conservative">Conservative</option>
                        <option value="moderate" selected>Moderate</option>
                        <option value="aggressive">Aggressive</option>
                        <option value="extreme">Extreme</option>
                    </select>
                </div>
            </div>
            
            <!-- Strategies -->
            <div class="form-group">
                <label>Strategies</label>
                <div style="margin-bottom: 8px; color: #555; font-size: 0.98em;">
                    <span style="font-weight: 600;">Legend:</span>
                    <span style="color: #28a745;">(No AI)</span> = No LLM/AI required &nbsp;|&nbsp;
                    <span style="color: #fd7e14;">(AI/LLM)</span> = Requires LLM/AI assistance
                    <span title="LLM/AI strategies use large language models for signal generation, filtering, or news/sentiment analysis. Non-AI strategies are pure quant/statistical.">
                        <svg style="vertical-align: middle; margin-left: 4px;" width="16" height="16" fill="#888" viewBox="0 0 16 16"><circle cx="8" cy="8" r="8"/><text x="8" y="12" text-anchor="middle" font-size="10" fill="#fff">i</text></svg>
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
                    <!-- Basic Strategies -->
                    <div class="strategy-category">
                        <h4 style="color: #007bff; margin-bottom: 10px;">📊 Basic Strategies</h4>
                        <div class="checkbox-group">
                            <div class="checkbox-item">
                                <input type="checkbox" id="bollinger_bands" name="strategies" value="BollingerBands" checked>
                                <label for="bollinger_bands">Bollinger Bands <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="rsi" name="strategies" value="RSI" checked>
                                <label for="rsi">RSI <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="macd" name="strategies" value="MACD" checked>
                                <label for="macd">MACD <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="momentum" name="strategies" value="Momentum">
                                <label for="momentum">Momentum <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="mean_reversion" name="strategies" value="MeanReversion">
                                <label for="mean_reversion">Mean Reversion <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="sma_crossover" name="strategies" value="SMACrossover">
                                <label for="sma_crossover">SMA Crossover <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="volatility_breakout" name="strategies" value="VolatilityBreakout">
                                <label for="volatility_breakout">Volatility Breakout <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="ichimoku" name="strategies" value="Ichimoku">
                                <label for="ichimoku">Ichimoku <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="ichimoku_enhanced" name="strategies" value="IchimokuEnhanced">
                                <label for="ichimoku_enhanced">Enhanced Ichimoku <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="adaptive_momentum" name="strategies" value="AdaptiveMomentum">
                                <label for="adaptive_momentum">Adaptive Momentum <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="regime_switching" name="strategies" value="RegimeSwitching">
                                <label for="regime_switching">Regime Switching <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="vwap" name="strategies" value="VWAP">
                                <label for="vwap">VWAP <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="pairs_trading" name="strategies" value="PairsTrading">
                                <label for="pairs_trading">Pairs Trading <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="kalman_filter" name="strategies" value="KalmanFilter">
                                <label for="kalman_filter">Kalman Filter <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="ml_ensemble" name="strategies" value="MLEnsemble">
                                <label for="ml_ensemble">ML Ensemble <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="enhanced_day_trading" name="strategies" value="EnhancedDayTrading">
                                <label for="enhanced_day_trading">Enhanced Day Trading <span title='No LLM/AI required' style='color: #28a745;'>(No AI)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="news_enhanced" name="strategies" value="NewsEnhanced">
                                <label for="news_enhanced">News Enhanced <span title='Requires LLM/AI' style='color: #fd7e14;'>(AI/LLM)</span></label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="social_media_sentiment" name="strategies" value="SocialMediaSentiment">
                                <label for="social_media_sentiment">Social Media Sentiment <span title='Requires LLM/AI' style='color: #fd7e14;'>(AI/LLM)</span></label>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Options Strategies -->
                    <div class="strategy-category">
                        <h4 style="color: #6f42c1; margin-bottom: 10px;">🎯 Options Strategies</h4>
                        <div class="checkbox-group">
                            <div class="checkbox-item">
                                <input type="checkbox" id="greeks_enhanced" name="strategies" value="GreeksEnhanced">
                                <label for="greeks_enhanced">Greeks Enhanced</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="iron_condor" name="strategies" value="IronCondor">
                                <label for="iron_condor">Iron Condor</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="enhanced_iron_condor" name="strategies" value="EnhancedIronCondor">
                                <label for="enhanced_iron_condor">Enhanced Iron Condor</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="cash_secured_put" name="strategies" value="CashSecuredPut">
                                <label for="cash_secured_put">Cash Secured Put</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="covered_call" name="strategies" value="CoveredCall">
                                <label for="covered_call">Covered Call</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="calendar_spread" name="strategies" value="CalendarSpread">
                                <label for="calendar_spread">Calendar Spread</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="butterfly_spread" name="strategies" value="ButterflySpread">
                                <label for="butterfly_spread">Butterfly Spread</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="volatility_strategy" name="strategies" value="VolatilityStrategy">
                                <label for="volatility_strategy">Volatility Strategy</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="earnings_strategy" name="strategies" value="EarningsStrategy">
                                <label for="earnings_strategy">Earnings Strategy</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="straddle" name="strategies" value="Straddle">
                                <label for="straddle">Straddle</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="long_strangle" name="strategies" value="LongStrangle">
                                <label for="long_strangle">Long Strangle</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="short_strangle" name="strategies" value="ShortStrangle">
                                <label for="short_strangle">Short Strangle</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="bullish_diagonal" name="strategies" value="BullishDiagonal">
                                <label for="bullish_diagonal">Bullish Diagonal</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="bearish_diagonal" name="strategies" value="BearishDiagonal">
                                <label for="bearish_diagonal">Bearish Diagonal</label>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Advanced Strategies -->
                    <div class="strategy-category">
                        <h4 style="color: #fd7e14; margin-bottom: 10px;">🚀 Advanced Strategies</h4>
                        <div class="checkbox-group">
                            <div class="checkbox-item">
                                <input type="checkbox" id="trailing_stop" name="strategies" value="TrailingStop">
                                <label for="trailing_stop">Trailing Stop</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="fibonacci" name="strategies" value="Fibonacci">
                                <label for="fibonacci">Fibonacci</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="neural_network" name="strategies" value="NeuralNetwork">
                                <label for="neural_network">Neural Network</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="quantum_momentum" name="strategies" value="QuantumMomentum">
                                <label for="quantum_momentum">Quantum Momentum</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="cross_sectional_momentum" name="strategies" value="CrossSectionalMomentum">
                                <label for="cross_sectional_momentum">Cross Sectional Momentum</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="enhanced_exit" name="strategies" value="EnhancedExit">
                                <label for="enhanced_exit">Enhanced Exit</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="advanced_exit" name="strategies" value="AdvancedExit">
                                <label for="advanced_exit">Advanced Exit</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="portfolio_strategy" name="strategies" value="PortfolioStrategy">
                                <label for="portfolio_strategy">Portfolio Strategy</label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Advanced Options -->
            <div class="form-group">
                <label>Advanced Options</label>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="use_llm" name="use_llm">
                        <label for="use_llm">Use LLM Evaluation</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="parallel_execution" name="parallel_execution" checked>
                        <label for="parallel_execution">Parallel Execution</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="database_only" name="database_only" checked>
                        <label for="database_only">Database Only (No API calls)</label>
                    </div>
                </div>
            </div>
            
            <!-- Email Notifications -->
            <div class="form-group">
                <label>📧 Email Notifications</label>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="enable_notifications" name="enable_notifications">
                        <label for="enable_notifications">Send email when backtest completes</label>
                    </div>
                </div>
                <div class="form-group" id="email-field" style="display: none;">
                    <label for="user_email">Email Address</label>
                    <input type="email" id="user_email" name="user_email" placeholder="your.email@example.com">
                </div>
            </div>
            
            <button type="submit" class="submit-btn" id="submit-btn">
                🚀 Submit Backtest Request
            </button>
        </form>
    </div>
    
    <script>
        // Preset configurations
        const presets = {
            quick: {
                symbols: "AAPL,GOOGL,MSFT",
                start_date: "2024-01-01",
                end_date: "2024-12-31",
                initial_capital: 50000,
                risk_profile: "moderate",
                strategies: ["BollingerBands", "RSI", "MACD"],
                use_llm: false,
                parallel_execution: true,
                database_only: true
            },
            comprehensive: {
                symbols: "AAPL,GOOGL,MSFT,TSLA,NVDA,META,AMZN,NFLX,AMD,INTC",
                start_date: "2023-01-01",
                end_date: "2025-01-01",
                initial_capital: 100000,
                risk_profile: "moderate",
                strategies: ["BollingerBands", "RSI", "MACD", "Momentum", "MeanReversion", "SMACrossover", "VolatilityBreakout", "Ichimoku", "AdaptiveMomentum", "VWAP", "PairsTrading"],
                use_llm: false,
                parallel_execution: true,
                database_only: true
            },
            options: {
                symbols: "SPY,QQQ,IWM,DIA,XLF,XLE,XLK,XLV,XLI,XLP",
                start_date: "2023-06-01",
                end_date: "2025-01-01",
                initial_capital: 100000,
                risk_profile: "aggressive",
                strategies: ["GreeksEnhanced", "IronCondor", "EnhancedIronCondor", "CashSecuredPut", "CoveredCall", "CalendarSpread", "ButterflySpread", "VolatilityStrategy", "EarningsStrategy"],
                use_llm: false,
                parallel_execution: true,
                database_only: true
            },
            advanced: {
                symbols: "AAPL,GOOGL,MSFT,TSLA,NVDA,META,AMZN,NFLX,AMD,INTC",
                start_date: "2023-01-01",
                end_date: "2025-01-01",
                initial_capital: 100000,
                risk_profile: "aggressive",
                strategies: ["BollingerBands", "RSI", "MACD", "Momentum", "MeanReversion", "VolatilityBreakout", "TrailingStop", "Fibonacci", "NeuralNetwork", "QuantumMomentum", "RegimeSwitching", "KalmanFilter", "MLEnsemble", "EnhancedDayTrading"],
                use_llm: true,
                parallel_execution: true,
                database_only: false
            }
        };
        
        function loadPreset(presetName) {
            const preset = presets[presetName];
            if (!preset) return;
            
            // Update form fields
            document.getElementById('symbols').value = preset.symbols;
            document.getElementById('start_date').value = preset.start_date;
            document.getElementById('end_date').value = preset.end_date;
            document.getElementById('initial_capital').value = preset.initial_capital;
            document.getElementById('risk_profile').value = preset.risk_profile;
            
            // Update checkboxes
            document.querySelectorAll('input[name="strategies"]').forEach(checkbox => {
                checkbox.checked = preset.strategies.includes(checkbox.value);
            });
            
            document.getElementById('use_llm').checked = preset.use_llm;
            document.getElementById('parallel_execution').checked = preset.parallel_execution;
            document.getElementById('database_only').checked = preset.database_only;
            
            // Update preset button styling
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            
            if (type === 'success') {
                setTimeout(() => {
                    alertContainer.innerHTML = '';
                }, 5000);
            }
        }
        
        document.getElementById('backtest-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = '🔄 Submitting...';
            
            try {
                // Collect form data
                const formData = new FormData(e.target);
                const symbols = formData.get('symbols').split(',').map(s => s.trim());
                const strategies = Array.from(formData.getAll('strategies'));
                const startDate = formData.get('start_date');
                const endDate = formData.get('end_date');
                const initialCapital = parseFloat(formData.get('initial_capital'));
                const riskProfile = formData.get('risk_profile');
                const useLLM = formData.has('use_llm');
                const parallelExecution = formData.has('parallel_execution');
                const databaseOnly = formData.has('database_only');
                const enableNotifications = formData.has('enable_notifications');
                const userEmail = formData.get('user_email');
                
                // Validate form
                if (symbols.length === 0) {
                    throw new Error('Please select at least one symbol');
                }
                if (strategies.length === 0) {
                    throw new Error('Please select at least one strategy');
                }
                if (new Date(startDate) >= new Date(endDate)) {
                    throw new Error('Start date must be before end date');
                }
                if (enableNotifications && !userEmail) {
                    throw new Error('Please enter an email address for notifications');
                }
                
                // Submit request
                const response = await fetch('/api/submit-backtest', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        symbols: symbols,
                        strategies: strategies,
                        start_date: startDate,
                        end_date: endDate,
                        initial_capital: initialCapital,
                        risk_profile: riskProfile,
                        use_llm: useLLM,
                        parallel_execution: parallelExecution,
                        database_only: databaseOnly,
                        enable_notifications: enableNotifications,
                        user_email: userEmail
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(`✅ Backtest request submitted successfully! Job ID: ${result.job_id}`, 'success');
                    e.target.reset();
                } else {
                    throw new Error(result.error || 'Failed to submit backtest request');
                }
                
            } catch (error) {
                showAlert(`❌ Error: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Submit Backtest Request';
            }
        });
        
        // Email notification toggle functionality
        document.getElementById('enable_notifications').addEventListener('change', function() {
            const emailField = document.getElementById('email-field');
            if (this.checked) {
                emailField.style.display = 'block';
            } else {
                emailField.style.display = 'none';
            }
        });

        // Strategy selection functions
        function selectAllStrategies() {
            document.querySelectorAll('input[name="strategies"]').forEach(checkbox => {
                checkbox.checked = true;
            });
        }

        function clearAllStrategies() {
            document.querySelectorAll('input[name="strategies"]').forEach(checkbox => {
                checkbox.checked = false;
            });
        }

        function selectCategory(category) {
            // Clear all first
            clearAllStrategies();
            
            // Select based on category
            const basicStrategies = ['BollingerBands', 'RSI', 'MACD', 'Momentum', 'MeanReversion', 'SMACrossover', 'VolatilityBreakout', 'Ichimoku', 'IchimokuEnhanced', 'AdaptiveMomentum', 'RegimeSwitching', 'VWAP', 'PairsTrading', 'KalmanFilter', 'MLEnsemble', 'EnhancedDayTrading', 'NewsEnhanced', 'SocialMediaSentiment'];
            const optionsStrategies = ['GreeksEnhanced', 'IronCondor', 'EnhancedIronCondor', 'CashSecuredPut', 'CoveredCall', 'CalendarSpread', 'ButterflySpread', 'VolatilityStrategy', 'EarningsStrategy', 'Straddle', 'LongStrangle', 'ShortStrangle', 'BullishDiagonal', 'BearishDiagonal'];
            const advancedStrategies = ['TrailingStop', 'Fibonacci', 'NeuralNetwork', 'QuantumMomentum', 'CrossSectionalMomentum', 'EnhancedExit', 'AdvancedExit', 'PortfolioStrategy'];
            
            let strategiesToSelect = [];
            
            if (category === 'basic') {
                strategiesToSelect = basicStrategies;
            } else if (category === 'options') {
                strategiesToSelect = optionsStrategies;
            } else if (category === 'advanced') {
                strategiesToSelect = advancedStrategies;
            }
            
            strategiesToSelect.forEach(strategy => {
                const checkbox = document.querySelector(`input[value="${strategy}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        }


        
        // Set default date range (last 2 years)
        const today = new Date();
        const twoYearsAgo = new Date(today.getFullYear() - 2, today.getMonth(), today.getDate());
        
        document.getElementById('end_date').value = today.toISOString().split('T')[0];
        document.getElementById('start_date').value = twoYearsAgo.toISOString().split('T')[0];
    </script>
</body>
</html>
"""

@app.post("/api/submit-backtest")
async def submit_backtest(request: BacktestRequest):
    """Submit a backtest request"""
    try:
        logger.info(f"Received backtest request: {request}")
        
        # Generate job name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_name = f"backtest-{request.risk_profile}-{timestamp}"
        
        # Create Kubernetes job
        job_created = await create_backtest_job(request, job_name)
        
        if job_created:
            return {
                "success": True,
                "job_id": job_name,
                "message": "Backtest job created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create backtest job")
            
    except Exception as e:
        logger.error(f"Error submitting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_backtest_job(request: BacktestRequest, job_name: str) -> bool:
    """Create a Kubernetes job for the backtest"""
    try:
        # Generate the appropriate script based on request
        script_name = determine_script_name(request)
        
        # Create job YAML
        job_yaml = generate_job_yaml(request, job_name, script_name)
        
        # Write job YAML to temporary file
        job_file = f"/tmp/{job_name}.yaml"
        with open(job_file, 'w') as f:
            f.write(job_yaml)
        
        # Apply job to Kubernetes
        result = subprocess.run([
            "kubectl", "apply", "-f", job_file,
            "-n", KUBERNETES_NAMESPACE
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully created backtest job: {job_name}")
            return True
        else:
            logger.error(f"Failed to create job: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating backtest job: {e}")
        return False

def determine_script_name(request: BacktestRequest) -> str:
    """Determine which script to use based on request parameters"""
    # Use notification script if email notifications are enabled
    if request.enable_notifications and request.user_email:
        return "run_backtest_with_notifications.py"
    elif "GreeksEnhanced" in request.strategies or "IronCondor" in request.strategies:
        return "run_comprehensive_options_backtest.py"
    elif request.use_llm:
        return "run_enhanced_comprehensive_backtest.py"
    elif len(request.strategies) > 6:
        return "run_unified_advanced_portfolio_backtest.py"
    else:
        return "run_comprehensive_options_backtest.py"

def generate_job_yaml(request: BacktestRequest, job_name: str, script_name: str) -> str:
    """Generate Kubernetes job YAML"""
    
    # Environment variables
    env_vars = [
        {"name": "DATABASE_URL", "value": "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot"},
        {"name": "POLYGON_API_KEY", "valueFrom": {"secretKeyRef": {"name": "trading-secrets", "key": "polygon-api-key"}}},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "ENABLE_LLM_EVALUATION", "value": str(request.use_llm).lower()},
        {"name": "PARALLEL_EXECUTION", "value": str(request.parallel_execution).lower()},
        {"name": "DATABASE_ONLY", "value": str(request.database_only).lower()},
        {"name": "BACKTEST_SYMBOLS", "value": ",".join(request.symbols)},
        {"name": "BACKTEST_START_DATE", "value": request.start_date},
        {"name": "BACKTEST_END_DATE", "value": request.end_date},
        {"name": "BACKTEST_INITIAL_CAPITAL", "value": str(request.initial_capital)},
        {"name": "BACKTEST_RISK_PROFILE", "value": request.risk_profile},
        {"name": "BACKTEST_STRATEGIES", "value": ",".join(request.strategies)}
    ]
    
    # Add email notification environment variables if enabled
    if request.enable_notifications and request.user_email:
        env_vars.extend([
            {"name": "ENABLE_EMAIL_NOTIFICATIONS", "value": "true"},
            {"name": "USER_EMAIL", "value": request.user_email},
            {"name": "NOTIFICATION_SERVICE_URL", "value": "http://notification-service:80"}
        ])
    
    # Generate environment variables YAML
    env_yaml_lines = []
    for env in env_vars:
        if "value" in env:
            env_yaml_lines.append(f'        - name: {env["name"]}')
            env_yaml_lines.append(f'          value: "{env["value"]}"')
        else:
            env_yaml_lines.append(f'        - name: {env["name"]}')
            env_yaml_lines.append(f'          valueFrom:')
            env_yaml_lines.append(f'            secretKeyRef:')
            env_yaml_lines.append(f'              name: {env["valueFrom"]["secretKeyRef"]["name"]}')
            env_yaml_lines.append(f'              key: {env["valueFrom"]["secretKeyRef"]["key"]}')
    
    env_yaml = "\n".join(env_yaml_lines)
    
    return f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: {KUBERNETES_NAMESPACE}
  labels:
    app: backtest
    type: web-request
    risk-profile: {request.risk_profile}
spec:
  template:
    metadata:
      labels:
        app: backtest
        type: web-request
    spec:
      serviceAccountName: default
      containers:
      - name: backtest
        image: localhost:32000/backtest:latest
        command: ["python"]
        args: ["{script_name}"]
        env:
{env_yaml}
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: shared-data
          mountPath: /app/data
      volumes:
      - name: shared-data
        emptyDir: {{}}
      restartPolicy: Never
  backoffLimit: 2"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082) 