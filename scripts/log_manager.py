#!/usr/bin/env python3
"""
Log Manager Utility
Tools for managing and analyzing trading system logs
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import glob

class LogManager:
    """Utility for managing trading system logs"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.log_files = {
            'main': f"{log_dir}/trading_system.log",
            'errors': f"{log_dir}/errors.log",
            'performance': f"{log_dir}/performance.log",
            'security': f"{log_dir}/security.log",
            'api': f"{log_dir}/api.log"
        }
    
    def analyze_logs(self, log_type: str = 'main', hours: int = 24) -> Dict[str, Any]:
        """Analyze logs for the specified time period"""
        log_file = self.log_files.get(log_type)
        if not log_file or not os.path.exists(log_file):
            return {"error": f"Log file {log_type} not found"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        stats = {
            'total_entries': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'performance_metrics': [],
            'errors': [],
            'warnings': [],
            'time_range': {
                'start': None,
                'end': None
            }
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if log_time < cutoff_time:
                            continue
                        
                        stats['total_entries'] += 1
                        
                        # Track time range
                        if not stats['time_range']['start'] or log_time < stats['time_range']['start']:
                            stats['time_range']['start'] = log_time
                        if not stats['time_range']['end'] or log_time > stats['time_range']['end']:
                            stats['time_range']['end'] = log_time
                        
                        # Count by level
                        level = log_entry.get('level', 'INFO')
                        if level == 'ERROR':
                            stats['error_count'] += 1
                            stats['errors'].append(log_entry)
                        elif level == 'WARNING':
                            stats['warning_count'] += 1
                            stats['warnings'].append(log_entry)
                        elif level == 'INFO':
                            stats['info_count'] += 1
                        elif level == 'DEBUG':
                            stats['debug_count'] += 1
                        
                        # Collect performance metrics
                        if 'performance_metric' in log_entry:
                            stats['performance_metrics'].append(log_entry['performance_metric'])
                    
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
        
        except Exception as e:
            return {"error": f"Error reading log file: {e}"}
        
        return stats
    
    def get_recent_errors(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent error logs"""
        stats = self.analyze_logs('errors', hours)
        return stats.get('errors', [])
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary"""
        stats = self.analyze_logs('performance', hours)
        metrics = stats.get('performance_metrics', [])
        
        if not metrics:
            return {"message": "No performance metrics found"}
        
        # Calculate averages
        durations = [m.get('duration', 0) for m in metrics if m.get('duration')]
        success_count = sum(1 for m in metrics if m.get('success', False))
        
        summary = {
            'total_operations': len(metrics),
            'successful_operations': success_count,
            'failed_operations': len(metrics) - success_count,
            'success_rate': (success_count / len(metrics)) * 100 if metrics else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0
        }
        
        return summary
    
    def cleanup_old_logs(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old log files"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_files = []
        total_size_freed = 0
        
        # Find old log files
        for log_file in glob.glob(f"{self.log_dir}/*.log.*"):
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_time < cutoff_time:
                    file_size = os.path.getsize(log_file)
                    os.remove(log_file)
                    cleaned_files.append(log_file)
                    total_size_freed += file_size
            except Exception as e:
                print(f"Error cleaning up {log_file}: {e}")
        
        return {
            'files_removed': len(cleaned_files),
            'size_freed_mb': total_size_freed / (1024 * 1024),
            'files': cleaned_files
        }
    
    def search_logs(self, query: str, log_type: str = 'main', hours: int = 24) -> List[Dict[str, Any]]:
        """Search logs for specific terms"""
        log_file = self.log_files.get(log_type)
        if not log_file or not os.path.exists(log_file):
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if log_time < cutoff_time:
                            continue
                        
                        # Search in message and extra fields
                        message = log_entry.get('message', '').lower()
                        extra_fields = log_entry.get('extra_fields', {})
                        
                        if (query.lower() in message or 
                            any(query.lower() in str(v).lower() for v in extra_fields.values())):
                            results.append(log_entry)
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Error searching logs: {e}")
        
        return results
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get overall log statistics"""
        stats = {}
        
        for log_type, log_file in self.log_files.items():
            if os.path.exists(log_file):
                try:
                    file_size = os.path.getsize(log_file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    stats[log_type] = {
                        'size_mb': file_size / (1024 * 1024),
                        'last_modified': file_time.isoformat(),
                        'exists': True
                    }
                except Exception as e:
                    stats[log_type] = {'error': str(e), 'exists': False}
            else:
                stats[log_type] = {'exists': False}
        
        return stats


def main():
    """Command line interface for log management"""
    parser = argparse.ArgumentParser(description='Trading System Log Manager')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--hours', type=int, default=24, help='Hours to analyze')
    parser.add_argument('--days', type=int, default=30, help='Days for cleanup')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze logs')
    analyze_parser.add_argument('--type', default='main', choices=['main', 'errors', 'performance', 'security', 'api'])
    
    # Errors command
    errors_parser = subparsers.add_parser('errors', help='Show recent errors')
    
    # Performance command
    perf_parser = subparsers.add_parser('performance', help='Show performance summary')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old logs')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--type', default='main', choices=['main', 'errors', 'performance', 'security', 'api'])
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show log statistics')
    
    args = parser.parse_args()
    
    log_manager = LogManager(args.log_dir)
    
    if args.command == 'analyze':
        stats = log_manager.analyze_logs(args.type, args.hours)
        print(json.dumps(stats, indent=2, default=str))
    
    elif args.command == 'errors':
        errors = log_manager.get_recent_errors(args.hours)
        print(f"Recent errors (last {args.hours} hours):")
        for error in errors:
            print(f"- {error.get('timestamp')}: {error.get('message')}")
    
    elif args.command == 'performance':
        summary = log_manager.get_performance_summary(args.hours)
        print(json.dumps(summary, indent=2))
    
    elif args.command == 'cleanup':
        result = log_manager.cleanup_old_logs(args.days)
        print(f"Cleanup completed: {result['files_removed']} files removed, {result['size_freed_mb']:.2f} MB freed")
    
    elif args.command == 'search':
        results = log_manager.search_logs(args.query, args.type, args.hours)
        print(f"Found {len(results)} matches for '{args.query}':")
        for result in results:
            print(f"- {result.get('timestamp')}: {result.get('message')}")
    
    elif args.command == 'stats':
        stats = log_manager.get_log_stats()
        print(json.dumps(stats, indent=2, default=str))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 