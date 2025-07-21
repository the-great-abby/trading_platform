# 🚀 Space Trading Station - Architecture Diagrams

This document contains comprehensive Mermaid diagrams showing how the Space Trading Station components fit together.

## 🏗️ System Architecture Overview

```mermaid
graph TB
    subgraph "🌌 External Universe"
        MD[Market Data Providers<br/>Polygon, Alpha Vantage]
        NP[News Providers<br/>Reuters, Bloomberg]
        API[External APIs<br/>Trading APIs]
    end
    
    subgraph "🚀 Space Trading Station"
        subgraph "🎯 Mission Control Gateway"
            GW[API Gateway<br/>localhost:8080]
            LB[Load Balancer]
        end
        
        subgraph "📊 Dashboard Layer"
            PD[Performance Dashboard<br/>localhost:11000]
            TD[Trading Dashboard<br/>localhost:11001]
            HD[Health Dashboard<br/>localhost:11002]
            RD[RSS Dashboard<br/>localhost:11003]
            BR[Backtest Request<br/>localhost:11031]
        end
        
        subgraph "🛰️ Core Services"
            TS[Trading Service]
            MDS[Market Data Service]
            RMS[Risk Management Service]
            PS[Portfolio Service]
            SS[Strategy Service]
            OMS[Order Management Service]
            AS[Analytics Service]
            UMS[User Management Service]
        end
        
        subgraph "🤖 AI & LLM Systems"
            LLM[LLM Service<br/>Ollama Integration]
            LP[LLM Proxy<br/>localhost:12001]
            TE[Trade Evaluator]
            RSI[RSI AI Enhanced]
            BB[Bollinger Bands AI]
            MACD[MACD AI Enhanced]
            SMA[SMA Crossover AI]
            NE[News Enhanced]
        end
        
        subgraph "📰 RSS & News Systems"
            RSS[RSS Feed Service]
            RSSD[RSS Dashboard]
            NS[News Scanner]
            NW[News Worker]
        end
        
        subgraph "📊 Data Storage Bay"
            WDB[(Write Database<br/>PostgreSQL)]
            RDB[(Read Database<br/>PostgreSQL)]
            ES[(Event Store)]
            CACHE[(Redis Cache)]
            TSDB[(Time Series DB)]
        end
        
        subgraph "🔄 Event Bus"
            EB[Event Bus]
            MQ[RabbitMQ<br/>Message Queue]
        end
        
        subgraph "🐳 Container Registry"
            REG[Docker Registry<br/>localhost:32000]
        end
    end
    
    MD --> MDS
    NP --> NS
    API --> GW
    
    GW --> TS
    GW --> MDS
    GW --> PS
    GW --> AS
    
    TS --> OMS
    TS --> RMS
    TS --> SS
    
    SS --> RSI
    SS --> BB
    SS --> MACD
    SS --> SMA
    SS --> NE
    
    LLM --> TE
    LP --> LLM
    TE --> SS
    
    RSS --> RSSD
    NS --> RSS
    NW --> RSS
    
    TS --> WDB
    MDS --> RDB
    PS --> RDB
    AS --> RDB
    
    TS --> ES
    OMS --> ES
    RMS --> ES
    
    EB --> TS
    EB --> MDS
    EB --> PS
    EB --> AS
    
    MQ --> SS
    MQ --> TS
    MQ --> NW
    
    REG -.->|Build/Push| TS
    REG -.->|Build/Push| MDS
    REG -.->|Build/Push| RSS
    REG -.->|Build/Push| RSSD
```

## 🔄 Data Flow Architecture

```mermaid
flowchart TD
    subgraph "📡 Input Sources"
        MD[Market Data]
        NEWS[News Events]
        USER[User Commands]
    end
    
    subgraph "🎯 Mission Control"
        API[API Gateway]
        AUTH[Authentication]
        VAL[Validation]
    end
    
    subgraph "🤖 AI Navigation Systems"
        LLM[Ollama LLM]
        SENT[Sentiment Analysis]
        CONF[Confidence Scoring]
    end
    
    subgraph "📊 Processing Pipeline"
        TS[Trading Service]
        RMS[Risk Management]
        OMS[Order Management]
    end
    
    subgraph "📈 Analytics & Reporting"
        AS[Analytics Service]
        PS[Portfolio Service]
        REP[Reporting]
    end
    
    subgraph "💾 Data Storage"
        WDB[(Write DB)]
        RDB[(Read DB)]
        ES[(Event Store)]
        CACHE[(Cache)]
    end
    
    MD --> API
    NEWS --> API
    USER --> API
    
    API --> AUTH
    AUTH --> VAL
    VAL --> TS
    
    TS --> LLM
    LLM --> SENT
    SENT --> CONF
    CONF --> TS
    
    TS --> RMS
    RMS --> OMS
    OMS --> WDB
    
    TS --> AS
    AS --> PS
    PS --> RDB
    
    WDB --> ES
    ES --> AS
    AS --> REP
    
    RDB --> CACHE
    CACHE --> API
```

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "☸️ Kubernetes Cluster"
        subgraph "🚀 Space Station Namespace"
            subgraph "🎯 Mission Control"
                GW[API Gateway]
                ING[Ingress Controller]
            end
            
            subgraph "🛰️ Core Services"
                TS[Trading Service]
                MDS[Satellite Data Service]
                PS[Portfolio Service]
                AS[Analytics Service]
            end
            
            subgraph "🤖 AI Systems"
                OLL[Ollama Service]
                ANS[AI Navigation Systems]
                NEWS[News Scanner]
            end
            
            subgraph "📊 Data Services"
                PG[(PostgreSQL)]
                RED[(Redis)]
                ES[(EventStore)]
            end
            
            subgraph "🔄 Message Queue"
                RAB[RabbitMQ]
                WORK[Workers]
            end
        end
    end
    
    subgraph "🌌 External"
        POL[Polygon API]
        ALP[Alpha Vantage]
        NEWS_API[News APIs]
    end
    
    POL --> MDS
    ALP --> MDS
    NEWS_API --> NEWS
    
    GW --> TS
    GW --> MDS
    GW --> PS
    GW --> AS
    
    TS --> OLL
    OLL --> ANS
    ANS --> TS
    
    TS --> RAB
    RAB --> WORK
    WORK --> TS
    
    TS --> PG
    MDS --> PG
    PS --> PG
    
    TS --> RED
    AS --> RED
```

## 🔄 Event-Driven Architecture

```mermaid
sequenceDiagram
    participant User
    participant Gateway
    participant Trading
    participant AI
    participant Risk
    participant Order
    participant Portfolio
    participant EventStore
    
    User->>Gateway: Place Order Command
    Gateway->>Trading: Forward Command
    Trading->>AI: Request Signal Analysis
    AI->>Trading: Return AI Signal
    Trading->>Risk: Validate Trade
    Risk->>Trading: Trade Validated
    Trading->>Order: Create Order
    Order->>EventStore: OrderPlaced Event
    EventStore->>Portfolio: Update Position
    Portfolio->>EventStore: PositionUpdated Event
    EventStore->>Trading: Order Executed
    Trading->>Gateway: Order Response
    Gateway->>User: Order Confirmation
