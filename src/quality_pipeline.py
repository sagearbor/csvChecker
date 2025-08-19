"""Main quality checking pipeline that orchestrates all data quality checks."""

from typing import Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd

from .data_loader import load_csv, CSVLoadError
from .checks import check_row_count, check_data_types, check_value_ranges, check_data_consistency, check_automatic_quality


def run_quality_checks(
    file: Union[str, Path], 
    schema: Optional[Dict[str, str]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    min_rows: int = 1
) -> Dict[str, Any]:
    """
    Run comprehensive data quality checks on a CSV file.
    
    Args:
        file: Path to the CSV file
        schema: Dictionary mapping column names to expected types
        rules: Dictionary mapping column names to validation rules
        min_rows: Minimum required number of rows
        
    Returns:
        Dict containing comprehensive quality check results
    """
    results = {
        'file_path': str(file),
        'load_success': False,
        'checks': [],
        'summary': {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'overall_passed': False
        },
        'errors': []
    }
    
    try:
        # Load the CSV file
        df = load_csv(file)
        results['load_success'] = True
        results['data_info'] = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
        
    except CSVLoadError as e:
        results['errors'].append(f"Failed to load CSV: {str(e)}")
        return results
    
    # Run row count check
    try:
        row_check = check_row_count(df, min_rows=min_rows)
        results['checks'].append(row_check)
    except Exception as e:
        results['errors'].append(f"Row count check failed: {str(e)}")
    
    # Run data type check if schema provided
    if schema:
        try:
            type_check = check_data_types(df, schema)
            results['checks'].append(type_check)
        except Exception as e:
            results['errors'].append(f"Data type check failed: {str(e)}")
    
    # Run value range check if rules provided
    if rules:
        try:
            range_check = check_value_ranges(df, rules)
            results['checks'].append(range_check)
        except Exception as e:
            results['errors'].append(f"Value range check failed: {str(e)}")
    
    # Run data consistency check (always run this)
    try:
        consistency_check = check_data_consistency(df)
        results['checks'].append(consistency_check)
    except Exception as e:
        results['errors'].append(f"Data consistency check failed: {str(e)}")
    
    # Run automatic quality check (always run this - main outlier detection)
    try:
        automatic_check = check_automatic_quality(df)
        results['checks'].append(automatic_check)
    except Exception as e:
        results['errors'].append(f"Automatic quality check failed: {str(e)}")
    
    # Calculate summary statistics
    total_checks = len(results['checks'])
    passed_checks = sum(1 for check in results['checks'] if check.get('passed', False))
    failed_checks = total_checks - passed_checks
    
    results['summary'] = {
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'failed_checks': failed_checks,
        'overall_passed': failed_checks == 0 and total_checks > 0,
        'success_rate': round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0
    }
    
    return results


def format_results_summary(results: Dict[str, Any]) -> str:
    """
    Format quality check results into a human-readable summary.
    
    Args:
        results: Results from run_quality_checks
        
    Returns:
        Formatted summary string
    """
    if not results['load_success']:
        return f"❌ Failed to load file: {results.get('errors', ['Unknown error'])[0]}"
    
    summary = results['summary']
    data_info = results.get('data_info', {})
    
    status_emoji = "✅" if summary['overall_passed'] else "❌"
    
    lines = [
        f"{status_emoji} Quality Check Summary for {Path(results['file_path']).name}",
        f"📊 Data: {data_info.get('row_count', 0)} rows × {data_info.get('column_count', 0)} columns",
        f"🔍 Checks: {summary['passed_checks']}/{summary['total_checks']} passed ({summary['success_rate']}%)",
        ""
    ]
    
    # Add details for each check
    for check in results['checks']:
        check_type = check.get('check_type', 'unknown')
        passed = check.get('passed', False)
        emoji = "✅" if passed else "❌"
        message = check.get('message', 'No message')
        lines.append(f"{emoji} {check_type.replace('_', ' ').title()}: {message}")
    
    if results.get('errors'):
        lines.append("\n⚠️  Errors:")
        for error in results['errors']:
            lines.append(f"  • {error}")
    
    return "\n".join(lines)


def get_detailed_issues(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract detailed issue information from quality check results.
    
    Args:
        results: Results from run_quality_checks
        
    Returns:
        Dictionary with detailed issue breakdown
    """
    issues = {
        'data_type_issues': {},
        'value_range_issues': {},
        'row_count_issues': {},
        'total_issue_count': 0
    }
    
    for check in results.get('checks', []):
        check_type = check.get('check_type')
        
        if check_type == 'data_types' and not check.get('passed', True):
            issues['data_type_issues'] = {
                'mismatches': check.get('mismatches', {}),
                'missing_columns': check.get('missing_columns', [])
            }
        
        elif check_type == 'value_ranges' and not check.get('passed', True):
            issues['value_range_issues'] = check.get('violations', {})
            issues['total_issue_count'] += check.get('total_violations', 0)
        
        elif check_type == 'row_count' and not check.get('passed', True):
            issues['row_count_issues'] = {
                'actual_rows': check.get('row_count', 0),
                'required_rows': check.get('min_rows_required', 1)
            }
    
    return issues