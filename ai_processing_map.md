# 🤖 AI Processing Map - Trading System

## Overview
This document shows the complete AI processing workflow in the trading system using Mermaid.js diagrams.

## 🧠 AI Processing Architecture

```mermaid
graph TB
    subgraph "📡 Data Ingestion Layer"
        MD[Market Data Service<br/>Port: 11084]
        NW[News Worker<br/>Sentiment Analysis]
        RW[Risk Worker<br/>Risk Assessment]
        MW[Market Data Worker<br/>Real-time Data]
    end
    
    subgraph "🔄 Message Queue Layer"
        RMQ[RabbitMQ<br/>Port: 11144]
        Q1[Market Data Queue]
        Q2[News Analysis Queue]
        Q3[AI Processing Queue]
        Q4[Trading Signal Queue]
    end
    
    subgraph "🤖 AI Analysis Services"
        AAS[AI Analysis Service<br/>Port: 11085]
        ADE[AI Decision Engine<br/>Investment Recommendations]
        AQI[AI Query Interface<br/>Natural Language Processing]
        VDS[Vector Database Service<br/>Semantic Search]
    end
    
    subgraph "🧠 LLM Processing Layer"
        LP[LLM Proxy<br/>Port: 12001]
        OLL[Ollama Service<br/>Local LLM]
        VS[Vector Storage<br/>Document Embeddings]
        BV[Background Vectorization<br/>Document Processing]
    end
    
    subgraph "📊 Analysis Components"
        TA[Technical Analysis<br/>RSI, MACD, Bollinger Bands]
        SA[Sentiment Analysis<br/>News & Social Media]
        PA[Pattern Recognition<br/>Market Patterns]
        CA[Context Analysis<br/>Market Conditions]
    end
    
    subgraph "🎯 Decision Making"
        DT[Decision Tree Engine<br/>5-Layer Validation]
        CS[Confidence Scoring<br/>0-100% Scale]
        RA[Risk Assessment<br/>Position Limits]
        PS[Position Sizing<br/>Risk-Adjusted]
    end
    
    subgraph "⚡ Execution Layer"
        TE[Trading Engine<br/>Order Management]
        OMS[Order Management Service<br/>Order Execution]
        PM[Portfolio Management<br/>Position Tracking]
        TM[Trade Monitoring<br/>Performance Tracking]
    end
    
    subgraph "📈 Output & Feedback"
        TR[Trading Recommendations<br/>Buy/Sell/Hold]
        AL[Alerts & Notifications<br/>Real-time Updates]
        PR[Performance Reports<br/>P&L Analysis]
        FB[Feedback Loop<br/>Learning & Improvement]
    end
    
    %% Data Flow Connections
    MD --> RMQ
    NW --> RMQ
    RW --> RMQ
    MW --> RMQ
    
    RMQ --> Q1
    RMQ --> Q2
    RMQ --> Q3
    RMQ --> Q4
    
    Q1 --> AAS
    Q2 --> AAS
    Q3 --> ADE
    Q4 --> TE
    
    AAS --> LP
    ADE --> LP
    AQI --> VDS
    VDS --> VS
    
    LP --> OLL
    VS --> BV
    BV --> VS
    
    AAS --> TA
    AAS --> SA
    ADE --> PA
    ADE --> CA
    
    TA --> DT
    SA --> DT
    PA --> DT
    CA --> DT
    
    DT --> CS
    CS --> RA
    RA --> PS
    
    PS --> TE
    TE --> OMS
    OMS --> PM
    PM --> TM
    
    TE --> TR
    TM --> AL
    PM --> PR
    PR --> FB
    
    FB -.-> DT
    FB -.-> AAS
    FB -.-> ADE
```

## 🔄 AI Processing Workflow

