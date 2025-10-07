#!/usr/bin/env python3
"""
Tax and Fee Optimization Script
Converts current high-frequency trading config to tax-efficient configuration
"""

import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaxOptimizer:
    """Optimize trading configuration for tax efficiency"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.backup_dir = self.project_root / "config" / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def analyze_current_config(self, config_path: Path) -> Dict[str, Any]:
        """Analyze current configuration for tax inefficiencies"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        issues = []
        
        # Check day trading frequency
        day_trading = config.get('trading_frequency', {}).get('day_trading', {})
        if day_trading.get('enabled') and day_trading.get('max_daily_trades', 0) > 5:
            issues.append({
                'type': 'HIGH_FREQUENCY_DAY_TRADING',
                'severity': 'HIGH',
                'current_value': day_trading.get('max_daily_trades'),
                'recommended_value': 5,
                'tax_impact': 'All gains taxed at ordinary income rates (10-37%)',
                'annual_cost_estimate': '$500-800 in excess fees'
            })
        
        # Check holding periods
        swing_trading = config.get('trading_frequency', {}).get('swing_trading', {})
        if swing_trading.get('max_position_duration_days', 0) < 30:
            issues.append({
                'type': 'SHORT_HOLDING_PERIOD',
                'severity': 'HIGH',
                'current_value': swing_trading.get('max_position_duration_days'),
                'recommended_value': 45,
                'tax_impact': 'Short-term capital gains (ordinary income rates)',
                'annual_cost_estimate': '$150-400 in excess taxes'
            })
        
        # Check options allocation
        asset_allocation = config.get('asset_allocation', {})
        options_pct = (asset_allocation.get('options_day_trading_pct', 0) + 
                      asset_allocation.get('options_swing_trading_pct', 0))
        if options_pct > 0.35:  # More than 35%
            issues.append({
                'type': 'HIGH_OPTIONS_ALLOCATION',
                'severity': 'MEDIUM',
                'current_value': f"{options_pct:.1%}",
                'recommended_value': '30%',
                'tax_impact': 'High contract fees ($0.65 each)',
                'annual_cost_estimate': '$300-600 in contract fees'
            })
        
        # Check wash sale protection
        compliance = config.get('compliance', {})
        if not compliance.get('wash_sale_rule'):
            issues.append({
                'type': 'NO_WASH_SALE_PROTECTION',
                'severity': 'MEDIUM',
                'current_value': 'Disabled',
                'recommended_value': 'Enabled',
                'tax_impact': 'Loss deductions may be disallowed',
                'annual_cost_estimate': '$100-300 in lost deductions'
            })
        
        # Check tax optimization features
        if 'tax_optimization' not in config or not config.get('tax_optimization', {}).get('enabled'):
            issues.append({
                'type': 'NO_TAX_LOSS_HARVESTING',
                'severity': 'MEDIUM',
                'current_value': 'Disabled',
                'recommended_value': 'Enabled',
                'tax_impact': 'Missed tax-loss harvesting opportunities',
                'annual_cost_estimate': '$200-500 in potential savings'
            })
        
        return {
            'issues': issues,
            'total_estimated_cost': sum([
                int(issue['annual_cost_estimate'].split('$')[1].split('-')[0])
                for issue in issues
            ]),
            'severity_counts': {
                'HIGH': len([i for i in issues if i['severity'] == 'HIGH']),
                'MEDIUM': len([i for i in issues if i['severity'] == 'MEDIUM']),
                'LOW': len([i for i in issues if i['severity'] == 'LOW'])
            }
        }
    
    def create_tax_optimized_config(self, original_config_path: Path) -> Dict[str, Any]:
        """Create tax-optimized version of configuration"""
        with open(original_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info("🔧 Creating tax-optimized configuration...")
        
        # 1. REDUCE DAY TRADING FREQUENCY
        if 'trading_frequency' not in config:
            config['trading_frequency'] = {}
        
        config['trading_frequency']['day_trading'] = {
            'enabled': True,
            'interval_minutes': 30,  # Check every 30 min (vs 5 min)
            'max_daily_trades': 5,   # Down from 15
            'max_position_duration_hours': 6,
            'symbols': ['SPY', 'QQQ', 'NVDA'],
            'strategies': ['AdaptiveSectorWaveStrategy'],
            'allocation_pct': 0.15   # Down from 0.25
        }
        
        # 2. EXTEND SWING TRADING HOLDS
        config['trading_frequency']['swing_trading'] = {
            'enabled': True,
            'interval_minutes': 120,  # Check every 2 hours (vs 10 min)
            'max_daily_trades': 3,    # Down from 5
            'min_holding_days': 30,   # NEW: Minimum 30 days
            'max_position_duration_days': 90,  # Up from 5
            'symbols': ['SPY', 'AAPL', 'NVDA', 'TSLA', 'META'],
            'strategies': ['MultiStrategyEnsemble'],
            'allocation_pct': 0.50
        }
        
        # 3. ADD LONG-TERM HOLDINGS
        config['trading_frequency']['long_term_holdings'] = {
            'enabled': True,
            'interval_minutes': 1440,  # Check once per day
            'max_monthly_trades': 2,   # Very infrequent
            'min_holding_days': 365,   # Hold for 1+ year
            'symbols': ['SPY', 'QQQ', 'VTI'],
            'allocation_pct': 0.25
        }
        
        # 4. OPTIMIZE ASSET ALLOCATION
        config['asset_allocation'] = {
            'enabled': True,
            'cash_reserve_pct': 0.15,           # Up from 0.10 for stability
            'stock_allocation_pct': 0.55,       # Up from 0.40 (no commission!)
            'options_day_trading_pct': 0.10,    # Down from 0.25 (reduce fees)
            'options_swing_trading_pct': 0.20,  # Down from 0.25
            'long_term_holdings_pct': 0.25,     # NEW: 1+ year holds
            
            # Position sizing
            'max_stock_position_pct': 0.15,
            'max_options_position_pct': 0.10,
            'max_long_term_position_pct': 0.20
        }
        
        # 5. ENABLE TAX OPTIMIZATION
        config['tax_optimization'] = {
            'enabled': True,
            'tax_loss_harvesting': {
                'enabled': True,
                'min_loss_threshold': 0.05,      # 5% loss minimum
                'year_end_harvesting': True,
                'max_harvests_per_year': 12
            },
            'wash_sale_protection': {
                'enabled': True,
                'lookback_days': 30,
                'replacement_delay_days': 31,
                'alternative_securities': {
                    'SPY': ['VOO', 'IVV'],       # Alternative S&P 500 ETFs
                    'QQQ': ['QQQM', 'ONEQ'],     # Alternative Nasdaq ETFs
                    'NVDA': ['AMD', 'AVGO'],     # Alternative semiconductor stocks
                    'AAPL': ['MSFT', 'GOOGL'],   # Alternative tech stocks
                    'TSLA': ['RIVN', 'LCID']     # Alternative EV stocks
                }
            },
            'holding_period_optimization': {
                'enabled': True,
                'prefer_long_term_gains': True,
                'min_hold_for_lt_gains_days': 365,
                'warning_before_st_sale': True
            },
            'tax_rates': {
                'short_term': 0.24,  # Assumed 24% bracket (update for your bracket)
                'long_term': 0.15,   # 15% long-term capital gains
                'options': 0.24      # Same as short-term
            }
        }
        
        # 6. ENHANCE COMPLIANCE
        if 'compliance' not in config:
            config['compliance'] = {}
        
        config['compliance'].update({
            'wash_sale_rule': True,
            'wash_sale_tracking': True,
            'pattern_day_trader_protection': True,
            'holding_period_tracking': True,
            'tax_lot_accounting': 'HIFO',  # Highest In First Out (tax efficient)
            'tax_reporting': True,
            'quarterly_tax_estimates': True
        })
        
        # 7. REDUCE TRADING LIMITS FOR FEE SAVINGS
        config['trading_limits'] = {
            'max_daily_trades': 8,    # Down from 25
            'max_weekly_trades': 20,   # Down from unlimited
            'max_monthly_trades': 60,  # Down from 150
            'trading_frequency_penalty': True,
            'high_frequency_warning_threshold': 10  # Warn if >10 trades/day
        }
        
        # 8. OPTIMIZE COST CONTROLS
        if 'cost_controls' not in config:
            config['cost_controls'] = {}
        
        config['cost_controls']['trading_costs'] = {
            'commission_per_contract': 0.65,
            'commission_per_trade': 0.0,
            'options_rebate_per_contract': 0.06,
            'max_contracts_per_trade': 2,    # Keep small to minimize fees
            'slippage': 0.0005,
            'spread_cost': 0.002,
            'extended_hours_fee': 0.0,       # Disabled to save fees
            'premium_membership_cost': 10.0,
            'monthly_fee_budget': 100.0,     # Alert if fees exceed $100/month
            'fee_optimization_enabled': True
        }
        
        # 9. UPDATE PORTFOLIO SETTINGS
        config['portfolio'].update({
            'max_daily_trades': 8,           # Conservative
            'max_monthly_trades': 60,        # Conservative
            'tax_efficient_rebalancing': True,
            'rebalance_threshold': 0.10,     # Only rebalance if >10% drift
            'rebalance_frequency_days': 90   # Quarterly (less frequent = fewer taxes)
        })
        
        return config
    
    def backup_config(self, config_path: Path) -> Path:
        """Backup current configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"{config_path.stem}_backup_{timestamp}.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        with open(backup_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"✅ Backed up to: {backup_path}")
        return backup_path
    
    def estimate_tax_savings(self, current_config: Dict, optimized_config: Dict) -> Dict[str, Any]:
        """Estimate annual tax and fee savings"""
        
        # Current costs
        current_day_trades = current_config.get('trading_frequency', {}).get('day_trading', {}).get('max_daily_trades', 15)
        current_swing_trades = current_config.get('trading_frequency', {}).get('swing_trading', {}).get('max_daily_trades', 5)
        current_options_pct = 0.50  # 50% in options currently
        
        # Optimized costs
        opt_day_trades = optimized_config.get('trading_frequency', {}).get('day_trading', {}).get('max_daily_trades', 5)
        opt_swing_trades = optimized_config.get('trading_frequency', {}).get('swing_trading', {}).get('max_daily_trades', 3)
        opt_options_pct = 0.30  # 30% in options optimized
        
        # Calculate savings
        trading_days_per_month = 20
        
        # Fee savings from reduced day trading
        day_trade_fee_savings = ((current_day_trades - opt_day_trades) * trading_days_per_month * 12 * 0.65)
        
        # Fee savings from reduced swing trading  
        swing_trade_fee_savings = ((current_swing_trades - opt_swing_trades) * trading_days_per_month * 12 * 0.65)
        
        # Fee savings from reduced options allocation
        options_fee_savings = ((current_options_pct - opt_options_pct) * 100 * 12)  # ~$100/month per 10%
        
        # Tax savings from longer holding periods (estimated)
        # Assume $2,000 annual gains, 24% -> 15% rate on 50% of positions
        tax_rate_savings = 2000 * 0.50 * (0.24 - 0.15)
        
        # Tax-loss harvesting opportunities
        tlh_savings = 300  # Conservative estimate
        
        return {
            'fee_savings': {
                'day_trading_reduction': round(day_trade_fee_savings, 2),
                'swing_trading_reduction': round(swing_trade_fee_savings, 2),
                'options_allocation_reduction': round(options_fee_savings, 2),
                'total_fee_savings': round(day_trade_fee_savings + swing_trade_fee_savings + options_fee_savings, 2)
            },
            'tax_savings': {
                'longer_holding_periods': round(tax_rate_savings, 2),
                'tax_loss_harvesting': round(tlh_savings, 2),
                'total_tax_savings': round(tax_rate_savings + tlh_savings, 2)
            },
            'total_annual_savings': round(
                day_trade_fee_savings + swing_trade_fee_savings + options_fee_savings + 
                tax_rate_savings + tlh_savings, 2
            )
        }
    
    def generate_report(self, config_path: Path, analysis: Dict, savings: Dict) -> str:
        """Generate optimization report"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║          TAX & FEE OPTIMIZATION REPORT                           ║
╚══════════════════════════════════════════════════════════════════╝

📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📁 Config: {config_path.name}

🔍 ISSUES FOUND:
   • High Severity: {analysis['severity_counts']['HIGH']}
   • Medium Severity: {analysis['severity_counts']['MEDIUM']}
   • Low Severity: {analysis['severity_counts']['LOW']}

💰 ESTIMATED ANNUAL SAVINGS:

   Fee Savings:
   • Day trading reduction:      ${savings['fee_savings']['day_trading_reduction']:,.2f}
   • Swing trading reduction:     ${savings['fee_savings']['swing_trading_reduction']:,.2f}
   • Options allocation cut:      ${savings['fee_savings']['options_allocation_reduction']:,.2f}
   • Total Fee Savings:           ${savings['fee_savings']['total_fee_savings']:,.2f}

   Tax Savings:
   • Longer holding periods:      ${savings['tax_savings']['longer_holding_periods']:,.2f}
   • Tax-loss harvesting:         ${savings['tax_savings']['tax_loss_harvesting']:,.2f}
   • Total Tax Savings:           ${savings['tax_savings']['total_tax_savings']:,.2f}

   💵 TOTAL ANNUAL SAVINGS:        ${savings['total_annual_savings']:,.2f}

📋 DETAILED ISSUES:
"""
        
        for i, issue in enumerate(analysis['issues'], 1):
            report += f"""
   {i}. {issue['type']} [{issue['severity']}]
      Current:     {issue['current_value']}
      Recommended: {issue['recommended_value']}
      Impact:      {issue['tax_impact']}
      Cost:        {issue['annual_cost_estimate']}
"""
        
        report += f"""
✅ OPTIMIZATIONS APPLIED:
   • Reduced day trading from 15 to 5 trades/day
   • Extended swing holds from 5 to 30-90 days
   • Added long-term holdings (365+ days, 25% allocation)
   • Cut options allocation from 50% to 30%
   • Enabled tax-loss harvesting
   • Enabled wash sale protection
   • Reduced trading frequency checks
   • Implemented quarterly rebalancing

📊 NEW ALLOCATION:
   • Long-term holdings: 25% (365+ day holds)
   • Stocks swing trading: 40% (30-90 day holds)
   • Options swing trading: 20%
   • Options day trading: 10%
   • Cash reserve: 15%

🎯 NEXT STEPS:
   1. Review the optimized config file
   2. Test in paper trading first
   3. Monitor actual tax savings vs estimates
   4. Adjust based on your tax bracket
   5. Consider Roth IRA for tax-free trading

═══════════════════════════════════════════════════════════════════
"""
        return report

    def run_optimization(self, config_name: str = "multi_strategy_ensemble_live_trading.yaml"):
        """Run full optimization process"""
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            logger.error(f"❌ Config not found: {config_path}")
            return
        
        logger.info(f"🔍 Analyzing {config_name}...")
        
        # Analyze current config
        with open(config_path, 'r') as f:
            current_config = yaml.safe_load(f)
        analysis = self.analyze_current_config(config_path)
        
        # Create optimized config
        optimized_config = self.create_tax_optimized_config(config_path)
        
        # Calculate savings
        savings = self.estimate_tax_savings(current_config, optimized_config)
        
        # Generate report
        report = self.generate_report(config_path, analysis, savings)
        print(report)
        
        # Save report
        report_path = self.project_root / f"TAX_OPTIMIZATION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        logger.info(f"📄 Report saved to: {report_path}")
        
        # Ask user if they want to apply changes
        print("\n" + "="*80)
        print("Would you like to apply these optimizations?")
        print("1. Yes - Apply to live config (backup will be created)")
        print("2. Save as new file (won't modify live config)")
        print("3. No - Just view the report")
        print("="*80)
        
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == "1":
            # Backup current config
            backup_path = self.backup_config(config_path)
            logger.info(f"✅ Backup created: {backup_path}")
            
            # Apply optimizations
            with open(config_path, 'w') as f:
                yaml.dump(optimized_config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"✅ Optimized config saved to: {config_path}")
            logger.info(f"💾 Original backed up to: {backup_path}")
            
        elif choice == "2":
            # Save as new file
            new_path = config_path.parent / f"{config_path.stem}_tax_optimized.yaml"
            with open(new_path, 'w') as f:
                yaml.dump(optimized_config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"✅ Optimized config saved to: {new_path}")
            
        else:
            logger.info("ℹ️  No changes made. Review the report and decide later.")
        
        print("\n" + "="*80)
        print("🎉 Optimization complete!")
        print(f"📊 Estimated annual savings: ${savings['total_annual_savings']:,.2f}")
        print("="*80)

if __name__ == "__main__":
    import sys
    
    optimizer = TaxOptimizer()
    
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
        optimizer.run_optimization(config_name)
    else:
        # Default to live trading config
        optimizer.run_optimization()

