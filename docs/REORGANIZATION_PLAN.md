# 🗂️ Repository Reorganization Plan

## 🎯 Goals
- **Clear separation** of concerns
- **Easy onboarding** for new users
- **Logical grouping** of related files
- **Reduced cognitive load** when exploring the repo

## 📁 Proposed New Structure

```
space-trading-station/
├── 📋 ONBOARDING & QUICK START
│   ├── README.md                    # Main project overview
│   ├── QUICKSTART.md               # 5-minute setup guide
│   ├── SETUP.md                    # Detailed setup instructions
│   └── CONTRIBUTING.md             # How to contribute
│
├── 🚀 CORE APPLICATION
│   ├── src/                        # Main application code
│   │   ├── api/                    # API endpoints
│   │   ├── core/                   # Core trading logic
│   │   ├── strategies/             # Trading strategies
│   │   ├── services/               # Business services
│   │   └── utils/                  # Utilities
│   ├── services/                   # Microservices
│   └── tests/                      # Test suite
│
├── 🎮 DEMOS & EXAMPLES
│   ├── demos/                      # All demo scripts
│   │   ├── monitor/                # Monitor demos
│   │   ├── api/                    # API demos
│   │   ├── backtest/               # Backtest demos
│   │   └── strategies/             # Strategy demos
│   └── examples/                   # Code examples
│
├── 📊 ANALYSIS & TOOLS
│   ├── analysis/                   # Analysis scripts
│   │   ├── performance/            # Performance analysis
│   │   ├── portfolio/              # Portfolio analysis
│   │   └── backtest/               # Backtest analysis
│   ├── tools/                      # Utility tools
│   │   ├── data/                   # Data tools
│   │   ├── testing/                # Testing tools
│   │   └── debugging/              # Debugging tools
│   └── notebooks/                  # Jupyter notebooks
│
├── 🐳 DEPLOYMENT & INFRASTRUCTURE
│   ├── k8s/                        # Kubernetes manifests
│   ├── docker/                     # Docker files
│   │   ├── services/               # Service Dockerfiles
│   │   └── development/            # Dev Dockerfiles
│   ├── scripts/                    # Deployment scripts
│   │   ├── deploy/                 # Deployment scripts
│   │   ├── setup/                  # Setup scripts
│   │   └── maintenance/            # Maintenance scripts
│   └── config/                     # Configuration files
│
├── 📚 DOCUMENTATION
│   ├── guides/                     # Detailed guides
│   │   ├── architecture/           # Architecture docs
│   │   ├── deployment/             # Deployment guides
│   │   ├── development/            # Development guides
│   │   └── monitoring/             # Monitoring guides
│   ├── api/                        # API documentation
│   ├── tutorials/                  # Step-by-step tutorials
│   └── reference/                  # Reference materials
│
├── 🔧 DEVELOPMENT TOOLS
│   ├── Makefile                    # Main Makefile
│   ├── Makefile.*                  # Modular Makefiles
│   ├── requirements.txt             # Python dependencies
│   ├── setup.py                    # Package setup
│   └── .env.example               # Environment template
│
└── 📁 DATA & LOGS
    ├── data/                       # Data files
    ├── logs/                       # Log files
    └── backups/                    # Backup files
```

## 📋 File Migration Plan

### **Root Directory Cleanup**

#### **Move to `demos/`**
```
demo_*.py → demos/
├── demos/monitor/
│   ├── demo_monitor.py
│   ├── demo_monitor_with_api.py
│   └── space_station_monitor.py
├── demos/api/
│   └── demo_backtest_api.py
├── demos/backtest/
│   ├── demo_news_backtest.py
│   ├── demo_llm_trading_strategy.py
│   └── demo_all_ai_strategies.py
└── demos/strategies/
    └── (strategy-specific demos)
```

#### **Move to `analysis/`**
```
analyze_*.py → analysis/performance/
run_*_backtest.py → analysis/backtest/
test_*.py → tools/testing/
scan_*.py → tools/data/
populate_*.py → tools/data/
fetch_*.py → tools/data/
```

#### **Move to `tools/`**
```
debug_*.py → tools/debugging/
verify_*.py → tools/testing/
setup_*.sh → scripts/setup/
fix_*.py → tools/debugging/
fix_*.sh → scripts/maintenance/
```

#### **Move to `config/`**
```
*.env.example → config/
alembic.ini → config/
pytest.ini → config/
.dockerignore → config/
.pre-commit-config.yaml → config/
```

#### **Move to `docker/`**
```
Dockerfile.* → docker/development/
docker-compose.*.yml → docker/
```

#### **Move to `scripts/`**
```
deploy-*.sh → scripts/deploy/
quick-start*.sh → scripts/setup/
run_*.sh → scripts/deploy/
```

#### **Move to `docs/guides/`**
```
*_GUIDE.md → docs/guides/
AI_ENHANCED_STRATEGIES_GUIDE.md → docs/guides/strategies/
```

### **Create New Directories**

#### **`demos/` Structure**
```
demos/
├── monitor/
│   ├── README.md
│   ├── demo_monitor.py
│   ├── demo_monitor_with_api.py
│   └── space_station_monitor.py
├── api/
│   ├── README.md
│   └── demo_backtest_api.py
├── backtest/
│   ├── README.md
│   ├── demo_news_backtest.py
│   ├── demo_llm_trading_strategy.py
│   └── demo_all_ai_strategies.py
└── strategies/
    ├── README.md
    └── (strategy-specific demos)
```