```mermaid
sequenceDiagram
    participant User
    participant AQI as AI Query Interface
    participant VDS as Vector Database
    participant ADE as AI Decision Engine
    participant AAS as AI Analysis Service
    participant LP as LLM Proxy
    participant OLL as Ollama LLM
    participant TE as Trading Engine
    
    User->>AQI: "Is now a good time to buy AAPL?"
    AQI->>VDS: Search historical patterns
    VDS->>AQI: Similar market conditions
    
    AQI->>ADE: Process investment query
    ADE->>AAS: Request market analysis
    AAS->>LP: Generate AI analysis prompt
    
    LP->>OLL: Send analysis request
    OLL->>LP: Return AI analysis
    LP->>AAS: AI analysis results
    
    AAS->>ADE: Market analysis + AI insights
    ADE->>ADE: Multi-factor decision making
    ADE->>ADE: Calculate confidence score
    ADE->>ADE: Determine position sizing
    
    ADE->>AQI: Investment recommendation
    AQI->>User: "BUY AAPL - 85% confidence"
    
    Note over ADE,TE: Optional: Execute trade
    ADE->>TE: Execute if confidence > 80%
    TE->>User: Trade execution confirmation
```

## 🧠 AI Analysis Pipeline

```mermaid
flowchart TD
    subgraph "📊 Input Data"
        MD[Market Data<br/>Price, Volume, OHLC]
        ND[News Data<br/>Sentiment, Impact]
        TD[Technical Data<br/>Indicators, Patterns]
        HD[Historical Data<br/>Past Performance]
    end
    
    subgraph "🔍 Data Processing"
        DP[Data Preprocessing<br/>Cleaning & Normalization]
        FE[Feature Engineering<br/>Technical Indicators]
        VS[Vectorization<br/>Text to Embeddings]
        AG[Data Aggregation<br/>Multi-timeframe Analysis]
    end
    
    subgraph "🤖 AI Analysis"
        LLM[LLM Analysis<br/>Ollama Integration]
        SA[Sentiment Analysis<br/>News & Social Media]
        PR[Pattern Recognition<br/>Market Patterns]
        CA[Context Analysis<br/>Market Conditions]
        RA[Risk Analysis<br/>Volatility & Exposure]
    end
    
    subgraph "🎯 Signal Generation"
        SG[Signal Generation<br/>Buy/Sell/Hold]
        CS[Confidence Scoring<br/>0-100% Scale]
        TS[Timing Analysis<br/>Entry/Exit Points]
        PS[Position Sizing<br/>Risk-Adjusted]
    end
    
    subgraph "✅ Validation"
        DT[Decision Tree<br/>5-Layer Validation]
        RC[Risk Checks<br/>Position Limits]
        TC[Technical Validation<br/>Indicator Confirmation]
        AC[AI Validation<br/>Confidence Threshold]
    end
    
    subgraph "📤 Output"
        TR[Trading Recommendation<br/>Action + Reasoning]
        AL[Alerts<br/>Real-time Notifications]
        RP[Reports<br/>Performance Analysis]
        FB[Feedback<br/>Learning Data]
    end
    
    MD --> DP
    ND --> DP
    TD --> DP
    HD --> DP
    
    DP --> FE
    DP --> VS
    DP --> AG
    
    FE --> LLM
    VS --> SA
    AG --> PR
    AG --> CA
    AG --> RA
    
    LLM --> SG
    SA --> SG
    PR --> SG
    CA --> SG
    RA --> SG
    
    SG --> CS
    CS --> TS
    TS --> PS
    
    PS --> DT
    DT --> RC
    RC --> TC
    TC --> AC
    
    AC --> TR
    TR --> AL
    TR --> RP
    RP --> FB
    
    FB -.-> LLM
    FB -.-> SG
    FB -.-> DT
```

## 🎯 AI Decision Tree Process

