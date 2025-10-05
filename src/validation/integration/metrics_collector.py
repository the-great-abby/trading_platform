"""
Metrics collection integration with Prometheus

This service provides metrics collection for validation framework operations
and integrates with Prometheus for monitoring and alerting.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime


class MetricsCollector:
    """
    Metrics collector for validation framework operations.
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.timers: Dict[str, float] = {}
        
        # Prometheus-style metric names
        self.metric_names = {
            "validations_total": "validation_operations_total",
            "validation_duration_seconds": "validation_duration_seconds",
            "scripts_discovered_total": "scripts_discovered_total",
            "database_operations_total": "database_operations_total",
            "batch_validations_total": "batch_validations_total",
            "validation_success_rate": "validation_success_rate",
            "active_validations": "active_validations",
            "memory_usage_bytes": "memory_usage_bytes",
            "cpu_usage_percent": "cpu_usage_percent"
        }
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        
        key = f"{name}_{self._labels_to_key(labels)}"
        self.counters[key] += value
        
        # Record metric point
        metric_point = MetricPoint(
            name=name,
            value=self.counters[key],
            labels=labels,
            timestamp=datetime.now()
        )
        self.metrics[name].append(metric_point)
        
        logger.debug(f"Counter {name} incremented by {value} to {self.counters[key]}")
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        
        key = f"{name}_{self._labels_to_key(labels)}"
        self.gauges[key] = value
        
        # Record metric point
        metric_point = MetricPoint(
            name=name,
            value=value,
            labels=labels,
            timestamp=datetime.now()
        )
        self.metrics[name].append(metric_point)
        
        logger.debug(f"Gauge {name} set to {value}")
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value for histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        
        key = f"{name}_{self._labels_to_key(labels)}"
        self.histograms[key].append(value)
        
        logger.debug(f"Histogram {name} observed value {value}")
    
    def start_timer(self, name: str) -> None:
        """Start a timer for measuring duration."""
        self.timers[name] = time.time()
        logger.debug(f"Timer {name} started")
    
    def stop_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Stop a timer and record the duration.
        
        Args:
            name: Timer name
            labels: Optional labels for the metric
            
        Returns:
            Duration in seconds
        """
        if name not in self.timers:
            logger.warning(f"Timer {name} was not started")
            return 0.0
        
        duration = time.time() - self.timers[name]
        del self.timers[name]
        
        # Record as histogram
        self.observe_histogram(name, duration, labels)
        
        logger.debug(f"Timer {name} stopped: {duration:.3f}s")
        return duration
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """Convert labels dictionary to string key."""
        if not labels:
            return "default"
        return "_".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def record_validation_metric(self, script_type: str, status: str, duration: float) -> None:
        """Record validation-specific metrics."""
        labels = {"script_type": script_type, "status": status}
        
        # Increment total validations
        self.increment_counter(self.metric_names["validations_total"], labels=labels)
        
        # Record duration
        self.observe_histogram(self.metric_names["validation_duration_seconds"], duration, labels)
        
        # Update success rate
        total_validations = sum(
            count for key, count in self.counters.items() 
            if key.startswith(f"{self.metric_names['validations_total']}_")
        )
        successful_validations = sum(
            count for key, count in self.counters.items() 
            if key.startswith(f"{self.metric_names['validations_total']}_") and "status=SUCCESS" in key
        )
        
        if total_validations > 0:
            success_rate = successful_validations / total_validations
            self.set_gauge(self.metric_names["validation_success_rate"], success_rate)
    
    def record_discovery_metric(self, script_count: int) -> None:
        """Record script discovery metrics."""
        self.increment_counter(self.metric_names["scripts_discovered_total"], script_count)
    
    def record_database_metric(self, operation: str, table: str) -> None:
        """Record database operation metrics."""
        labels = {"operation": operation, "table": table}
        self.increment_counter(self.metric_names["database_operations_total"], labels=labels)
    
    def record_batch_metric(self, script_count: int, successful: int, failed: int) -> None:
        """Record batch validation metrics."""
        labels = {"total_scripts": str(script_count)}
        self.increment_counter(self.metric_names["batch_validations_total"], labels=labels)
        
        # Record individual results
        success_labels = {"result": "success"}
        fail_labels = {"result": "failed"}
        self.increment_counter(self.metric_names["validations_total"], successful, success_labels)
        self.increment_counter(self.metric_names["validations_total"], failed, fail_labels)
    
    def record_system_metrics(self) -> None:
        """Record system resource metrics."""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge(self.metric_names["memory_usage_bytes"], memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge(self.metric_names["cpu_usage_percent"], cpu_percent)
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "mean": sum(values) / len(values) if values else 0
                }
                for name, values in self.histograms.items()
            },
            "active_timers": list(self.timers.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Add header
        lines.append("# Validation Framework Metrics")
        lines.append(f"# Generated at: {datetime.now().isoformat()}")
        lines.append("")
        
        # Export counters
        for name, value in self.counters.items():
            metric_name, labels_str = self._parse_metric_name(name)
            if labels_str:
                lines.append(f'{metric_name}{{{labels_str}}} {value}')
            else:
                lines.append(f'{metric_name} {value}')
        
        lines.append("")
        
        # Export gauges
        for name, value in self.gauges.items():
            metric_name, labels_str = self._parse_metric_name(name)
            if labels_str:
                lines.append(f'{metric_name}{{{labels_str}}} {value}')
            else:
                lines.append(f'{metric_name} {value}')
        
        lines.append("")
        
        # Export histogram summaries
        for name, values in self.histograms.items():
            if not values:
                continue
                
            metric_name, labels_str = self._parse_metric_name(name)
            labels_suffix = f"{{{labels_str}}}" if labels_str else ""
            
            # Calculate summary statistics
            count = len(values)
            total = sum(values)
            min_val = min(values)
            max_val = max(values)
            
            # Export summary metrics
            lines.append(f'{metric_name}_count{labels_suffix} {count}')
            lines.append(f'{metric_name}_sum{labels_suffix} {total}')
            lines.append(f'{metric_name}_min{labels_suffix} {min_val}')
            lines.append(f'{metric_name}_max{labels_suffix} {max_val}')
        
        return "\n".join(lines)
    
    def _parse_metric_name(self, name: str) -> tuple:
        """Parse metric name and labels from internal key."""
        if "_" not in name or "=" not in name:
            return name, ""
        
        # Find the last underscore that separates metric name from labels
        parts = name.split("_")
        metric_parts = []
        labels_part = ""
        
        for i, part in enumerate(parts):
            if "=" in part:
                # This is where labels start
                labels_part = "_".join(parts[i:])
                metric_name = "_".join(parts[:i])
                return metric_name, labels_part
        
        return name, ""
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
        logger.info("All metrics reset")


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_validation_metric(script_type: str, status: str, duration: float) -> None:
    """Record validation metric using global collector."""
    collector = get_metrics_collector()
    collector.record_validation_metric(script_type, status, duration)


def record_discovery_metric(script_count: int) -> None:
    """Record discovery metric using global collector."""
    collector = get_metrics_collector()
    collector.record_discovery_metric(script_count)


def record_database_metric(operation: str, table: str) -> None:
    """Record database metric using global collector."""
    collector = get_metrics_collector()
    collector.record_database_metric(operation, table)


def record_batch_metric(script_count: int, successful: int, failed: int) -> None:
    """Record batch metric using global collector."""
    collector = get_metrics_collector()
    collector.record_batch_metric(script_count, successful, failed)