```

## 🤖 AI Navigation System Flow

```mermaid
flowchart TD
    subgraph "📊 Market Data"
        PRICE[Price Data]
        VOL[Volume Data]
        TECH[Technical Indicators]
        NEWS[News Events]
    end
    
    subgraph "🤖 AI Navigation Systems"
        subgraph "🧠 Base Strategies"
            RSI[RSI Strategy]
            BB[Bollinger Bands]
            MACD[MACD Strategy]
            SMA[SMA Crossover]
        end
        
        subgraph "🚀 AI Enhancement"
            LLM[Ollama LLM]
            SENT[Sentiment Analysis]
            CONF[Confidence Scoring]
            RISK[Risk Assessment]
        end
    end
    
    subgraph "📈 Signal Generation"
        BASE[Base Signal]
        AI[AI Analysis]
        COMB[Combined Signal]
        META[Metadata]
    end
    
    subgraph "🎯 Trading Execution"
        VAL[Validation]
        EXE[Execution]
        MON[Monitoring]
    end
    
    PRICE --> RSI
    PRICE --> BB
    PRICE --> MACD
    PRICE --> SMA
    
    TECH --> RSI
    TECH --> BB
    TECH --> MACD
    TECH --> SMA
    
    NEWS --> LLM
    
    RSI --> BASE
    BB --> BASE
    MACD --> BASE
    SMA --> BASE
    
    BASE --> LLM
    LLM --> SENT
    SENT --> CONF
    CONF --> RISK
    
    BASE --> AI
    AI --> COMB
    COMB --> META
    
    COMB --> VAL
    VAL --> EXE
    EXE --> MON
```

## 📊 Monitoring & Observability

```mermaid
graph TB
    subgraph "🚀 Space Trading Station"
        subgraph "📡 Data Collection"
            MET[Metrics]
            LOG[Logs]
            TRACE[Traces]
        end
        
        subgraph "📊 Monitoring Stack"
            PROM[Prometheus]
            GRAF[Grafana]
            ALERT[Alert Manager]
        end
        
        subgraph "📈 Dashboards"
            MC[Mission Control]
            TRAD[Trading Dashboard]
            AI[AI Systems]
            PERF[Performance]
        end
    end
    
    subgraph "🔍 Observability"
        subgraph "📊 Metrics"
            ORD[Order Metrics]
            TRADE[Trade Metrics]
            PORT[Portfolio Metrics]
            AI_MET[AI Metrics]
        end
        
        subgraph "📝 Logs"
            APP[Application Logs]
            SYS[System Logs]
            ERR[Error Logs]
        end
        
        subgraph "🔗 Traces"
            REQ[Request Traces]
            DB[Database Traces]
            API[API Traces]
        end
    end
    
    MET --> PROM
    LOG --> PROM
    TRACE --> PROM
    
    PROM --> GRAF
    GRAF --> MC
    GRAF --> TRAD
    GRAF --> AI
    GRAF --> PERF
    
    PROM --> ALERT
    
    ORD --> MET
    TRADE --> MET
    PORT --> MET
    AI_MET --> MET
    
    APP --> LOG
    SYS --> LOG
    ERR --> LOG
    
    REQ --> TRACE
    DB --> TRACE
    API --> TRACE
```

## 🔧 Development Workflow

```mermaid
graph LR
    subgraph "👨‍💻 Development"
        CODE[Code Changes]
        TEST[Testing]
        BUILD[Build]
    end
    
    subgraph "🐳 Containerization"
        DOCKER[Docker Build]
        REG[Registry]
        IMG[Images]
    end
    
    subgraph "☸️ Deployment"
        K8S[Kubernetes]
        DEPLOY[Deploy]
        ROLL[Rollout]
    end
    
    subgraph "🚀 Space Station"
        PODS[Pods]
        SVC[Services]
        ING[Ingress]
    end
    
    subgraph "📊 Monitoring"
        HEALTH[Health Checks]
        METRICS[Metrics]
        ALERTS[Alerts]
    end
    
    CODE --> TEST
    TEST --> BUILD
    BUILD --> DOCKER
    DOCKER --> REG
    REG --> IMG
    IMG --> K8S
    K8S --> DEPLOY
    DEPLOY --> ROLL
    ROLL --> PODS
    PODS --> SVC
    SVC --> ING
    ING --> HEALTH
    HEALTH --> METRICS
    METRICS --> ALERTS
```

## 🎯 Mission Control Dashboard Layout

```mermaid
graph TB
    subgraph "🎯 Mission Control Dashboard"
        subgraph "📊 Real-time Metrics"
            ORD[Orders/sec]
            TRAD[Trades/sec]
            PNL[P&L]
            POS[Positions]
        end
        
        subgraph "🤖 AI Navigation Systems"
            AI_STATUS[AI Status]
            SIGNALS[Active Signals]
            CONF[Confidence Levels]
            SENT[Sentiment]
        end
        
        subgraph "📈 Portfolio View"
            VALUE[Portfolio Value]
            ALLOC[Allocation]
            PERF[Performance]
            RISK[Risk Metrics]
        end
        
        subgraph "🛰️ System Status"
            SERVICES[Service Health]
            RESOURCES[Resource Usage]
            ALERTS[Active Alerts]
            LOGS[Recent Logs]
        end
    end
    
    subgraph "🔧 Controls"
        DEPLOY[Deploy]
        SCALE[Scale]
        RESTART[Restart]
        CONFIG[Configure]
    end
    
    ORD --> SERVICES
    TRAD --> SERVICES
    PNL --> PERF
    POS --> ALLOC
    
    AI_STATUS --> SIGNALS
    SIGNALS --> CONF
    CONF --> SENT
    
    VALUE --> PERF
    ALLOC --> RISK
    PERF --> ALERTS
    
    SERVICES --> ALERTS
    RESOURCES --> ALERTS
    ALERTS --> LOGS
    
    DEPLOY --> SERVICES
    SCALE --> RESOURCES
    RESTART --> SERVICES
    CONFIG --> SERVICES
```

## 🛰️ Orbital Backtesting Flow

```mermaid
flowchart TD
    subgraph "📊 Historical Data Sources"
        POL[Polygon API]
        ALP[Alpha Vantage]
        LOCAL[Local Cache]
        DB[(Historical DB)]
    end
    
    subgraph "🛰️ Orbital Backtesting Engine"
        HIST[Historical Data Loader]
        STRAT[Strategy Selection]
        EXEC[Backtest Execution]
        RES[Results Analysis]
        COMP[Comparison Engine]
    end
    
    subgraph "🤖 AI Navigation Systems"
        BASE[Base Strategy]
        AI[AI Enhancement]
        COMB[Combined Signal]
        CONF[Confidence Scoring]
    end
    
    subgraph "📈 Performance Metrics"
        RET[Returns Analysis]
        SHARPE[Sharpe Ratio]
        DRAWDOWN[Max Drawdown]
        WIN_RATE[Win Rate]
        VOL[Volatility]
        SORTINO[Sortino Ratio]
    end
    
    subgraph "📊 Results & Reporting"
        REP[Backtest Report]
        CHART[Performance Charts]
        STATS[Statistics]
        EXPORT[Data Export]
    end
    
    POL --> HIST
    ALP --> HIST
    LOCAL --> HIST
    DB --> HIST
    
    HIST --> STRAT
    STRAT --> BASE
    BASE --> AI
    AI --> COMB
    COMB --> CONF
    
    CONF --> EXEC
    EXEC --> RES
    RES --> COMP
    
    COMP --> RET
    COMP --> SHARPE
    COMP --> DRAWDOWN
    COMP --> WIN_RATE
    COMP --> VOL
    COMP --> SORTINO
    
    RET --> REP
    SHARPE --> REP
    DRAWDOWN --> REP
    WIN_RATE --> REP
    VOL --> REP
    SORTINO --> REP
    
    REP --> CHART
    REP --> STATS
    REP --> EXPORT