#### **`analysis/` Structure**
```
analysis/
├── performance/
│   ├── README.md
│   ├── analyze_portfolio_performance.py
│   ├── analyze_real_portfolio_performance.py
│   └── analyze_fixed_portfolio_performance.py
├── backtest/
│   ├── README.md
│   ├── run_comprehensive_historical_backtest.py
│   ├── run_historical_greeks_backtest.py
│   ├── run_greeks_comprehensive_backtest.py
│   ├── run_news_enhanced_backtest.py
│   ├── run_portfolio_backtest.py
│   └── run_backtest_with_real_data.py
└── README.md
```

#### **`tools/` Structure**
```
tools/
├── data/
│   ├── README.md
│   ├── scan_backtest_data.py
│   ├── populate_2year_data.py
│   ├── populate_2year_data_simple.py
│   ├── store_2year_data.py
│   ├── fetch_and_store_polygon_data.py
│   └── build_backtest_data.py
├── testing/
│   ├── README.md
│   ├── test_database_storage.py
│   ├── test_llm_analysis.py
│   ├── test_import.py
│   ├── test_db_connection.py
│   ├── test_historical_greeks_direct.py
│   ├── test_polygon_options_access.py
│   └── verify_ollama_model.py
├── debugging/
│   ├── README.md
│   ├── debug_config.py
│   ├── fix_llm_column.py
│   └── logging_config.py
└── README.md
```

#### **`scripts/` Structure**
```
scripts/
├── deploy/
│   ├── README.md
│   ├── deploy-all-services.sh
│   ├── deploy-health-dashboard.sh
│   ├── deploy-backtest-api.sh
│   └── deploy.sh
├── setup/
│   ├── README.md
│   ├── setup_polygon_secret.sh
│   ├── setup-local-registry.sh
│   ├── docker-registry-setup.sh
│   ├── quick-start.sh
│   └── quick-start-secure.sh
├── maintenance/
│   ├── README.md
│   ├── fix_k8s_containers.sh
│   └── create_services.py
├── cli/
│   ├── README.md
│   ├── backtest_cli.py
│   ├── trading_cli.py
│   ├── kube_backtest_cli.py
│   └── log_manager.py
└── README.md
```

#### **`docs/` Structure**
```
docs/
├── guides/
│   ├── architecture/
│   │   ├── README.md
│   │   ├── ARCHITECTURE_DIAGRAM.md
│   │   ├── SPACE_STATION_ARCHITECTURE_DIAGRAMS.md
│   │   └── architecture.md
│   ├── deployment/
│   │   ├── README.md
│   │   ├── DEPLOYMENT.md
│   │   ├── KUBERNETES_FIRST_GUIDE.md
│   │   ├── CONTAINER_FIRST_GUIDE.md
│   │   ├── LOCAL_REGISTRY_GUIDE.md
│   │   └── SECURE_ARCHITECTURE_GUIDE.md
│   ├── development/
│   │   ├── README.md
│   │   ├── DEVELOPMENT_RULES.md
│   │   ├── MAKEFILE_MODULAR_GUIDE.md
│   │   ├── MAKEFILE_REFERENCE.md
│   │   └── CURSOR_RULES_SUMMARY.md
│   ├── monitoring/
│   │   ├── README.md
│   │   ├── MONITOR_API_GUIDE.md
│   │   ├── MONITOR_API_CHECKLIST.md
│   │   ├── QUICK_REFERENCE.md
│   │   └── SPACE_STATION_MONITOR_GUIDE.md
│   ├── strategies/
│   │   ├── README.md
│   │   └── AI_ENHANCED_STRATEGIES_GUIDE.md
│   ├── news/
│   │   ├── README.md
│   │   ├── NEWS_AI_GUIDE.md
│   │   ├── NEWS_BOT_GUIDE.md
│   │   ├── HISTORICAL_NEWS_GUIDE.md
│   │   ├── KUBERNETES_NEWS_DEPLOYMENT.md
│   │   └── NEWS_TRADING_IMPACT_DIAGRAM.md
│   └── data/
│       ├── README.md
│       ├── MARKET_DATA_GUIDE.md
│       ├── YAHOO_FINANCE_GUIDE.md
│       ├── RABBITMQ_WORKERS_GUIDE.md
│       └── EVENT_REPLAY_GUIDE.md
├── api/
│   ├── README.md
│   └── (API documentation)
├── tutorials/
│   ├── README.md
│   └── (Step-by-step tutorials)
├── reference/
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── QUICK_WINS_SUMMARY.md
│   └── TODO.md
└── README.md
```

## 🚀 Implementation Strategy

### **Phase 1: Create New Structure**
1. Create new directories
2. Move files in batches
3. Update import paths
4. Test functionality

### **Phase 2: Update Documentation**
1. Update README files
2. Create directory-specific guides
3. Update Makefile paths
4. Update CI/CD scripts

### **Phase 3: Cleanup**
1. Remove old directories
2. Update .gitignore
3. Test everything works
4. Create migration guide

## 📋 Benefits for New Users

### **Clear Entry Points:**
- `README.md` - Project overview
- `QUICKSTART.md` - 5-minute setup
- `demos/` - See it in action
- `docs/guides/` - Learn more

### **Logical Organization:**
- **Demos** - See examples first
- **Analysis** - Understand performance
- **Tools** - Utilities and debugging
- **Documentation** - Learn the system

### **Reduced Cognitive Load:**
- Fewer files in root directory
- Related files grouped together
- Clear naming conventions
- Consistent structure

## 🎯 Success Metrics

- [ ] Root directory has < 10 files
- [ ] New users can find demos in 30 seconds
- [ ] Documentation is logically organized
- [ ] All imports and paths work correctly
- [ ] CI/CD pipeline still works
- [ ] Development workflow is unchanged

---

**This reorganization will make the Space Trading Station much more accessible to new users! 🚀** 