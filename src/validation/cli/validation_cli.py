"""
CLI interface for the backtest validation framework

This module provides a command-line interface for discovering, executing,
and validating backtest scripts.
"""

import asyncio
import click
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..discovery import BacktestScriptDiscovery
from ..execution import ScriptExecutor, BatchValidator
from ..config import ConfigManager
from ..reporting import ReportGenerator
from ..models.backtest_script import BacktestScript
from ..models.test_configuration import TestConfiguration


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-dir', type=click.Path(), help='Configuration directory')
@click.pass_context
def cli(ctx, verbose, config_dir):
    """Backtest Validation Framework CLI"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_dir'] = Path(config_dir) if config_dir else None


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--script-type', type=click.Choice(['INDIVIDUAL_STRATEGY', 'MULTI_STRATEGY', 'OPTIONS', 'COMPREHENSIVE']), 
              help='Filter by script type')
@click.option('--output', '-o', type=click.File('w'), help='Output file for results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'table']), default='table', 
              help='Output format')
@click.pass_context
def discover(ctx, directory, script_type, output, output_format):
    """Discover backtest scripts in a directory"""
    discovery = BacktestScriptDiscovery()
    
    try:
        scripts = discovery.discover_scripts(
            directory=Path(directory),
            script_type=script_type
        )
        
        if output_format == 'json':
            result = {
                'scripts': [script.to_dict() for script in scripts],
                'total_count': len(scripts),
                'discovered_at': datetime.now().isoformat()
            }
            output_data = json.dumps(result, indent=2)
        else:
            # Table format
            output_data = f"Discovered {len(scripts)} backtest scripts:\n\n"
            output_data += "ID\tName\tType\tStatus\tPath\n"
            output_data += "-" * 80 + "\n"
            
            for script in scripts:
                output_data += f"{script.id[:8]}\t{script.name}\t{script.script_type}\t{script.validation_status}\t{script.file_path}\n"
        
        if output:
            output.write(output_data)
            click.echo(f"Results written to {output.name}")
        else:
            click.echo(output_data)
            
    except Exception as e:
        click.echo(f"Error discovering scripts: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--timeout', type=int, help='Execution timeout in seconds')
@click.option('--parameters', type=click.File('r'), help='JSON file with script parameters')
@click.option('--output', '-o', type=click.File('w'), help='Output file for results')
@click.pass_context
def validate(ctx, script_path, timeout, parameters, output):
    """Validate a single backtest script"""
    executor = ScriptExecutor()
    discovery = BacktestScriptDiscovery()
    
    try:
        # Discover script
        script_dir = Path(script_path).parent
        scripts = discovery.discover_scripts_in_directory(script_dir)
        script = next((s for s in scripts if s.file_path == str(Path(script_path).absolute())), None)
        
        if not script:
            click.echo(f"No backtest script found at {script_path}", err=True)
            raise click.Abort()
        
        # Load parameters if provided
        script_params = None
        if parameters:
            script_params = json.load(parameters)
        
        # Execute validation
        click.echo(f"Validating script: {script.name}")
        result = executor.execute_script(script, script_params, timeout)
        
        # Display results
        click.echo(f"\nValidation Results:")
        click.echo(f"Status: {result.status}")
        click.echo(f"Duration: {result.duration_seconds:.2f} seconds")
        click.echo(f"Exit Code: {result.exit_code}")
        
        if result.performance_metrics:
            metrics = result.performance_metrics
            click.echo(f"\nPerformance Metrics:")
            click.echo(f"Total Return: {metrics.total_return_pct:.2f}%")
            click.echo(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            click.echo(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
            click.echo(f"Win Rate: {metrics.win_rate:.2%}")
            click.echo(f"Total Trades: {metrics.total_trades}")
        
        if result.validation_errors:
            click.echo(f"\nValidation Errors:")
            for error in result.validation_errors:
                click.echo(f"- {error.field}: {error.message}")
        
        # Save results if output specified
        if output:
            result_data = result.to_dict()
            json.dump(result_data, output, indent=2)
            click.echo(f"\nResults saved to {output.name}")
            
    except Exception as e:
        click.echo(f"Error validating script: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--max-parallel', type=int, default=4, help='Maximum parallel executions')
@click.option('--config', type=str, help='Configuration name to use')
@click.option('--output', '-o', type=click.File('w'), help='Output file for report')
@click.option('--format', 'output_format', type=click.Choice(['json', 'html', 'csv']), default='json',
              help='Report format')
@click.pass_context
def batch(ctx, directory, max_parallel, config, output, output_format):
    """Run batch validation on all scripts in a directory"""
    discovery = BacktestScriptDiscovery()
    batch_validator = BatchValidator()
    config_manager = ConfigManager()
    report_generator = ReportGenerator()
    
    try:
        # Load configuration
        if config:
            configuration = config_manager.load_configuration(config)
        else:
            configuration = config_manager.get_default_configuration()
            if not configuration:
                configuration = config_manager.create_default_configuration()
        
        # Discover scripts
        click.echo(f"Discovering scripts in {directory}")
        scripts = discovery.discover_scripts_in_directory(Path(directory))
        click.echo(f"Found {len(scripts)} scripts")
        
        if not scripts:
            click.echo("No scripts found to validate", err=True)
            raise click.Abort()
        
        # Run batch validation
        click.echo(f"Running batch validation with {max_parallel} parallel jobs")
        
        def progress_callback(completed, total, current_script):
            click.echo(f"Progress: {completed}/{total} - {current_script}")
        
        results = batch_validator.validate_batch(
            scripts=scripts,
            configuration=configuration,
            max_parallel_jobs=max_parallel,
            progress_callback=progress_callback
        )
        
        # Generate report
        click.echo("Generating validation report")
        report = report_generator.generate_report(
            report_name=f"Batch Validation - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            results=results,
            scripts=scripts,
            include_consistency_analysis=True,
            include_performance_analysis=True,
            include_recommendations=True
        )
        
        # Display summary
        click.echo(f"\nBatch Validation Summary:")
        click.echo(f"Total Scripts: {report.total_scripts}")
        click.echo(f"Passed: {report.passed_scripts}")
        click.echo(f"Failed: {report.failed_scripts}")
        click.echo(f"Errors: {report.error_scripts}")
        click.echo(f"Success Rate: {report.calculate_success_rate():.1%}")
        
        # Save report
        if output:
            if output_format == 'json':
                report_data = report_generator.export_to_json(report)
            elif output_format == 'html':
                report_data = report_generator.export_to_html(report)
            elif output_format == 'csv':
                report_data = report_generator.export_to_csv(report)
            
            output.write(report_data)
            click.echo(f"Report saved to {output.name}")
        else:
            # Display report summary
            click.echo(f"\nRecommendations:")
            for rec in report.recommendations[:5]:  # Show top 5
                click.echo(f"- {rec.recommendation} ({rec.priority})")
            
    except Exception as e:
        click.echo(f"Error running batch validation: {e}", err=True)
        raise click.Abort()


@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command('list')
@click.pass_context
def config_list(ctx):
    """List all configurations"""
    config_manager = ConfigManager()
    
    try:
        configurations = config_manager.list_configurations()
        
        if not configurations:
            click.echo("No configurations found")
            return
        
        click.echo("Available configurations:")
        click.echo("-" * 60)
        
        for config in configurations:
            default_marker = " (default)" if config.is_default else ""
            click.echo(f"{config.name}{default_marker}")
            click.echo(f"  ID: {config.id}")
            click.echo(f"  Description: {config.description}")
            click.echo(f"  Created: {config.created_at.strftime('%Y-%m-%d %H:%M')}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error listing configurations: {e}", err=True)
        raise click.Abort()


@config.command('create')
@click.argument('name')
@click.option('--description', help='Configuration description')
@click.option('--default', 'set_default', is_flag=True, help='Set as default configuration')
@click.pass_context
def config_create(ctx, name, description, set_default):
    """Create a new configuration"""
    config_manager = ConfigManager()
    
    try:
        configuration = TestConfiguration(
            name=name,
            description=description or "",
            is_default=set_default
        )
        
        saved_config = config_manager.save_configuration(configuration)
        
        if set_default:
            config_manager.set_default_configuration(saved_config.id)
        
        click.echo(f"Created configuration: {saved_config.name}")
        click.echo(f"ID: {saved_config.id}")
        
    except Exception as e:
        click.echo(f"Error creating configuration: {e}", err=True)
        raise click.Abort()


@config.command('set-default')
@click.argument('config_name')
@click.pass_context
def config_set_default(ctx, config_name):
    """Set a configuration as default"""
    config_manager = ConfigManager()
    
    try:
        configuration = config_manager.get_configuration_by_name(config_name)
        if not configuration:
            click.echo(f"Configuration not found: {config_name}", err=True)
            raise click.Abort()
        
        config_manager.set_default_configuration(configuration.id)
        click.echo(f"Set default configuration: {config_name}")
        
    except Exception as e:
        click.echo(f"Error setting default configuration: {e}", err=True)
        raise click.Abort()


@config.command('export')
@click.argument('config_name')
@click.option('--output', '-o', type=click.File('w'), required=True, help='Output file')
@click.pass_context
def config_export(ctx, config_name, output):
    """Export a configuration"""
    config_manager = ConfigManager()
    
    try:
        configuration = config_manager.get_configuration_by_name(config_name)
        if not configuration:
            click.echo(f"Configuration not found: {config_name}", err=True)
            raise click.Abort()
        
        config_data = config_manager.export_configuration(configuration.id)
        json.dump(config_data, output, indent=2)
        
        click.echo(f"Exported configuration: {config_name}")
        click.echo(f"Saved to: {output.name}")
        
    except Exception as e:
        click.echo(f"Error exporting configuration: {e}", err=True)
        raise click.Abort()


@config.command('import')
@click.argument('config_file', type=click.File('r'))
@click.option('--name', help='Name for imported configuration')
@click.pass_context
def config_import(ctx, config_file, name):
    """Import a configuration"""
    config_manager = ConfigManager()
    
    try:
        config_data = json.load(config_file)
        
        if name:
            config_data['name'] = name
        
        imported_config = config_manager.import_configuration(config_data, name)
        
        click.echo(f"Imported configuration: {imported_config.name}")
        click.echo(f"ID: {imported_config.id}")
        
    except Exception as e:
        click.echo(f"Error importing configuration: {e}", err=True)
        raise click.Abort()


def main():
    """Main entry point for the CLI"""
    cli()


if __name__ == '__main__':
    main()