```

## 🛡️ Risk Management Pipeline

```mermaid
flowchart TD
    subgraph "🎯 Risk Management Service"
        subgraph "📊 Position Management"
            POS[Position Sizing]
            LIMITS[Risk Limits]
            EXP[Exposure Calculation]
            CORR[Correlation Analysis]
        end
        
        subgraph "🛡️ Risk Controls"
            VAR[Value at Risk]
            STRESS[Stress Testing]
            SCENARIO[Scenario Analysis]
            ALERT[Risk Alerts]
        end
        
        subgraph "📈 Real-time Monitoring"
            MONITOR[Risk Monitor]
            THRESHOLD[Threshold Checks]
            AUTO[Auto-adjustment]
            MANUAL[Manual Override]
        end
    end
    
    subgraph "📊 Risk Metrics"
        PORT_RISK[Portfolio Risk]
        POS_RISK[Position Risk]
        MARKET_RISK[Market Risk]
        LIQUIDITY[Liquidity Risk]
    end
    
    subgraph "🚨 Risk Alerts"
        HIGH_RISK[High Risk Alert]
        LIMIT_BREACH[Limit Breach]
        VOL_SPIKE[Volatility Spike]
        LIQ_CRISIS[Liquidity Crisis]
    end
    
    subgraph "🔧 Risk Actions"
        REDUCE[Reduce Position]
        HEDGE[Hedge Position]
        STOP[Stop Trading]
        EMERGENCY[Emergency Protocol]
    end
    
    POS --> VAR
    LIMITS --> THRESHOLD
    EXP --> PORT_RISK
    CORR --> MARKET_RISK
    
    VAR --> STRESS
    STRESS --> SCENARIO
    SCENARIO --> ALERT
    
    MONITOR --> THRESHOLD
    THRESHOLD --> AUTO
    AUTO --> MANUAL
    
    PORT_RISK --> HIGH_RISK
    POS_RISK --> LIMIT_BREACH
    MARKET_RISK --> VOL_SPIKE
    LIQUIDITY --> LIQ_CRISIS
    
    HIGH_RISK --> REDUCE
    LIMIT_BREACH --> HEDGE
    VOL_SPIKE --> STOP
    LIQ_CRISIS --> EMERGENCY
```

## 📰 News Integration Flow

```mermaid
sequenceDiagram
    participant NewsAPI
    participant Scanner
    participant AI
    participant Trading
    participant Portfolio
    participant Alert
    
    NewsAPI->>Scanner: News Event
    Scanner->>Scanner: Filter Relevance
    Scanner->>AI: Sentiment Analysis Request
    AI->>AI: Process News + Market Context
    AI->>Trading: Enhanced Signal
    Trading->>Trading: Validate Signal
    Trading->>Portfolio: Position Update
    Trading->>Alert: Risk Assessment
    Alert->>Alert: Check Thresholds
    alt High Impact News
        Alert->>Trading: Emergency Protocol
        Trading->>Portfolio: Emergency Position Update
    end
