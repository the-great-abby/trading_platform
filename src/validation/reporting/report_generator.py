"""
Report generation service for creating comprehensive validation reports

This service generates detailed reports from validation results including
performance analysis, consistency checks, and recommendations.
"""

import json
import csv
from io import StringIO
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..models.validation_report import ValidationReport, ExecutionSummary, ConsistencyResults, PerformanceAnalysis, Recommendation
from ..models.backtest_result import BacktestResult
from ..models.backtest_script import BacktestScript
from ..validation.result_validator import ResultValidator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Service for generating comprehensive validation reports.
    """
    
    def __init__(self):
        self.result_validator = ResultValidator()
    
    def generate_report(self, report_name: str,
                       results: List[BacktestResult],
                       scripts: List[BacktestScript],
                       include_consistency_analysis: bool = True,
                       include_performance_analysis: bool = True,
                       include_recommendations: bool = True) -> ValidationReport:
        """
        Generate a comprehensive validation report.
        
        Args:
            report_name: Name of the report
            results: List of BacktestResult objects
            scripts: List of BacktestScript objects
            include_consistency_analysis: Whether to include consistency analysis
            include_performance_analysis: Whether to include performance analysis
            include_recommendations: Whether to include recommendations
            
        Returns:
            ValidationReport object
            
        Raises:
            ValueError: If report name is empty or results are invalid
        """
        if not report_name.strip():
            raise ValueError("Report name cannot be empty")
        
        if results is None:
            raise ValueError("Results cannot be None")
        
        logger.info(f"Generating validation report: {report_name}")
        
        # Calculate basic statistics
        total_scripts = len(results)
        passed_scripts = sum(1 for r in results if r.status == "SUCCESS")
        failed_scripts = sum(1 for r in results if r.status == "FAILED")
        error_scripts = sum(1 for r in results if r.status in ["ERROR", "TIMEOUT"])
        
        # Generate execution summary
        execution_summary = self._generate_execution_summary(results)
        
        # Generate consistency analysis
        consistency_results = None
        if include_consistency_analysis:
            consistency_results = self._generate_consistency_analysis(results)
        
        # Generate performance analysis
        performance_analysis = None
        if include_performance_analysis:
            performance_analysis = self._generate_performance_analysis(results)
        
        # Generate recommendations
        recommendations = []
        if include_recommendations:
            recommendations = self._generate_recommendations(results, scripts)
        
        # Generate detailed results
        detailed_results = self._generate_detailed_results(results, scripts)
        
        # Create validation report
        report = ValidationReport(
            report_name=report_name,
            total_scripts=total_scripts,
            passed_scripts=passed_scripts,
            failed_scripts=failed_scripts,
            error_scripts=error_scripts,
            execution_summary=execution_summary,
            consistency_results=consistency_results,
            performance_analysis=performance_analysis,
            recommendations=recommendations,
            detailed_results=detailed_results
        )
        
        logger.info(f"Generated validation report with {total_scripts} scripts")
        return report
    
    def _generate_execution_summary(self, results: List[BacktestResult]) -> ExecutionSummary:
        """Generate execution summary from results."""
        if not results:
            return ExecutionSummary(
                total_execution_time_seconds=0.0,
                average_execution_time_seconds=0.0,
                parallel_execution_enabled=False,
                success_rate=0.0,
                failure_rate=0.0
            )
        
        total_time = sum(r.duration_seconds for r in results)
        average_time = total_time / len(results)
        
        successful_count = sum(1 for r in results if r.status == "SUCCESS")
        success_rate = successful_count / len(results)
        failure_rate = 1.0 - success_rate
        
        return ExecutionSummary(
            total_execution_time_seconds=total_time,
            average_execution_time_seconds=average_time,
            parallel_execution_enabled=True,
            success_rate=success_rate,
            failure_rate=failure_rate
        )
    
    def _generate_consistency_analysis(self, results: List[BacktestResult]) -> ConsistencyResults:
        """Generate consistency analysis from results."""
        # Group results by script ID
        script_groups = {}
        for result in results:
            if result.script_id not in script_groups:
                script_groups[result.script_id] = []
            script_groups[result.script_id].append(result)
        
        consistent_scripts = []
        inconsistent_scripts = []
        inconsistency_details = []
        total_consistency_score = 0.0
        analyzed_scripts = 0
        
        for script_id, script_results in script_groups.items():
            if len(script_results) >= 2:
                # Analyze consistency within this script
                consistency_result = self.result_validator.validate_consistency(script_results, None)
                
                if consistency_result.is_consistent:
                    consistent_scripts.append(script_id)
                else:
                    inconsistent_scripts.append(script_id)
                    inconsistency_details.extend(consistency_result.inconsistencies)
                
                total_consistency_score += consistency_result.consistency_score
                analyzed_scripts += 1
        
        overall_consistency_score = total_consistency_score / analyzed_scripts if analyzed_scripts > 0 else 100.0
        
        return ConsistencyResults(
            consistent_scripts=consistent_scripts,
            inconsistent_scripts=inconsistent_scripts,
            consistency_score=overall_consistency_score,
            inconsistency_details=inconsistency_details
        )
    
    def _generate_performance_analysis(self, results: List[BacktestResult]) -> PerformanceAnalysis:
        """Generate performance analysis from results."""
        successful_results = [r for r in results if r.performance_metrics and r.status == "SUCCESS"]
        
        if not successful_results:
            return PerformanceAnalysis(
                average_return=0.0,
                average_sharpe=0.0,
                average_drawdown=0.0,
                average_win_rate=0.0,
                performance_trends={},
                top_performers=[],
                underperformers=[]
            )
        
        # Calculate averages
        returns = [r.performance_metrics.total_return_pct for r in successful_results]
        sharpes = [r.performance_metrics.sharpe_ratio for r in successful_results]
        drawdowns = [r.performance_metrics.max_drawdown_pct for r in successful_results]
        win_rates = [r.performance_metrics.win_rate for r in successful_results]
        
        # Calculate trends
        performance_trends = {
            "return_std": self._calculate_std(returns),
            "sharpe_std": self._calculate_std(sharpes),
            "drawdown_std": self._calculate_std(drawdowns),
            "win_rate_std": self._calculate_std(win_rates),
            "return_range": max(returns) - min(returns) if returns else 0.0,
            "sharpe_range": max(sharpes) - min(sharpes) if sharpes else 0.0
        }
        
        # Identify top and bottom performers
        sorted_by_return = sorted(successful_results, 
                                key=lambda r: r.performance_metrics.total_return_pct, 
                                reverse=True)
        
        top_performers = [r.script_id for r in sorted_by_return[:3]]
        underperformers = [r.script_id for r in sorted_by_return[-3:]]
        
        return PerformanceAnalysis(
            average_return=sum(returns) / len(returns),
            average_sharpe=sum(sharpes) / len(sharpes),
            average_drawdown=sum(drawdowns) / len(drawdowns),
            average_win_rate=sum(win_rates) / len(win_rates),
            performance_trends=performance_trends,
            top_performers=top_performers,
            underperformers=underperformers
        )
    
    def _generate_recommendations(self, results: List[BacktestResult], 
                                scripts: List[BacktestScript]) -> List[Recommendation]:
        """Generate recommendations based on results and scripts."""
        recommendations = []
        
        # Create script lookup
        script_lookup = {s.id: s for s in scripts}
        
        for result in results:
            script = script_lookup.get(result.script_id)
            if not script:
                continue
            
            # High priority recommendations for failed scripts
            if result.status in ["FAILED", "ERROR", "TIMEOUT"]:
                recommendations.append(Recommendation(
                    script_id=result.script_id,
                    recommendation="Fix script execution issues",
                    priority="HIGH",
                    category="Execution",
                    description=f"Script failed with status: {result.status}. Check error logs and fix issues."
                ))
            
            # Performance recommendations
            if result.performance_metrics:
                metrics = result.performance_metrics
                
                # Low return recommendation
                if metrics.total_return_pct < 5.0:
                    recommendations.append(Recommendation(
                        script_id=result.script_id,
                        recommendation="Improve strategy performance",
                        priority="MEDIUM",
                        category="Performance",
                        description=f"Low return of {metrics.total_return_pct:.2f}% suggests strategy optimization needed."
                    ))
                
                # High drawdown recommendation
                if metrics.max_drawdown_pct > 20.0:
                    recommendations.append(Recommendation(
                        script_id=result.script_id,
                        recommendation="Reduce maximum drawdown",
                        priority="HIGH",
                        category="Risk Management",
                        description=f"High drawdown of {metrics.max_drawdown_pct:.2f}% indicates risk management issues."
                    ))
                
                # Low Sharpe ratio recommendation
                if metrics.sharpe_ratio < 1.0:
                    recommendations.append(Recommendation(
                        script_id=result.script_id,
                        recommendation="Improve risk-adjusted returns",
                        priority="MEDIUM",
                        category="Performance",
                        description=f"Low Sharpe ratio of {metrics.sharpe_ratio:.2f} suggests poor risk-adjusted performance."
                    ))
            
            # Resource usage recommendations
            if result.resource_usage:
                usage = result.resource_usage
                
                if usage.peak_memory_mb > 1024:
                    recommendations.append(Recommendation(
                        script_id=result.script_id,
                        recommendation="Optimize memory usage",
                        priority="LOW",
                        category="Performance",
                        description=f"High memory usage of {usage.peak_memory_mb:.1f}MB may impact scalability."
                    ))
                
                if result.duration_seconds > 1800:  # 30 minutes
                    recommendations.append(Recommendation(
                        script_id=result.script_id,
                        recommendation="Optimize execution time",
                        priority="MEDIUM",
                        category="Performance",
                        description=f"Long execution time of {result.duration_seconds:.1f} seconds may impact productivity."
                    ))
        
        return recommendations
    
    def _generate_detailed_results(self, results: List[BacktestResult], 
                                 scripts: List[BacktestScript]) -> List[Dict[str, Any]]:
        """Generate detailed results for each script."""
        script_lookup = {s.id: s for s in scripts}
        detailed_results = []
        
        for result in results:
            script = script_lookup.get(result.script_id)
            
            detail = {
                "script_id": result.script_id,
                "execution_id": result.execution_id,
                "status": result.status,
                "duration_seconds": result.duration_seconds,
                "exit_code": result.exit_code,
                "script_info": {
                    "name": script.name if script else "Unknown",
                    "script_type": script.script_type if script else "Unknown",
                    "validation_status": script.validation_status if script else "Unknown",
                    "file_path": script.file_path if script else "Unknown"
                }
            }
            
            # Add performance metrics if available
            if result.performance_metrics:
                detail["performance_metrics"] = {
                    "total_return_pct": result.performance_metrics.total_return_pct,
                    "sharpe_ratio": result.performance_metrics.sharpe_ratio,
                    "max_drawdown_pct": result.performance_metrics.max_drawdown_pct,
                    "win_rate": result.performance_metrics.win_rate,
                    "total_trades": result.performance_metrics.total_trades,
                    "initial_capital": result.performance_metrics.initial_capital,
                    "final_capital": result.performance_metrics.final_capital
                }
            
            # Add resource usage if available
            if result.resource_usage:
                detail["resource_usage"] = {
                    "peak_memory_mb": result.resource_usage.peak_memory_mb,
                    "average_cpu_percent": result.resource_usage.average_cpu_percent
                }
            
            # Add validation errors if any
            if result.validation_errors:
                detail["validation_errors"] = [
                    {"field": e.field, "message": e.message, "severity": e.severity}
                    for e in result.validation_errors
                ]
            
            detailed_results.append(detail)
        
        return detailed_results
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def export_to_json(self, report: ValidationReport) -> str:
        """Export report to JSON format."""
        return json.dumps(report.to_dict(), indent=2)
    
    def export_to_html(self, report: ValidationReport) -> str:
        """Export report to HTML format."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.report_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 14px; color: #6c757d; }}
        .recommendations {{ margin-top: 20px; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .recommendation.high {{ background-color: #f8d7da; }}
        .recommendation.medium {{ background-color: #fff3cd; }}
        .recommendation.low {{ background-color: #d1ecf1; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.report_name}</h1>
        <p>Generated on: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <div class="metric-value">{report.total_scripts}</div>
            <div class="metric-label">Total Scripts</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.passed_scripts}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.failed_scripts}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.error_scripts}</div>
            <div class="metric-label">Errors</div>
        </div>
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
"""
        
        for rec in report.recommendations:
            html += f"""
        <div class="recommendation {rec.priority.lower()}">
            <strong>{rec.recommendation}</strong> ({rec.priority})
            <br>{rec.description}
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def export_to_csv(self, report: ValidationReport) -> str:
        """Export report to CSV format."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Script ID', 'Script Name', 'Status', 'Duration (s)', 'Return %', 
            'Sharpe Ratio', 'Max Drawdown %', 'Win Rate', 'Total Trades'
        ])
        
        # Write data
        for detail in report.detailed_results:
            metrics = detail.get('performance_metrics', {})
            script_info = detail.get('script_info', {})
            
            writer.writerow([
                detail['script_id'],
                script_info.get('name', 'Unknown'),
                detail['status'],
                detail['duration_seconds'],
                metrics.get('total_return_pct', ''),
                metrics.get('sharpe_ratio', ''),
                metrics.get('max_drawdown_pct', ''),
                metrics.get('win_rate', ''),
                metrics.get('total_trades', '')
            ])
        
        return output.getvalue()

