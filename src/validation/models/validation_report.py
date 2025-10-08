"""
ValidationReport model for the validation framework

Aggregated results from testing multiple backtest scripts with pass/fail status and detailed analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid


class ExecutionSummary(BaseModel):
    """Summary of execution statistics"""
    total_execution_time_seconds: float = Field(..., description="Total execution time")
    average_execution_time_seconds: float = Field(..., description="Average execution time")
    parallel_execution_enabled: bool = Field(..., description="Whether parallel execution was used")
    success_rate: float = Field(..., description="Success rate (0.0 to 1.0)")
    failure_rate: float = Field(..., description="Failure rate (0.0 to 1.0)")
    
    @validator('success_rate', 'failure_rate')
    def validate_rates(cls, v):
        """Validate rates are between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('rates must be between 0.0 and 1.0')
        return v


class ConsistencyResults(BaseModel):
    """Consistency analysis results"""
    consistent_scripts: List[str] = Field(default_factory=list, description="IDs of consistent scripts")
    inconsistent_scripts: List[str] = Field(default_factory=list, description="IDs of inconsistent scripts")
    consistency_score: float = Field(..., description="Overall consistency score (0-100)")
    inconsistency_details: List[Dict[str, Any]] = Field(default_factory=list, description="Inconsistency details")
    
    @validator('consistency_score')
    def validate_consistency_score(cls, v):
        """Validate consistency score is between 0 and 100"""
        if not 0.0 <= v <= 100.0:
            raise ValueError('consistency_score must be between 0.0 and 100.0')
        return v


class PerformanceAnalysis(BaseModel):
    """Performance analysis results"""
    average_return: float = Field(..., description="Average return percentage")
    average_sharpe: float = Field(..., description="Average Sharpe ratio")
    average_drawdown: float = Field(..., description="Average drawdown percentage")
    average_win_rate: float = Field(..., description="Average win rate")
    performance_trends: Dict[str, Any] = Field(default_factory=dict, description="Performance trends")
    top_performers: List[str] = Field(default_factory=list, description="Top performing script IDs")
    underperformers: List[str] = Field(default_factory=list, description="Underperforming script IDs")


class Recommendation(BaseModel):
    """Recommendation for script improvement"""
    script_id: str = Field(..., description="ID of the script")
    recommendation: str = Field(..., description="Recommendation text")
    priority: str = Field(..., description="Priority level (HIGH, MEDIUM, LOW)")
    category: str = Field(..., description="Recommendation category")
    description: str = Field(..., description="Detailed description")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority is valid"""
        if v not in ['HIGH', 'MEDIUM', 'LOW']:
            raise ValueError('priority must be HIGH, MEDIUM, or LOW')
        return v


class ValidationReport(BaseModel):
    """
    Aggregated results from testing multiple backtest scripts with pass/fail status and detailed analysis.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    report_name: str = Field(..., description="Report name")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    total_scripts: int = Field(..., description="Total number of scripts tested")
    passed_scripts: int = Field(..., description="Number of scripts that passed")
    failed_scripts: int = Field(..., description="Number of scripts that failed")
    error_scripts: int = Field(..., description="Number of scripts that errored")
    execution_summary: Optional[ExecutionSummary] = Field(None, description="Execution summary")
    consistency_results: Optional[ConsistencyResults] = Field(None, description="Consistency analysis")
    performance_analysis: Optional[PerformanceAnalysis] = Field(None, description="Performance analysis")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Recommendations")
    detailed_results: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed results")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @validator('passed_scripts', 'failed_scripts', 'error_scripts')
    def validate_script_counts(cls, v):
        """Validate script counts are non-negative"""
        if v < 0:
            raise ValueError('script counts must be non-negative')
        return v
    
    @validator('total_scripts')
    def validate_total_scripts(cls, v, values):
        """Validate total scripts matches sum of individual counts"""
        if 'passed_scripts' in values and 'failed_scripts' in values and 'error_scripts' in values:
            total = values['passed_scripts'] + values['failed_scripts'] + values['error_scripts']
            if v != total:
                raise ValueError('total_scripts must equal sum of passed, failed, and error scripts')
        return v
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_recommendation(self, script_id: str, recommendation: str, priority: str, 
                          category: str, description: str) -> None:
        """Add a recommendation to the report"""
        rec = Recommendation(
            script_id=script_id,
            recommendation=recommendation,
            priority=priority,
            category=category,
            description=description
        )
        self.recommendations.append(rec)
    
    def get_recommendations_by_priority(self, priority: str) -> List[Recommendation]:
        """Get recommendations by priority level"""
        return [rec for rec in self.recommendations if rec.priority == priority]
    
    def get_recommendations_by_script(self, script_id: str) -> List[Recommendation]:
        """Get recommendations for a specific script"""
        return [rec for rec in self.recommendations if rec.script_id == script_id]
    
    def calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_scripts == 0:
            return 0.0
        return self.passed_scripts / self.total_scripts
    
    def calculate_failure_rate(self) -> float:
        """Calculate overall failure rate"""
        if self.total_scripts == 0:
            return 0.0
        return (self.failed_scripts + self.error_scripts) / self.total_scripts
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_scripts": self.total_scripts,
            "passed_scripts": self.passed_scripts,
            "failed_scripts": self.failed_scripts,
            "error_scripts": self.error_scripts,
            "success_rate": self.calculate_success_rate(),
            "failure_rate": self.calculate_failure_rate(),
            "total_recommendations": len(self.recommendations),
            "high_priority_recommendations": len(self.get_recommendations_by_priority("HIGH")),
            "medium_priority_recommendations": len(self.get_recommendations_by_priority("MEDIUM")),
            "low_priority_recommendations": len(self.get_recommendations_by_priority("LOW"))
        }
    
    def is_healthy(self) -> bool:
        """Check if the validation report indicates a healthy system"""
        success_rate = self.calculate_success_rate()
        high_priority_issues = len(self.get_recommendations_by_priority("HIGH"))
        
        return success_rate >= 0.8 and high_priority_issues == 0
    
    def needs_attention(self) -> bool:
        """Check if the validation report needs attention"""
        success_rate = self.calculate_success_rate()
        high_priority_issues = len(self.get_recommendations_by_priority("HIGH"))
        
        return success_rate < 0.6 or high_priority_issues > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "report_name": self.report_name,
            "generated_at": self.generated_at.isoformat(),
            "total_scripts": self.total_scripts,
            "passed_scripts": self.passed_scripts,
            "failed_scripts": self.failed_scripts,
            "error_scripts": self.error_scripts,
            "execution_summary": self.execution_summary.dict() if self.execution_summary else None,
            "consistency_results": self.consistency_results.dict() if self.consistency_results else None,
            "performance_analysis": self.performance_analysis.dict() if self.performance_analysis else None,
            "recommendations": [rec.dict() for rec in self.recommendations],
            "detailed_results": self.detailed_results,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationReport':
        """Create instance from dictionary"""
        # Handle datetime fields
        if 'generated_at' in data and isinstance(data['generated_at'], str):
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Handle nested models
        if 'execution_summary' in data and data['execution_summary']:
            data['execution_summary'] = ExecutionSummary(**data['execution_summary'])
        
        if 'consistency_results' in data and data['consistency_results']:
            data['consistency_results'] = ConsistencyResults(**data['consistency_results'])
        
        if 'performance_analysis' in data and data['performance_analysis']:
            data['performance_analysis'] = PerformanceAnalysis(**data['performance_analysis'])
        
        if 'recommendations' in data:
            data['recommendations'] = [Recommendation(**rec) for rec in data['recommendations']]
        
        return cls(**data)













