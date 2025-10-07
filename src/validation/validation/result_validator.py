"""
Result validation service for validating backtest results

This service validates backtest results against configuration tolerances
and business rules to ensure quality and consistency.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..models.backtest_result import BacktestResult, ValidationError, PerformanceMetrics
from ..models.test_configuration import TestConfiguration

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of validation process"""
    
    def __init__(self, is_valid: bool, score: float = 0.0):
        self.is_valid = is_valid
        self.score = score
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def add_error(self, field: str, message: str) -> None:
        """Add a validation error"""
        self.errors.append(ValidationError(field=field, message=message, severity="ERROR"))
    
    def add_warning(self, field: str, message: str) -> None:
        """Add a validation warning"""
        self.warnings.append(ValidationError(field=field, message=message, severity="WARNING"))


class ConsistencyResult:
    """Result of consistency validation"""
    
    def __init__(self, is_consistent: bool, consistency_score: float = 0.0):
        self.is_consistent = is_consistent
        self.consistency_score = consistency_score
        self.inconsistencies: List[Dict[str, Any]] = []


class ResultValidator:
    """
    Service for validating backtest results against configuration tolerances and business rules.
    """
    
    def __init__(self):
        self.performance_bounds = {
            'total_return_pct': {'min': -100.0, 'max': 10000.0},  # -100% to 10000%
            'sharpe_ratio': {'min': -10.0, 'max': 100.0},         # -10 to 100
            'max_drawdown_pct': {'min': 0.0, 'max': 100.0},       # 0% to 100%
            'win_rate': {'min': 0.0, 'max': 1.0},                 # 0% to 100%
            'total_trades': {'min': 0, 'max': 1000000},           # 0 to 1M trades
        }
    
    def validate_result(self, result: BacktestResult, 
                       configuration: TestConfiguration) -> ValidationResult:
        """
        Validate a single backtest result.
        
        Args:
            result: BacktestResult to validate
            configuration: TestConfiguration with validation rules
            
        Returns:
            ValidationResult with validation details
        """
        validation = ValidationResult(is_valid=True, score=100.0)
        
        # Check execution status
        if result.status != "SUCCESS":
            validation.add_error("execution", f"Script execution failed with status: {result.status}")
            validation.is_valid = False
            validation.score = 0.0
            return validation
        
        # Validate performance metrics completeness
        if not result.performance_metrics:
            validation.add_error("performance_metrics", "Missing performance metrics")
            validation.is_valid = False
            validation.score = 0.0
            return validation
        
        # Validate required metrics
        self._validate_required_metrics(result, configuration, validation)
        
        # Validate metric values
        self._validate_metric_values(result, configuration, validation)
        
        # Validate trade data
        self._validate_trade_data(result, validation)
        
        # Validate resource usage
        self._validate_resource_usage(result, validation)
        
        # Calculate final score
        validation.score = self._calculate_validation_score(validation)
        
        # Determine overall validity
        validation.is_valid = len(validation.errors) == 0 and validation.score >= 70.0
        
        return validation
    
    def validate_consistency(self, results: List[BacktestResult],
                           configuration: TestConfiguration) -> ConsistencyResult:
        """
        Validate consistency across multiple results from the same script.
        
        Args:
            results: List of BacktestResult objects
            configuration: TestConfiguration with tolerances
            
        Returns:
            ConsistencyResult with consistency analysis
        """
        if len(results) < 2:
            return ConsistencyResult(is_consistent=True, consistency_score=100.0)
        
        consistency = ConsistencyResult(is_consistent=True, consistency_score=100.0)
        successful_results = [r for r in results if r.performance_metrics]
        
        if len(successful_results) < 2:
            return consistency
        
        # Group results by script
        script_groups = {}
        for result in successful_results:
            if result.script_id not in script_groups:
                script_groups[result.script_id] = []
            script_groups[result.script_id].append(result)
        
        # Check consistency within each script group
        for script_id, script_results in script_groups.items():
            if len(script_results) >= 2:
                script_consistency = self._validate_script_consistency(
                    script_results, configuration
                )
                
                if not script_consistency['is_consistent']:
                    consistency.is_consistent = False
                    consistency.inconsistencies.extend(script_consistency['inconsistencies'])
                    consistency.consistency_score = min(
                        consistency.consistency_score,
                        script_consistency['score']
                    )
        
        return consistency
    
    def _validate_required_metrics(self, result: BacktestResult,
                                 configuration: TestConfiguration,
                                 validation: ValidationResult) -> None:
        """Validate that all required metrics are present."""
        if not result.performance_metrics:
            return
        
        missing_metrics = []
        for metric in configuration.validation_rules.required_metrics:
            if not hasattr(result.performance_metrics, metric):
                if metric not in configuration.validation_rules.allow_missing_metrics:
                    missing_metrics.append(metric)
        
        if missing_metrics:
            validation.add_error(
                "performance_metrics",
                f"Missing required metrics: {', '.join(missing_metrics)}"
            )
            validation.is_valid = False
    
    def _validate_metric_values(self, result: BacktestResult,
                              configuration: TestConfiguration,
                              validation: ValidationResult) -> None:
        """Validate metric values against bounds and tolerances."""
        if not result.performance_metrics:
            return
        
        metrics = result.performance_metrics
        
        # Validate return percentage
        if hasattr(metrics, 'total_return_pct'):
            if not (-100.0 <= metrics.total_return_pct <= 10000.0):
                validation.add_error(
                    "total_return_pct",
                    f"Return percentage {metrics.total_return_pct}% is outside normal bounds (-100% to 10000%)"
                )
        
        # Validate Sharpe ratio
        if hasattr(metrics, 'sharpe_ratio'):
            if not (-10.0 <= metrics.sharpe_ratio <= 100.0):
                validation.add_error(
                    "sharpe_ratio",
                    f"Sharpe ratio {metrics.sharpe_ratio} is outside normal bounds (-10 to 100)"
                )
        
        # Validate drawdown
        if hasattr(metrics, 'max_drawdown_pct'):
            if not (0.0 <= metrics.max_drawdown_pct <= 100.0):
                validation.add_error(
                    "max_drawdown_pct",
                    f"Max drawdown {metrics.max_drawdown_pct}% is outside normal bounds (0% to 100%)"
                )
        
        # Validate win rate
        if hasattr(metrics, 'win_rate'):
            if not (0.0 <= metrics.win_rate <= 1.0):
                validation.add_error(
                    "win_rate",
                    f"Win rate {metrics.win_rate} is outside normal bounds (0.0 to 1.0)"
                )
        
        # Validate trade count
        if hasattr(metrics, 'total_trades'):
            if metrics.total_trades < 0:
                validation.add_error(
                    "total_trades",
                    f"Total trades {metrics.total_trades} cannot be negative"
                )
            
            # Check for suspicious trade counts
            if metrics.total_trades == 0 and metrics.total_return_pct != 0:
                validation.add_error(
                    "total_trades",
                    "Zero trades but non-zero return is suspicious"
                )
        
        # Validate capital values
        if hasattr(metrics, 'initial_capital') and hasattr(metrics, 'final_capital'):
            if metrics.initial_capital <= 0:
                validation.add_error(
                    "initial_capital",
                    f"Initial capital {metrics.initial_capital} must be positive"
                )
            
            if metrics.final_capital <= 0:
                validation.add_error(
                    "final_capital",
                    f"Final capital {metrics.final_capital} must be positive"
                )
            
            # Check for unrealistic capital growth
            if metrics.final_capital > metrics.initial_capital * 1000:
                validation.add_warning(
                    "final_capital",
                    f"Final capital is {metrics.final_capital/metrics.initial_capital:.1f}x initial capital (very high)"
                )
    
    def _validate_trade_data(self, result: BacktestResult,
                           validation: ValidationResult) -> None:
        """Validate trade data structure and content."""
        if not result.trade_data:
            return
        
        for i, trade in enumerate(result.trade_data):
            # Validate required fields
            required_fields = ['symbol', 'action', 'price', 'quantity']
            for field in required_fields:
                if field not in trade:
                    validation.add_error(
                        "trade_data",
                        f"Trade {i} missing required field: {field}"
                    )
            
            # Validate field values
            if 'symbol' in trade and not trade['symbol']:
                validation.add_error("trade_data", f"Trade {i} has empty symbol")
            
            if 'price' in trade:
                try:
                    price = float(trade['price'])
                    if price <= 0:
                        validation.add_error(
                            "trade_data",
                            f"Trade {i} has invalid price: {price}"
                        )
                except (ValueError, TypeError):
                    validation.add_error(
                        "trade_data",
                        f"Trade {i} has non-numeric price: {trade['price']}"
                    )
            
            if 'quantity' in trade:
                try:
                    quantity = int(trade['quantity'])
                    if quantity <= 0:
                        validation.add_error(
                            "trade_data",
                            f"Trade {i} has invalid quantity: {quantity}"
                        )
                except (ValueError, TypeError):
                    validation.add_error(
                        "trade_data",
                        f"Trade {i} has non-integer quantity: {trade['quantity']}"
                    )
            
            if 'action' in trade:
                if trade['action'] not in ['BUY', 'SELL', 'SHORT', 'COVER']:
                    validation.add_error(
                        "trade_data",
                        f"Trade {i} has invalid action: {trade['action']}"
                    )
    
    def _validate_resource_usage(self, result: BacktestResult,
                               validation: ValidationResult) -> None:
        """Validate resource usage is reasonable."""
        if not result.resource_usage:
            return
        
        usage = result.resource_usage
        
        # Check memory usage
        if usage.peak_memory_mb > 2048:  # 2GB
            validation.add_warning(
                "resource_usage",
                f"High memory usage: {usage.peak_memory_mb:.1f}MB"
            )
        
        # Check CPU usage
        if usage.average_cpu_percent > 80:
            validation.add_warning(
                "resource_usage",
                f"High CPU usage: {usage.average_cpu_percent:.1f}%"
            )
        
        # Check execution time
        if result.duration_seconds > 3600:  # 1 hour
            validation.add_warning(
                "execution_time",
                f"Long execution time: {result.duration_seconds:.1f} seconds"
            )
    
    def _validate_script_consistency(self, results: List[BacktestResult],
                                   configuration: TestConfiguration) -> Dict[str, Any]:
        """Validate consistency within a single script's results."""
        if len(results) < 2:
            return {'is_consistent': True, 'score': 100.0, 'inconsistencies': []}
        
        inconsistencies = []
        total_score = 100.0
        
        # Compare metrics across results
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            if not result.performance_metrics or not first_result.performance_metrics:
                continue
            
            # Compare return percentages
            return_diff = abs(
                result.performance_metrics.total_return_pct - 
                first_result.performance_metrics.total_return_pct
            )
            if return_diff > configuration.tolerances.returns_tolerance_pct:
                inconsistencies.append({
                    'script_id': result.script_id,
                    'metric': 'total_return_pct',
                    'difference': return_diff,
                    'tolerance': configuration.tolerances.returns_tolerance_pct,
                    'result_index': i
                })
                total_score -= 20.0
            
            # Compare Sharpe ratios
            sharpe_diff = abs(
                result.performance_metrics.sharpe_ratio - 
                first_result.performance_metrics.sharpe_ratio
            )
            if sharpe_diff > configuration.tolerances.ratios_tolerance:
                inconsistencies.append({
                    'script_id': result.script_id,
                    'metric': 'sharpe_ratio',
                    'difference': sharpe_diff,
                    'tolerance': configuration.tolerances.ratios_tolerance,
                    'result_index': i
                })
                total_score -= 15.0
            
            # Compare trade counts (exact match required)
            if configuration.validation_rules.require_exact_trade_counts:
                if (result.performance_metrics.total_trades != 
                    first_result.performance_metrics.total_trades):
                    inconsistencies.append({
                        'script_id': result.script_id,
                        'metric': 'total_trades',
                        'difference': abs(
                            result.performance_metrics.total_trades - 
                            first_result.performance_metrics.total_trades
                        ),
                        'tolerance': 0,
                        'result_index': i
                    })
                    total_score -= 30.0
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'score': max(0.0, total_score),
            'inconsistencies': inconsistencies
        }
    
    def _calculate_validation_score(self, validation: ValidationResult) -> float:
        """Calculate validation score based on errors and warnings."""
        score = 100.0
        
        # Deduct points for errors
        for error in validation.errors:
            if error.severity == "ERROR":
                score -= 25.0
            elif error.severity == "WARNING":
                score -= 10.0
        
        # Deduct points for warnings
        for warning in validation.warnings:
            score -= 5.0
        
        return max(0.0, score)