```mermaid
flowchart TD
    START([AI Analysis Request]) --> INPUT[Gather Input Data]
    
    INPUT --> MD[Market Data]
    INPUT --> ND[News Data]
    INPUT --> TD[Technical Data]
    INPUT --> HD[Historical Data]
    
    MD --> LLM[LLM Analysis]
    ND --> SA[Sentiment Analysis]
    TD --> PR[Pattern Recognition]
    HD --> CA[Context Analysis]
    
    LLM --> COMBINE[Combine Analysis]
    SA --> COMBINE
    PR --> COMBINE
    CA --> COMBINE
    
    COMBINE --> SCORE[Calculate Confidence Score]
    
    SCORE --> CHECK{Confidence > 30%?}
    CHECK -->|No| REJECT[Reject - Low Confidence]
    CHECK -->|Yes| TECH{Technical Validation}
    
    TECH -->|Fail| REJECT
    TECH -->|Pass| AI{AI Validation}
    
    AI -->|Fail| REJECT
    AI -->|Pass| RISK{Risk Assessment}
    
    RISK -->|Fail| REJECT
    RISK -->|Pass| FINAL{Final Decision}
    
    FINAL -->|Confidence < 70%| WAIT[Wait for Better Conditions]
    FINAL -->|Confidence >= 70%| EXECUTE[Execute Trade]
    
    EXECUTE --> MONITOR[Monitor Trade]
    MONITOR --> FEEDBACK[Update Learning Data]
    FEEDBACK -.-> LLM
    
    style START fill:#e1f5fe
    style EXECUTE fill:#c8e6c9
    style REJECT fill:#ffcdd2
    style WAIT fill:#fff3e0
```

## 🔧 AI Service Integration

```mermaid
graph LR
    subgraph "🤖 AI Services"
        AAS[AI Analysis Service<br/>Port: 11085]
        ADE[AI Decision Engine]
        AQI[AI Query Interface]
        VDS[Vector Database Service]
    end
    
    subgraph "🧠 LLM Services"
        LP[LLM Proxy<br/>Port: 12001]
        OLL[Ollama Service<br/>Local LLM]
        VS[Vector Storage]
        BV[Background Vectorization]
    end
    
    subgraph "📊 Data Services"
        MDS[Market Data Service<br/>Port: 11084]
        NS[News Service]
        TS[Technical Service]
        PS[Portfolio Service]
    end
    
    subgraph "⚡ Execution Services"
        TE[Trading Engine]
        OMS[Order Management]
        RM[Risk Management]
        PM[Portfolio Management]
    end
    
    AAS --> LP
    ADE --> LP
    AQI --> VDS
    VDS --> VS
    
    LP --> OLL
    VS --> BV
    
    AAS --> MDS
    AAS --> NS
    ADE --> TS
    ADE --> PS
    
    ADE --> TE
    TE --> OMS
    OMS --> RM
    RM --> PM
```

## 📈 Performance Metrics

```mermaid
graph TB
    subgraph "📊 AI Performance Metrics"
        subgraph "⚡ Response Times"
            RT1[LLM Response: < 5s]
            RT2[Analysis Complete: < 10s]
            RT3[Decision Made: < 15s]
            RT4[Trade Executed: < 30s]
        end
        
        subgraph "🎯 Accuracy Metrics"
            ACC1[Signal Accuracy: > 60%]
            ACC2[AI Confidence: 70-90%]
            ACC3[Risk Prediction: > 80%]
            ACC4[Pattern Recognition: > 75%]
        end
        
        subgraph "📈 Trading Performance"
            PERF1[Win Rate: > 55%]
            PERF2[Sharpe Ratio: > 1.5]
            PERF3[Max Drawdown: < 15%]
            PERF4[Profit Factor: > 1.3]
        end
        
        subgraph "🔄 Learning Metrics"
            LEARN1[Model Updates: Daily]
            LEARN2[Pattern Learning: Continuous]
            LEARN3[Feedback Integration: Real-time]
            LEARN4[Performance Improvement: Monthly]
        end
    end
    
    RT1 --> ACC1
    RT2 --> ACC2
    RT3 --> ACC3
    RT4 --> ACC4
    
    ACC1 --> PERF1
    ACC2 --> PERF2
    ACC3 --> PERF3
    ACC4 --> PERF4
    
    PERF1 --> LEARN1
    PERF2 --> LEARN2
    PERF3 --> LEARN3
    PERF4 --> LEARN4
```

## 🚀 Current Status

**MCP Service Status**: ✅ **Healthy and Running**
- **Version**: 1.0.0
- **Port**: 11117 (Port-forwarded)
- **Status**: All tools available
- **Documentation**: 166+ files indexed
- **AI Services**: 4 active AI services

**No new deployment needed** - the MCP service is fully operational with all AI processing capabilities available through the API endpoints.






