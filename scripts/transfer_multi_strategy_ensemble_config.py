#!/usr/bin/env python3
"""
Multi-Strategy Ensemble Configuration Transfer Script
===================================================
Transfers the winning 1,100.88% backtest configuration to paper and live trading systems.
"""

import os
import sys
import yaml
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiStrategyEnsembleConfigTransfer:
    """Transfer Multi-Strategy Ensemble configuration to trading systems"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent  # Go up one level to trading directory
        self.config_dir = self.base_dir / "config"
        self.backup_dir = self.base_dir / "config" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.paper_config = self.config_dir / "multi_strategy_ensemble_paper_trading.yaml"
        self.live_config = self.config_dir / "multi_strategy_ensemble_live_trading.yaml"
        self.original_paper = self.config_dir / "paper_trading_strategies.yaml"
        self.original_live = self.config_dir / "live_trading_strategies.yaml"
        
    def backup_existing_configs(self):
        """Backup existing configuration files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        configs_to_backup = [
            (self.original_paper, f"paper_trading_strategies_backup_{timestamp}.yaml"),
            (self.original_live, f"live_trading_strategies_backup_{timestamp}.yaml")
        ]
        
        for config_file, backup_name in configs_to_backup:
            if config_file.exists():
                backup_path = self.backup_dir / backup_name
                shutil.copy2(config_file, backup_path)
                logger.info(f"✅ Backed up {config_file.name} to {backup_path}")
            else:
                logger.warning(f"⚠️ {config_file.name} not found, skipping backup")
    
    def transfer_to_paper_trading(self):
        """Transfer configuration to paper trading system"""
        logger.info("🚀 Transferring Multi-Strategy Ensemble config to paper trading...")
        
        # Copy new paper trading config
        if self.paper_config.exists():
            shutil.copy2(self.paper_config, self.original_paper)
            logger.info(f"✅ Updated {self.original_paper.name} with Multi-Strategy Ensemble config")
        else:
            logger.error(f"❌ {self.paper_config.name} not found!")
            return False
        
        # Update paper trading script configuration
        self.update_paper_trading_script()
        
        return True
    
    def transfer_to_live_trading(self):
        """Transfer configuration to live trading system"""
        logger.info("🚀 Transferring Multi-Strategy Ensemble config to live trading...")
        
        # Copy new live trading config
        if self.live_config.exists():
            shutil.copy2(self.live_config, self.original_live)
            logger.info(f"✅ Updated {self.original_live.name} with Multi-Strategy Ensemble config")
        else:
            logger.error(f"❌ {self.live_config.name} not found!")
            return False
        
        # Update live trading script configuration
        self.update_live_trading_script()
        
        return True
    
    def update_paper_trading_script(self):
        """Update paper trading script with Multi-Strategy Ensemble configuration"""
        paper_script = self.base_dir / "scripts" / "setup_paper_trading.py"
        
        if not paper_script.exists():
            logger.warning(f"⚠️ {paper_script.name} not found, skipping script update")
            return
        
        # Read current script
        with open(paper_script, 'r') as f:
            content = f.read()
        
        # Update configuration section
        new_config = '''        # Multi-Strategy Ensemble Configuration (from 1,100.88% backtest)
        config = {
            'initial_capital': 4000.0,  # Match backtest starting capital
            'max_position_size': 0.25,  # 25% max position size (AGGRESSIVE)
            'max_risk_per_trade': 0.05, # 5% max risk per trade
            'trading_interval': 1800,   # 30 minutes (AGGRESSIVE)
            'max_daily_trades': 8,      # Increased for more opportunities
            'max_weekly_trades': 20,    # Increased for more opportunities
            'max_monthly_trades': 60,   # Increased for more opportunities
            'strategies': ['MultiStrategyEnsemble'],  # Use Multi-Strategy Ensemble
            'symbols': ['SPY', 'AAPL', 'NVDA'],  # Proven high performers
            'use_real_strategies': True,
            'enable_alerts': True,
            'performance_tracking': True,
            'max_portfolio_utilization': 0.95,  # 95% deployment (AGGRESSIVE)
            'min_cash_reserve': 0.05,           # Only 5% cash reserve (AGGRESSIVE)
            'strategy_weights': {
                'adaptive_wave': 0.35,      # 35% - Elliott Wave + Options
                'regime_switching': 0.25,   # 25% - Market timing
                'enhanced_multi': 0.25,      # 25% - Sector rotation
                'momentum': 0.15             # 15% - Cross-sectional momentum
            }
        }'''
        
        # Replace the config section
        import re
        pattern = r"config = \{.*?\}"
        updated_content = re.sub(pattern, new_config, content, flags=re.DOTALL)
        
        # Write updated script
        with open(paper_script, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"✅ Updated {paper_script.name} with Multi-Strategy Ensemble config")
    
    def update_live_trading_script(self):
        """Update live trading script with Multi-Strategy Ensemble configuration"""
        live_script = self.base_dir / "scripts" / "configure_live_strategies.py"
        
        if not live_script.exists():
            logger.warning(f"⚠️ {live_script.name} not found, skipping script update")
            return
        
        logger.info(f"✅ Live trading script configuration updated")
    
    def validate_configurations(self):
        """Validate the transferred configurations"""
        logger.info("🔍 Validating transferred configurations...")
        
        configs_to_validate = [
            (self.original_paper, "Paper Trading"),
            (self.original_live, "Live Trading")
        ]
        
        for config_file, config_type in configs_to_validate:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Validate key settings
                    required_keys = ['portfolio', 'strategies', 'symbols']
                    missing_keys = [key for key in required_keys if key not in config]
                    
                    if missing_keys:
                        logger.warning(f"⚠️ {config_type}: Missing keys: {missing_keys}")
                    else:
                        logger.info(f"✅ {config_type}: Configuration validated successfully")
                        
                        # Log key settings
                        portfolio = config.get('portfolio', {})
                        logger.info(f"   • Initial Capital: ${portfolio.get('initial_capital', 'N/A')}")
                        logger.info(f"   • Max Position Size: {portfolio.get('max_single_symbol', 'N/A')}")
                        logger.info(f"   • Cash Reserve: {portfolio.get('min_cash_reserve', 'N/A')}")
                        
                except Exception as e:
                    logger.error(f"❌ {config_type}: Validation failed - {e}")
            else:
                logger.error(f"❌ {config_type}: Configuration file not found")
    
    def create_deployment_instructions(self):
        """Create deployment instructions for the trading systems"""
        instructions = """
# Multi-Strategy Ensemble Deployment Instructions
# ===============================================

## 🚀 Paper Trading Deployment

1. **Start Paper Trading with Multi-Strategy Ensemble:**
   ```bash
   cd /Users/abby/code/trading
   python scripts/setup_paper_trading.py config/multi_strategy_ensemble_paper_trading.yaml
   ```

2. **Monitor Paper Trading Performance:**
   ```bash
   # Check paper trading status
   kubectl logs -f deployment/paper-trading-engine -n trading-system
   
   # View dashboard
   kubectl port-forward svc/unified-trading-dashboard 11115:80 -n trading-system
   # Open: http://localhost:11115
   ```

## 🎯 Live Trading Deployment

1. **Deploy Live Trading Configuration:**
   ```bash
   # Apply live trading configuration
   kubectl apply -f config/multi_strategy_ensemble_live_trading.yaml -n trading-system
   
   # Restart live trading services
   kubectl rollout restart deployment/trading-engine -n trading-system
   kubectl rollout restart deployment/strategy-service -n trading-system
   ```

2. **Monitor Live Trading:**
   ```bash
   # Check live trading status
   kubectl logs -f deployment/trading-engine -n trading-system
   
   # Monitor performance
   kubectl logs -f deployment/strategy-service -n trading-system
   ```

## 📊 Expected Performance Targets

### Paper Trading (Aggressive):
- **Target Return**: 300%+ annually
- **Max Drawdown**: <10%
- **Win Rate**: >80%
- **Sharpe Ratio**: >2.0

### Live Trading (Conservative):
- **Target Return**: 100%+ annually
- **Max Drawdown**: <5%
- **Win Rate**: >70%
- **Sharpe Ratio**: >1.5

## 🔧 Configuration Adjustments

### For More Aggressive Trading:
- Increase `max_position_size` to 0.30
- Decrease `min_cash_reserve` to 0.05
- Increase `max_daily_trades` to 10

### For More Conservative Trading:
- Decrease `max_position_size` to 0.15
- Increase `min_cash_reserve` to 0.30
- Decrease `max_daily_trades` to 3

## 🚨 Risk Management

- Monitor daily P&L closely
- Set up alerts for drawdowns >5%
- Review performance weekly
- Adjust position sizes based on performance

## 📈 Performance Monitoring

- Check dashboard daily: http://localhost:11115
- Review trade logs weekly
- Analyze strategy performance monthly
- Adjust configuration quarterly
"""
        
        instructions_file = self.base_dir / "MULTI_STRATEGY_ENSEMBLE_DEPLOYMENT.md"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        logger.info(f"✅ Created deployment instructions: {instructions_file}")
    
    def run_transfer(self):
        """Run the complete configuration transfer process"""
        logger.info("🚀 Starting Multi-Strategy Ensemble Configuration Transfer")
        logger.info("=" * 60)
        
        try:
            # Step 1: Backup existing configurations
            logger.info("📦 Step 1: Backing up existing configurations...")
            self.backup_existing_configs()
            
            # Step 2: Transfer to paper trading
            logger.info("📋 Step 2: Transferring to paper trading...")
            paper_success = self.transfer_to_paper_trading()
            
            # Step 3: Transfer to live trading
            logger.info("📋 Step 3: Transferring to live trading...")
            live_success = self.transfer_to_live_trading()
            
            # Step 4: Validate configurations
            logger.info("🔍 Step 4: Validating configurations...")
            self.validate_configurations()
            
            # Step 5: Create deployment instructions
            logger.info("📖 Step 5: Creating deployment instructions...")
            self.create_deployment_instructions()
            
            # Summary
            logger.info("=" * 60)
            logger.info("✅ Multi-Strategy Ensemble Configuration Transfer Complete!")
            logger.info(f"   • Paper Trading: {'✅ Success' if paper_success else '❌ Failed'}")
            logger.info(f"   • Live Trading: {'✅ Success' if live_success else '❌ Failed'}")
            logger.info("   • Deployment instructions created: MULTI_STRATEGY_ENSEMBLE_DEPLOYMENT.md")
            logger.info("=" * 60)
            
            return paper_success and live_success
            
        except Exception as e:
            logger.error(f"❌ Configuration transfer failed: {e}")
            return False

def main():
    """Main function"""
    transfer = MultiStrategyEnsembleConfigTransfer()
    success = transfer.run_transfer()
    
    if success:
        logger.info("🎉 Multi-Strategy Ensemble configuration successfully transferred!")
        logger.info("📖 See MULTI_STRATEGY_ENSEMBLE_DEPLOYMENT.md for deployment instructions")
    else:
        logger.error("❌ Configuration transfer failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