```

## 🗄️ Database Schema Relationships

```mermaid
erDiagram
    USERS ||--o{ PORTFOLIOS : owns
    PORTFOLIOS ||--o{ POSITIONS : contains
    POSITIONS ||--o{ TRADES : generates
    ORDERS ||--o{ TRADES : executes
    
    STRATEGIES ||--o{ SIGNALS : produces
    SIGNALS ||--o{ ORDERS : triggers
    EVENTS ||--o{ PROJECTIONS : creates
    
    MARKET_DATA ||--o{ SIGNALS : influences
    NEWS_EVENTS ||--o{ SIGNALS : enhances
    AI_ANALYSIS ||--o{ SIGNALS : improves
    
    PORTFOLIOS {
        string id PK
        string user_id FK
        decimal total_value
        decimal cash_balance
        timestamp created_at
        timestamp updated_at
    }
    
    POSITIONS {
        string id PK
        string portfolio_id FK
        string symbol
        int quantity
        decimal avg_price
        decimal current_value
        timestamp created_at
    }
    
    TRADES {
        string id PK
        string order_id FK
        string position_id FK
        string symbol
        string side
        int quantity
        decimal price
        decimal commission
        timestamp executed_at
    }
    
    SIGNALS {
        string id PK
        string strategy_id FK
        string symbol
        string action
        decimal confidence
        json metadata
        timestamp generated_at
    }
    
    AI_ANALYSIS {
        string id PK
        string signal_id FK
        decimal sentiment_score
        decimal confidence_boost
        text reasoning
        timestamp analyzed_at
    }
```

## ☸️ Kubernetes Resource Allocation

```mermaid
graph TB
    subgraph "☸️ Space Station Resource Allocation"
        subgraph "🚀 Mission Critical (High Priority)"
            TS[Trading Service<br/>CPU: 2, RAM: 4GB]
            OLL[Ollama Service<br/>CPU: 4, RAM: 8GB]
            ANS[AI Navigation<br/>CPU: 2, RAM: 4GB]
            RMS[Risk Management<br/>CPU: 1, RAM: 2GB]
        end
        
        subgraph "📊 Core Services (Medium Priority)"
            MDS[Satellite Data<br/>CPU: 1, RAM: 2GB]
            PS[Portfolio Service<br/>CPU: 1, RAM: 2GB]
            AS[Analytics Service<br/>CPU: 2, RAM: 4GB]
            OMS[Order Management<br/>CPU: 1, RAM: 2GB]
        end
        
        subgraph "🔄 Background Services (Low Priority)"
            WORK[Workers<br/>CPU: 0.5, RAM: 1GB]
            SCAN[News Scanner<br/>CPU: 0.5, RAM: 1GB]
            BACKUP[Backup Jobs<br/>CPU: 0.5, RAM: 1GB]
            MONITOR[Monitoring<br/>CPU: 0.5, RAM: 1GB]
        end
    end
    
    subgraph "💾 Data Storage"
        PG[(PostgreSQL<br/>Storage: 100GB)]
        RED[(Redis<br/>Storage: 10GB)]
        ES[(EventStore<br/>Storage: 50GB)]
    end
    
    subgraph "🌐 Network"
        ING[Ingress Controller]
        LB[Load Balancer]
        GW[API Gateway]
    end
```

## 🛡️ Error Handling & Circuit Breakers

```mermaid
flowchart TD
    subgraph "🛡️ Error Handling System"
        subgraph "🟢 Normal Operation"
            NORMAL[Normal Operation]
            HEALTH[Health Checks]
            METRICS[Metrics Collection]
        end
        
        subgraph "🟡 Warning State"
            WARNING[Warning Threshold]
            DEGRADE[Degraded Performance]
            RETRY[Retry Logic]
        end
        
        subgraph "🔴 Circuit Breaker"
            BREAK[Circuit Breaker Open]
            FALLBACK[Fallback Mode]
            TIMEOUT[Timeout Protection]
        end
        
        subgraph "🔄 Recovery Mode"
            RECOVER[Recovery Attempt]
            TEST[Health Test]
            RESET[Reset Circuit]
        end
    end
    
    subgraph "🔧 Fallback Strategies"
        CACHE[Cache Fallback]
        AI_OFF[AI Disabled Mode]
        MANUAL[Manual Override]
        EMERGENCY[Emergency Protocol]
    end
    
    subgraph "📊 Monitoring"
        ALERT[Alert System]
        LOG[Error Logging]
        DASH[Dashboard Updates]
    end
    
    NORMAL --> HEALTH
    HEALTH --> WARNING
    WARNING --> BREAK
    BREAK --> RECOVER
    RECOVER --> NORMAL
    
    WARNING --> DEGRADE
    DEGRADE --> RETRY
    RETRY --> WARNING
    
    BREAK --> FALLBACK
    FALLBACK --> CACHE
    FALLBACK --> AI_OFF
    FALLBACK --> MANUAL
    FALLBACK --> EMERGENCY
    
    BREAK --> ALERT
    ALERT --> LOG
    LOG --> DASH
```

## 🎯 API Endpoints & Routes

```mermaid
graph LR
    subgraph "🎯 Mission Control API Gateway"
        subgraph "📊 Query Endpoints (Read)"
            PORT[/portfolio<br/>GET /api/v1/portfolio]
            POS[/positions<br/>GET /api/v1/positions]
            PERF[/performance<br/>GET /api/v1/performance]
            SIGNALS[/signals<br/>GET /api/v1/signals]
            MARKET[/market-data<br/>GET /api/v1/market-data]
            ANALYTICS[/analytics<br/>GET /api/v1/analytics]
        end
        
        subgraph "🚀 Command Endpoints (Write)"
            ORDER[/orders<br/>POST /api/v1/orders]
            TRADE[/trades<br/>POST /api/v1/trades]
            STRAT[/strategies<br/>POST /api/v1/strategies]
            CONFIG[/config<br/>PUT /api/v1/config]
            RISK[/risk-limits<br/>PUT /api/v1/risk-limits]
            PORTFOLIO[/portfolio<br/>PUT /api/v1/portfolio]
        end
        
        subgraph "🤖 AI Navigation Endpoints"
            AI_SIGNAL[/ai-signals<br/>GET /api/v1/ai-signals]
            AI_ANALYSIS[/ai-analysis<br/>POST /api/v1/ai-analysis]
            AI_CONSENSUS[/ai-consensus<br/>GET /api/v1/ai-consensus]
        end
        
        subgraph "🛰️ Backtesting Endpoints"
            BACKTEST[/backtest<br/>POST /api/v1/backtest]
            BACKTEST_RESULTS[/backtest-results<br/>GET /api/v1/backtest-results]
            BACKTEST_COMPARE[/backtest-compare<br/>GET /api/v1/backtest-compare]
        end
    end
```

## 📡 Data Pipeline Architecture

```mermaid
flowchart TD
    subgraph "📡 Data Ingestion Layer"
        POL[Polygon API]
        ALP[Alpha Vantage]
        NEWS[News APIs]
        USER[User Input]
    end
    
    subgraph "🔄 Data Processing Pipeline"
        VAL[Validation Layer]
        TRANS[Transformation Layer]
        ENRICH[Enrichment Layer]
        NORMALIZE[Normalization Layer]
    end
    
    subgraph "💾 Data Storage Tiers"
        HOT[Hot Storage<br/>Redis/In-Memory]
        WARM[Warm Storage<br/>PostgreSQL]
        COLD[Cold Storage<br/>Time Series DB]
        ARCHIVE[Archive Storage<br/>Object Storage]
    end
    
    subgraph "📊 Data Consumption"
        TRADING[Trading Engine]
        ANALYTICS[Analytics Engine]
        AI[AI Navigation Systems]
        REPORTING[Reporting Engine]
    end
    
    POL --> VAL
    ALP --> VAL
    NEWS --> VAL
    USER --> VAL
    
    VAL --> TRANS
    TRANS --> ENRICH
    ENRICH --> NORMALIZE
    
    NORMALIZE --> HOT
    HOT --> WARM
    WARM --> COLD
    COLD --> ARCHIVE
    
    HOT --> TRADING
    WARM --> ANALYTICS
    COLD --> AI
    ARCHIVE --> REPORTING
```

## 🧪 Testing & Quality Assurance Pipeline

```mermaid
flowchart TD
    subgraph "🧪 Testing Pipeline"
        subgraph "📝 Unit Testing"
            UNIT_CODE[Code Unit Tests]
            UNIT_LOGIC[Business Logic Tests]
            UNIT_UTILS[Utility Function Tests]
            UNIT_MODELS[Data Model Tests]
        end
        
        subgraph "🔗 Integration Testing"
            API_TESTS[API Integration Tests]
            DB_TESTS[Database Integration Tests]
            SERVICE_TESTS[Service Communication Tests]
            AI_TESTS[AI Service Integration]
        end
        
        subgraph "🛰️ Backtest Validation"
            STRATEGY_BACKTEST[Strategy Backtesting]
            PERFORMANCE_VALIDATION[Performance Validation]
            RISK_ASSESSMENT[Risk Assessment]
            ACCURACY_TESTING[Signal Accuracy Testing]
        end
        
        subgraph "⚡ Stress Testing"
            LOAD_TESTING[Load Testing]
            STRESS_TESTING[Stress Testing]
            FAILOVER_TESTING[Failover Testing]
            RECOVERY_TESTING[Recovery Testing]
        end
    end
    
    subgraph "📊 Quality Gates"
        subgraph "📈 Code Quality"
            COVERAGE[Code Coverage > 80%]
            LINTING[Code Linting]
            SECURITY_SCAN[Security Scanning]
            PERFORMANCE_BENCH[Performance Benchmarks]
        end
        
        subgraph "🚀 Deployment Quality"
            DEPLOYMENT_TEST[Deployment Testing]
            ROLLBACK_TEST[Rollback Testing]
            HEALTH_CHECK[Health Check Validation]
            MONITORING_SETUP[Monitoring Setup]
        end
        
        subgraph "🎯 Trading Quality"
            SIGNAL_ACCURACY[Signal Accuracy > 60%]
            RISK_LIMITS[Risk Limit Compliance]
            PERFORMANCE_METRICS[Performance Metrics]
            PROFIT_VALIDATION[Profit/Loss Validation]
        end
    end
    
    UNIT_CODE --> API_TESTS
    UNIT_LOGIC --> SERVICE_TESTS
    UNIT_UTILS --> DB_TESTS
    UNIT_MODELS --> AI_TESTS
    
    API_TESTS --> STRATEGY_BACKTEST
    DB_TESTS --> PERFORMANCE_VALIDATION
    SERVICE_TESTS --> RISK_ASSESSMENT
    AI_TESTS --> ACCURACY_TESTING
    
    STRATEGY_BACKTEST --> LOAD_TESTING
    PERFORMANCE_VALIDATION --> STRESS_TESTING
    RISK_ASSESSMENT --> FAILOVER_TESTING
    ACCURACY_TESTING --> RECOVERY_TESTING
    
    LOAD_TESTING --> COVERAGE
    STRESS_TESTING --> LINTING
    FAILOVER_TESTING --> SECURITY_SCAN
    RECOVERY_TESTING --> PERFORMANCE_BENCH
    
    COVERAGE --> DEPLOYMENT_TEST
    LINTING --> ROLLBACK_TEST
    SECURITY_SCAN --> HEALTH_CHECK
    PERFORMANCE_BENCH --> MONITORING_SETUP
    
    DEPLOYMENT_TEST --> SIGNAL_ACCURACY
    ROLLBACK_TEST --> RISK_LIMITS
    HEALTH_CHECK --> PERFORMANCE_METRICS
    MONITORING_SETUP --> PROFIT_VALIDATION
```

## 🔐 Security & Compliance Architecture

```mermaid
graph TB
    subgraph "🔐 Security Layers"
        subgraph "🛡️ Authentication"
            OAUTH[OAuth 2.0]
            JWT[JWT Tokens]
            MFA[Multi-Factor Auth]
            SSO[Single Sign-On]
        end
        
        subgraph "🔒 Authorization"
            RBAC[Role-Based Access Control]
            ABAC[Attribute-Based Access Control]
            API_KEYS[API Key Management]
            PERMISSIONS[Permission Matrix]
        end
        
        subgraph "🔐 Encryption"
            TLS[TLS/SSL Encryption]
            DATA_AT_REST[Data at Rest Encryption]
            DATA_IN_TRANSIT[Data in Transit Encryption]
            KEY_MANAGEMENT[Key Management]
        end
        
        subgraph "📝 Audit & Logging"
            AUDIT_LOGS[Audit Logging]
            ACCESS_LOGS[Access Logging]
            TRADE_LOGS[Trade Logging]
            COMPLIANCE_LOGS[Compliance Logging]
        end
    end
    
    subgraph "📋 Compliance Framework"
        subgraph "🏦 Financial Compliance"
            SOX[SOX Compliance]
            FINRA[FINRA Rules]
            PCI[PCI DSS]
            GLBA[GLBA Compliance]
        end
        
        subgraph "🌍 Data Protection"
            GDPR[GDPR Compliance]
            CCPA[CCPA Compliance]
            DATA_RETENTION[Data Retention Policies]
            PRIVACY[Privacy Controls]
        end
        
        subgraph "🔍 Regulatory Reporting"
            TRADE_REPORTS[Trade Reports]
            RISK_REPORTS[Risk Reports]
            COMPLIANCE_REPORTS[Compliance Reports]
            AUDIT_REPORTS[Audit Reports]
        end
    end
    
    subgraph "🛡️ Security Controls"
        subgraph "🚨 Threat Detection"
            INTRUSION[Intrusion Detection]
            ANOMALY[Anomaly Detection]
            MALWARE[Malware Protection]
            DDoS[DDoS Protection]
        end
        
        subgraph "🔄 Incident Response"
            INCIDENT_RESPONSE[Incident Response Plan]
            FORENSICS[Digital Forensics]
            RECOVERY[Disaster Recovery]
            BUSINESS_CONTINUITY[Business Continuity]
        end
    end
    
    OAUTH --> RBAC
    JWT --> ABAC
    MFA --> API_KEYS
    SSO --> PERMISSIONS
    
    RBAC --> TLS
    ABAC --> DATA_AT_REST
    API_KEYS --> DATA_IN_TRANSIT
    PERMISSIONS --> KEY_MANAGEMENT
    
    TLS --> AUDIT_LOGS
    DATA_AT_REST --> ACCESS_LOGS
    DATA_IN_TRANSIT --> TRADE_LOGS
    KEY_MANAGEMENT --> COMPLIANCE_LOGS
    
    AUDIT_LOGS --> SOX
    ACCESS_LOGS --> FINRA
    TRADE_LOGS --> PCI
    COMPLIANCE_LOGS --> GLBA
    
    SOX --> GDPR
    FINRA --> CCPA
    PCI --> DATA_RETENTION
    GLBA --> PRIVACY
    
    GDPR --> TRADE_REPORTS
    CCPA --> RISK_REPORTS
    DATA_RETENTION --> COMPLIANCE_REPORTS
    PRIVACY --> AUDIT_REPORTS
    
    TRADE_REPORTS --> INTRUSION
    RISK_REPORTS --> ANOMALY
    COMPLIANCE_REPORTS --> MALWARE
    AUDIT_REPORTS --> DDoS
    
    INTRUSION --> INCIDENT_RESPONSE
    ANOMALY --> FORENSICS
    MALWARE --> RECOVERY
    DDoS --> BUSINESS_CONTINUITY
```

## 📈 Performance Monitoring & Alerting

```mermaid
flowchart TD
    subgraph "📊 Performance Metrics"
        subgraph "⚡ Trading Performance"
            LATENCY[Trading Latency < 100ms]
            THROUGHPUT[Order Throughput > 1000/sec]
            ACCURACY[Signal Accuracy > 60%]
            PROFIT[Profit/Loss Tracking]
        end
        
        subgraph "🤖 AI Performance"
            AI_LATENCY[AI Response Time < 5s]
            AI_ACCURACY[AI Prediction Accuracy]
            MODEL_PERFORMANCE[Model Performance]
            TRAINING_METRICS[Training Metrics]
        end
        
        subgraph "📊 System Performance"
            CPU_USAGE[CPU Usage < 80%]
            MEMORY_USAGE[Memory Usage < 85%]
            DISK_IO[Disk I/O Performance]
            NETWORK_LATENCY[Network Latency]
        end
    end
    
    subgraph "🚨 Alerting System"
        subgraph "🔴 Critical Alerts"
            SYSTEM_DOWN[System Down]
            TRADING_STOPPED[Trading Stopped]
            SECURITY_BREACH[Security Breach]
            COMPLIANCE_VIOLATION[Compliance Violation]
        end
        
        subgraph "🟡 Warning Alerts"
            HIGH_LATENCY[High Latency]
            LOW_ACCURACY[Low Signal Accuracy]
            HIGH_ERROR_RATE[High Error Rate]
            RESOURCE_CONSTRAINTS[Resource Constraints]
        end
        
        subgraph "🟢 Info Notifications"
            DEPLOYMENT_SUCCESS[Deployment Success]
            BACKUP_COMPLETE[Backup Complete]
            MAINTENANCE_SCHEDULED[Maintenance Scheduled]
            PERFORMANCE_IMPROVEMENT[Performance Improvement]
        end
        
        subgraph "🔄 Auto-Recovery"
            AUTO_RESTART[Auto Restart Services]
            LOAD_BALANCING[Load Balancing]
            FAILOVER[Automatic Failover]
            SCALING[Auto Scaling]
        end
    end
    
    subgraph "📈 Monitoring Dashboard"
        subgraph "🎯 Mission Control"
            REAL_TIME_METRICS[Real-time Metrics]
            ALERT_HISTORY[Alert History]
            SYSTEM_STATUS[System Status]
            PERFORMANCE_TRENDS[Performance Trends]
        end
        
        subgraph "📊 Trading Dashboard"
            PORTFOLIO_VALUE[Portfolio Value]
            TRADING_SIGNALS[Trading Signals]
            RISK_METRICS[Risk Metrics]
            PROFIT_LOSS[Profit/Loss]
        end
    end
    
    LATENCY --> SYSTEM_DOWN
    THROUGHPUT --> TRADING_STOPPED
    ACCURACY --> SECURITY_BREACH
    PROFIT --> COMPLIANCE_VIOLATION
    
    AI_LATENCY --> HIGH_LATENCY
    AI_ACCURACY --> LOW_ACCURACY
    MODEL_PERFORMANCE --> HIGH_ERROR_RATE
    TRAINING_METRICS --> RESOURCE_CONSTRAINTS
    
    CPU_USAGE --> DEPLOYMENT_SUCCESS
    MEMORY_USAGE --> BACKUP_COMPLETE
    DISK_IO --> MAINTENANCE_SCHEDULED
    NETWORK_LATENCY --> PERFORMANCE_IMPROVEMENT
    
    SYSTEM_DOWN --> AUTO_RESTART
    TRADING_STOPPED --> LOAD_BALANCING
    SECURITY_BREACH --> FAILOVER
    COMPLIANCE_VIOLATION --> SCALING
    
    AUTO_RESTART --> REAL_TIME_METRICS
    LOAD_BALANCING --> ALERT_HISTORY
    FAILOVER --> SYSTEM_STATUS
    SCALING --> PERFORMANCE_TRENDS
    
    REAL_TIME_METRICS --> PORTFOLIO_VALUE
    ALERT_HISTORY --> TRADING_SIGNALS
    SYSTEM_STATUS --> RISK_METRICS
    PERFORMANCE_TRENDS --> PROFIT_LOSS
```

## 🔄 CI/CD Pipeline

```mermaid
graph LR
    subgraph "🔄 Development Pipeline"
        subgraph "👨‍💻 Development"
            CODE[Code Changes]
            REVIEW[Code Review]
            BRANCH[Feature Branch]
            MERGE[Merge to Main]
        end
        
        subgraph "🧪 Testing"
            UNIT_TEST[Unit Tests]
            INTEGRATION_TEST[Integration Tests]
            BACKTEST_VALIDATION[Backtest Validation]
            SECURITY_SCAN[Security Scan]
        end
        
        subgraph "🐳 Build & Package"
            DOCKER_BUILD[Docker Build]
            IMAGE_TAG[Image Tagging]
            REGISTRY_PUSH[Registry Push]
            ARTIFACT_STORE[Artifact Store]
        end
        
        subgraph "☸️ Deployment"
            K8S_DEPLOY[Kubernetes Deploy]
            HEALTH_CHECK[Health Check]
            ROLLBACK[Rollback if Failed]
            MONITOR[Monitor Deployment]
        end
    end
    
    subgraph "🚀 Production Pipeline"
        subgraph "🎯 Staging"
            STAGING_DEPLOY[Staging Deploy]
            STAGING_TEST[Staging Tests]
            PERFORMANCE_TEST[Performance Tests]
            USER_ACCEPTANCE[User Acceptance]
        end
        
        subgraph "🚀 Production"
            PROD_DEPLOY[Production Deploy]
            BLUE_GREEN[Blue-Green Deployment]
            CANARY[Canary Deployment]
            MONITORING[Production Monitoring]
        end
    end
    
    CODE --> REVIEW
    REVIEW --> BRANCH
    BRANCH --> MERGE
    
    MERGE --> UNIT_TEST
    UNIT_TEST --> INTEGRATION_TEST
    INTEGRATION_TEST --> BACKTEST_VALIDATION
    BACKTEST_VALIDATION --> SECURITY_SCAN
    
    SECURITY_SCAN --> DOCKER_BUILD
    DOCKER_BUILD --> IMAGE_TAG
    IMAGE_TAG --> REGISTRY_PUSH
    REGISTRY_PUSH --> ARTIFACT_STORE
    
    ARTIFACT_STORE --> K8S_DEPLOY
    K8S_DEPLOY --> HEALTH_CHECK
    HEALTH_CHECK --> ROLLBACK
    ROLLBACK --> MONITOR
    
    MONITOR --> STAGING_DEPLOY
    STAGING_DEPLOY --> STAGING_TEST
    STAGING_TEST --> PERFORMANCE_TEST
    PERFORMANCE_TEST --> USER_ACCEPTANCE
    
    USER_ACCEPTANCE --> PROD_DEPLOY
    PROD_DEPLOY --> BLUE_GREEN
    BLUE_GREEN --> CANARY
    CANARY --> MONITORING
```

## 🗄️ Data Lifecycle Management

```mermaid
flowchart TD
    subgraph "📥 Data Ingestion"
        subgraph "⚡ Real-time Data"
            MARKET_DATA[Market Data Streams]
            NEWS_FEEDS[News Feeds]
            TRADING_SIGNALS[Trading Signals]
            USER_INPUT[User Input]
        end
        
        subgraph "📦 Batch Processing"
            HISTORICAL_DATA[Historical Data]
            BACKTEST_DATA[Backtest Data]
            ANALYTICS_DATA[Analytics Data]
            REPORTING_DATA[Reporting Data]
        end
        
        subgraph "🌊 Stream Processing"
            REAL_TIME_ANALYTICS[Real-time Analytics]
            EVENT_STREAMS[Event Streams]
            ALERT_STREAMS[Alert Streams]
            MONITORING_STREAMS[Monitoring Streams]
        end
    end
    
    subgraph "💾 Data Storage"
        subgraph "🔥 Hot Storage"
            REDIS[Redis Cache]
            IN_MEMORY[In-Memory Storage]
            TEMP_DATA[Temporary Data]
            SESSION_DATA[Session Data]
        end
        
        subgraph "🌡️ Warm Storage"
            POSTGRESQL[PostgreSQL]
            TIMESERIES[Time Series DB]
            ANALYTICS_DB[Analytics Database]
            USER_DB[User Database]
        end
        
        subgraph "❄️ Cold Storage"
            ARCHIVE_DB[Archive Database]
            BACKUP_STORAGE[Backup Storage]
            COMPLIANCE_DATA[Compliance Data]
            HISTORICAL_ARCHIVE[Historical Archive]
        end
        
        subgraph "🗄️ Archive Storage"
            OBJECT_STORAGE[Object Storage]
            LONG_TERM_ARCHIVE[Long-term Archive]
            COMPLIANCE_ARCHIVE[Compliance Archive]
            DISASTER_RECOVERY[Disaster Recovery]
        end
    end
    
    subgraph "📊 Data Consumption"
        subgraph "🚀 Trading Engine"
            REAL_TIME_TRADING[Real-time Trading]
            SIGNAL_GENERATION[Signal Generation]
            ORDER_EXECUTION[Order Execution]
            RISK_MANAGEMENT[Risk Management]
        end
        
        subgraph "📈 Analytics"
            PERFORMANCE_ANALYTICS[Performance Analytics]
            RISK_ANALYTICS[Risk Analytics]
            USER_ANALYTICS[User Analytics]
            BUSINESS_ANALYTICS[Business Analytics]
        end
        
        subgraph "📋 Reporting"
            TRADING_REPORTS[Trading Reports]
            COMPLIANCE_REPORTS[Compliance Reports]
            PERFORMANCE_REPORTS[Performance Reports]
            EXECUTIVE_REPORTS[Executive Reports]
        end
        
        subgraph "🤖 AI Training"
            MODEL_TRAINING[Model Training]
            DATA_LABELING[Data Labeling]
            FEATURE_ENGINEERING[Feature Engineering]
            MODEL_VALIDATION[Model Validation]
        end
    end
    
    MARKET_DATA --> REDIS
    NEWS_FEEDS --> IN_MEMORY
    TRADING_SIGNALS --> TEMP_DATA
    USER_INPUT --> SESSION_DATA
    
    HISTORICAL_DATA --> POSTGRESQL
    BACKTEST_DATA --> TIMESERIES
    ANALYTICS_DATA --> ANALYTICS_DB
    REPORTING_DATA --> USER_DB
    
    REAL_TIME_ANALYTICS --> ARCHIVE_DB
    EVENT_STREAMS --> BACKUP_STORAGE
    ALERT_STREAMS --> COMPLIANCE_DATA
    MONITORING_STREAMS --> HISTORICAL_ARCHIVE
    
    REDIS --> REAL_TIME_TRADING
    IN_MEMORY --> SIGNAL_GENERATION
    TEMP_DATA --> ORDER_EXECUTION
    SESSION_DATA --> RISK_MANAGEMENT
    
    POSTGRESQL --> PERFORMANCE_ANALYTICS
    TIMESERIES --> RISK_ANALYTICS
    ANALYTICS_DB --> USER_ANALYTICS
    USER_DB --> BUSINESS_ANALYTICS
    
    ARCHIVE_DB --> TRADING_REPORTS
    BACKUP_STORAGE --> COMPLIANCE_REPORTS
    COMPLIANCE_DATA --> PERFORMANCE_REPORTS
    HISTORICAL_ARCHIVE --> EXECUTIVE_REPORTS
    
    OBJECT_STORAGE --> MODEL_TRAINING
    LONG_TERM_ARCHIVE --> DATA_LABELING
    COMPLIANCE_ARCHIVE --> FEATURE_ENGINEERING
    DISASTER_RECOVERY --> MODEL_VALIDATION
```

## 🌐 Network & Communication Architecture

```mermaid
graph TB
    subgraph "🌐 Network Layers"
        subgraph "🌍 External Layer"
            INTERNET[Internet]
            CDN[Content Delivery Network]
            DNS[DNS Services]
            SSL[SSL/TLS Termination]
        end
        
        subgraph "⚖️ Load Balancing"
            LB[Load Balancer]
            HEALTH_CHECK[Health Checks]
            TRAFFIC_ROUTING[Traffic Routing]
            FAILOVER[Failover Management]
        end
        
        subgraph "🚪 API Gateway"
            API_GATEWAY[API Gateway]
            RATE_LIMITING[Rate Limiting]
            AUTHENTICATION[Authentication]
            ROUTING[Request Routing]
        end
        
        subgraph "🔗 Service Mesh"
            SERVICE_MESH[Service Mesh]
            SERVICE_DISCOVERY[Service Discovery]
            LOAD_BALANCING[Load Balancing]
            CIRCUIT_BREAKER[Circuit Breaker]
        end
        
        subgraph "🗄️ Database Layer"
            DB_PROXY[Database Proxy]
            CONNECTION_POOL[Connection Pooling]
            READ_REPLICAS[Read Replicas]
            BACKUP_DB[Backup Database]
        end
    end
    
    subgraph "🔗 Communication Protocols"
        subgraph "📡 REST APIs"
            HTTP[HTTP/HTTPS]
            JSON[JSON Payloads]
            REST_ENDPOINTS[REST Endpoints]
            API_VERSIONING[API Versioning]
        end
        
        subgraph "⚡ gRPC"
            GRPC[gRPC Protocol]
            PROTOBUF[Protocol Buffers]
            STREAMING[Streaming]
            BIDIRECTIONAL[Bidirectional]
        end
        
        subgraph "📨 Message Queue"
            RABBITMQ[RabbitMQ]
            KAFKA[Apache Kafka]
            REDIS_PUBSUB[Redis Pub/Sub]
            EVENT_STREAM[Event Streams]
        end
        
        subgraph "🔌 WebSocket"
            WEBSOCKET[WebSocket]
            REAL_TIME[Real-time Updates]
            PUSH_NOTIFICATIONS[Push Notifications]
            LIVE_DASHBOARD[Live Dashboard]
        end
    end
    
    subgraph "🛡️ Security & Monitoring"
        subgraph "🔐 Security"
            WAF[Web Application Firewall]
            DDoS_PROTECTION[DDoS Protection]
            VPN[VPN Access]
            FIREWALL[Firewall Rules]
        end
        
        subgraph "📊 Monitoring"
            NETWORK_MONITOR[Network Monitoring]
            TRAFFIC_ANALYSIS[Traffic Analysis]
            PERFORMANCE_METRICS[Performance Metrics]
            ALERTING[Network Alerting]
        end
    end
    
    INTERNET --> LB
    CDN --> HEALTH_CHECK
    DNS --> TRAFFIC_ROUTING
    SSL --> FAILOVER
    
    LB --> API_GATEWAY
    HEALTH_CHECK --> RATE_LIMITING
    TRAFFIC_ROUTING --> AUTHENTICATION
    FAILOVER --> ROUTING
    
    API_GATEWAY --> SERVICE_MESH
    RATE_LIMITING --> SERVICE_DISCOVERY
    AUTHENTICATION --> LOAD_BALANCING
    ROUTING --> CIRCUIT_BREAKER
    
    SERVICE_MESH --> DB_PROXY
    SERVICE_DISCOVERY --> CONNECTION_POOL
    LOAD_BALANCING --> READ_REPLICAS
    CIRCUIT_BREAKER --> BACKUP_DB
    
    DB_PROXY --> HTTP
    CONNECTION_POOL --> JSON
    READ_REPLICAS --> REST_ENDPOINTS
    BACKUP_DB --> API_VERSIONING
    
    HTTP --> GRPC
    JSON --> PROTOBUF
    REST_ENDPOINTS --> STREAMING
    API_VERSIONING --> BIDIRECTIONAL
    
    GRPC --> RABBITMQ
    PROTOBUF --> KAFKA
    STREAMING --> REDIS_PUBSUB
    BIDIRECTIONAL --> EVENT_STREAM
    
    RABBITMQ --> WEBSOCKET
    KAFKA --> REAL_TIME
    REDIS_PUBSUB --> PUSH_NOTIFICATIONS
    EVENT_STREAM --> LIVE_DASHBOARD
    
    WEBSOCKET --> WAF
    REAL_TIME --> DDoS_PROTECTION
    PUSH_NOTIFICATIONS --> VPN
    LIVE_DASHBOARD --> FIREWALL
    
    WAF --> NETWORK_MONITOR
    DDoS_PROTECTION --> TRAFFIC_ANALYSIS
    VPN --> PERFORMANCE_METRICS
    FIREWALL --> ALERTING
```

## 📊 Business Intelligence & Reporting

```mermaid
flowchart TD
    subgraph "📊 Data Sources"
        subgraph "📈 Trading Data"
            TRADES[Trading Records]
            ORDERS[Order History]
            POSITIONS[Position Data]
            P&L[Profit & Loss]
        end
        
        subgraph "📰 News Data"
            NEWS_EVENTS[News Events]
            SENTIMENT[Sentiment Scores]
            IMPACT_ANALYSIS[Impact Analysis]
            EVENT_CLASSIFICATION[Event Classification]
        end
        
        subgraph "📊 Market Data"
            PRICE_DATA[Price Data]
            VOLUME_DATA[Volume Data]
            TECHNICAL_INDICATORS[Technical Indicators]
            MARKET_SENTIMENT[Market Sentiment]
        end
        
        subgraph "👤 User Data"
            USER_PROFILES[User Profiles]
            TRADING_PREFERENCES[Trading Preferences]
            PERFORMANCE_HISTORY[Performance History]
            RISK_PROFILES[Risk Profiles]
        end
    end
    
    subgraph "🔄 Data Processing"
        subgraph "🧹 Data Cleaning"
            VALIDATION[Data Validation]
            NORMALIZATION[Data Normalization]
            DEDUPLICATION[Deduplication]
            ENRICHMENT[Data Enrichment]
        end
        
        subgraph "📊 Data Transformation"
            AGGREGATION[Data Aggregation]
            CALCULATION[Calculations]
            FEATURE_ENGINEERING[Feature Engineering]
            DIMENSION_MODELING[Dimension Modeling]
        end
        
        subgraph "💾 Data Storage"
            DATA_WAREHOUSE[Data Warehouse]
            DATA_MARTS[Data Marts]
            OLAP_CUBES[OLAP Cubes]
            CACHE_LAYER[Cache Layer]
        end
    end
    
    subgraph "📈 Analytics & Insights"
        subgraph "📊 Dashboards"
            EXECUTIVE_DASHBOARD[Executive Dashboard]
            TRADING_DASHBOARD[Trading Dashboard]
            RISK_DASHBOARD[Risk Dashboard]
            PERFORMANCE_DASHBOARD[Performance Dashboard]
        end
        
        subgraph "📋 Reports"
            DAILY_REPORTS[Daily Reports]
            WEEKLY_REPORTS[Weekly Reports]
            MONTHLY_REPORTS[Monthly Reports]
            QUARTERLY_REPORTS[Quarterly Reports]
        end
        
        subgraph "🚨 Alerts"
            PERFORMANCE_ALERTS[Performance Alerts]
            RISK_ALERTS[Risk Alerts]
            COMPLIANCE_ALERTS[Compliance Alerts]
            BUSINESS_ALERTS[Business Alerts]
        end
        
        subgraph "🔍 Insights"
            TREND_ANALYSIS[Trend Analysis]
            PATTERN_RECOGNITION[Pattern Recognition]
            PREDICTIVE_ANALYTICS[Predictive Analytics]
            RECOMMENDATIONS[Recommendations]
        end
    end
    
    TRADES --> VALIDATION
    ORDERS --> NORMALIZATION
    POSITIONS --> DEDUPLICATION
    P&L --> ENRICHMENT
    
    NEWS_EVENTS --> AGGREGATION
    SENTIMENT --> CALCULATION
    IMPACT_ANALYSIS --> FEATURE_ENGINEERING
    EVENT_CLASSIFICATION --> DIMENSION_MODELING
    
    PRICE_DATA --> DATA_WAREHOUSE
    VOLUME_DATA --> DATA_MARTS
    TECHNICAL_INDICATORS --> OLAP_CUBES
    MARKET_SENTIMENT --> CACHE_LAYER
    
    USER_PROFILES --> EXECUTIVE_DASHBOARD
    TRADING_PREFERENCES --> TRADING_DASHBOARD
    PERFORMANCE_HISTORY --> RISK_DASHBOARD
    RISK_PROFILES --> PERFORMANCE_DASHBOARD
    
    VALIDATION --> DAILY_REPORTS
    NORMALIZATION --> WEEKLY_REPORTS
    DEDUPLICATION --> MONTHLY_REPORTS
    ENRICHMENT --> QUARTERLY_REPORTS
    
    AGGREGATION --> PERFORMANCE_ALERTS
    CALCULATION --> RISK_ALERTS
    FEATURE_ENGINEERING --> COMPLIANCE_ALERTS
    DIMENSION_MODELING --> BUSINESS_ALERTS
    
    DATA_WAREHOUSE --> TREND_ANALYSIS
    DATA_MARTS --> PATTERN_RECOGNITION
    OLAP_CUBES --> PREDICTIVE_ANALYTICS
    CACHE_LAYER --> RECOMMENDATIONS
```

## 🎯 Strategy Performance Comparison

```mermaid
graph LR
    subgraph "📈 Strategy Performance"
        subgraph "🤖 AI Enhanced Strategies"
            RSI_AI[RSI AI Enhanced]
            MACD_AI[MACD AI Enhanced]
            BB_AI[Bollinger Bands AI]
            NEWS_AI[News Enhanced]
        end
        
        subgraph "📊 Traditional Strategies"
            RSI_TRAD[RSI Traditional]
            MACD_TRAD[MACD Traditional]
            BB_TRAD[Bollinger Traditional]
            SMA_TRAD[SMA Crossover]
        end
    end
    
    subgraph "📊 Performance Metrics"
        subgraph "📈 Return Metrics"
            TOTAL_RETURN[Total Return]
            ANNUAL_RETURN[Annual Return]
            RISK_ADJUSTED[Risk-Adjusted Return]
            ALPHA[Alpha]
        end
        
        subgraph "🛡️ Risk Metrics"
            SHARPE_RATIO[Sharpe Ratio]
            MAX_DRAWDOWN[Max Drawdown]
            VOLATILITY[Volatility]
            VAR[Value at Risk]
        end
        
        subgraph "📊 Trading Metrics"
            WIN_RATE[Win Rate]
            PROFIT_FACTOR[Profit Factor]
            AVERAGE_WIN[Average Win]
            AVERAGE_LOSS[Average Loss]
        end
        
        subgraph "⏱️ Efficiency Metrics"
            TRADE_FREQUENCY[Trade Frequency]
            HOLDING_PERIOD[Holding Period]
            TRANSACTION_COST[Transaction Cost]
            SLIPPAGE[Slippage]
        end
    end
    
    subgraph "📊 Comparison Dashboard"
        subgraph "🎯 Performance Ranking"
            TOP_PERFORMER[Top Performer]
            CONSISTENT[Most Consistent]
            LOW_RISK[Lowest Risk]
            HIGH_RETURN[Highest Return]
        end
        
        subgraph "📈 Trend Analysis"
            PERFORMANCE_TREND[Performance Trend]
            RISK_TREND[Risk Trend]
            CORRELATION[Strategy Correlation]
            DIVERSIFICATION[Diversification Benefit]
        end
    end
    
    RSI_AI --> TOTAL_RETURN
    MACD_AI --> ANNUAL_RETURN
    BB_AI --> RISK_ADJUSTED
    NEWS_AI --> ALPHA
    
    RSI_TRAD --> SHARPE_RATIO
    MACD_TRAD --> MAX_DRAWDOWN
    BB_TRAD --> VOLATILITY
    SMA_TRAD --> VAR
    
    TOTAL_RETURN --> WIN_RATE
    ANNUAL_RETURN --> PROFIT_FACTOR
    RISK_ADJUSTED --> AVERAGE_WIN
    ALPHA --> AVERAGE_LOSS
    
    SHARPE_RATIO --> TRADE_FREQUENCY
    MAX_DRAWDOWN --> HOLDING_PERIOD
    VOLATILITY --> TRANSACTION_COST
    VAR --> SLIPPAGE
    
    WIN_RATE --> TOP_PERFORMER
    PROFIT_FACTOR --> CONSISTENT
    AVERAGE_WIN --> LOW_RISK
    AVERAGE_LOSS --> HIGH_RETURN
    
    TRADE_FREQUENCY --> PERFORMANCE_TREND
    HOLDING_PERIOD --> RISK_TREND
    TRANSACTION_COST --> CORRELATION
    SLIPPAGE --> DIVERSIFICATION
```

## 🚀 Current System Configuration (July 2025)

### **📡 Port Configuration & Service Mapping**

| Service | External Port | Internal Port | Status | Recent Changes |
|---------|---------------|---------------|---------|----------------|
| Performance Dashboard | 11000 | 80 | ✅ Running | Registry fix |
| Trading Dashboard | 11001 | 8000 | ✅ Running | Registry fix |
| Health Dashboard | 11002 | 80 | ✅ Running | Registry fix |
| **RSS Dashboard** | **11003** | **80** | **✅ Running** | **NEW** |
| Backtest Request | 11031 | 80 | ✅ Running | Registry fix |
| **LLM Proxy** | **12001** | **11434** | **✅ Running** | **NEW** |

### **🔧 Infrastructure Services**

| Service | Port | Status | Notes |
|---------|------|---------|-------|
| Docker Registry | 32000 | ✅ Running | NodePort (Fixed) |
| RabbitMQ | 5672 | ✅ Running | Message Queue |
| PostgreSQL | 5432 | ✅ Running | Database |
| Redis | 6379 | ✅ Running | Cache |

### **🎯 Recent Architecture Updates**

#### **✅ July 2025 Changes**

1. **🔧 Registry Port Configuration Fix**
   - **Problem**: Docker registry accessible on port 32000 but build scripts used port 5000
   - **Solution**: Updated all build/push commands to use `localhost:32000`
   - **Impact**: All Docker builds now work correctly

2. **📰 RSS Dashboard Addition**
   - **New Service**: Complete RSS dashboard for trading recommendations
   - **Features**: Real-time recommendations, multiple feed types, auto-refresh
   - **URL**: `http://localhost:11003/`

3. **🤖 LLM Proxy Integration**
   - **New Service**: LLM Proxy for external access to Ollama
   - **Port**: `localhost:12001`
   - **Integration**: Connects to internal Ollama LLM service

4. **🔄 Port Forwarding Stability**
   - **Improvement**: Robust port forwarding with auto-restart
   - **Features**: Auto-restart on failure, proactive monitoring
   - **Result**: All dashboards now accessible

### **📊 Health Check Endpoints**

All services now have working health endpoints:
- `http://localhost:11000/health` - Performance Dashboard
- `http://localhost:11001/health` - Trading Dashboard  
- `http://localhost:11002/health` - Health Dashboard
- `http://localhost:11003/health` - RSS Dashboard
- `http://localhost:12001/health` - LLM Proxy

### **🔍 Registry Health**
- Registry Catalog: `http://localhost:32000/v2/_catalog`
- Registry Status: `kubectl get svc registry -n default`

---

*"This is ORION, Mission Control. All Space Trading Station architecture diagrams are now available for navigation!"* 🚀 