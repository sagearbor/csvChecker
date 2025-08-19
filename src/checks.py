"""Data quality check functions."""

import pandas as pd
from typing import Dict, Any, List, Union, Optional
import re
from datetime import datetime


def check_row_count(df: pd.DataFrame, min_rows: int = 1) -> Dict[str, Any]:
    """
    Check if DataFrame has minimum required number of rows.
    
    Args:
        df: DataFrame to check
        min_rows: Minimum required number of rows
        
    Returns:
        Dict containing check results
    """
    row_count = len(df)
    passed = row_count >= min_rows
    
    return {
        'check_type': 'row_count',
        'passed': passed,
        'row_count': row_count,
        'min_rows_required': min_rows,
        'message': f"Row count check {'passed' if passed else 'failed'}: {row_count} rows (minimum: {min_rows})"
    }


def check_data_types(df: pd.DataFrame, schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate DataFrame column types against expected schema.
    Now includes content validation to catch invalid values within columns.
    
    Args:
        df: DataFrame to validate
        schema: Dictionary mapping column names to expected types
                Supported types: 'int', 'float', 'str', 'bool', 'datetime'
        
    Returns:
        Dict containing validation results and mismatched columns
    """
    type_mapping = {
        'int': ['int64', 'int32', 'Int64', 'Int32'],
        'float': ['float64', 'float32'],
        'str': ['object', 'string'],
        'bool': ['bool'],
        'datetime': ['datetime64[ns]', 'datetime64']
    }
    
    mismatches = {}
    missing_columns = []
    content_issues = {}
    
    for column, expected_type in schema.items():
        if column not in df.columns:
            missing_columns.append(column)
            continue
            
        actual_type = str(df[column].dtype)
        expected_dtypes = type_mapping.get(expected_type, [expected_type])
        
        # Check pandas dtype mismatch
        if actual_type not in expected_dtypes:
            mismatches[column] = {
                'expected': expected_type,
                'actual': actual_type,
                'sample_values': df[column].head(3).tolist()
            }
        
        # Check content validity regardless of pandas dtype
        invalid_values = _check_content_validity(df[column], expected_type)
        if invalid_values:
            content_issues[column] = {
                'expected_type': expected_type,
                'invalid_values': invalid_values[:10],  # Limit to first 10
                'total_invalid': len(invalid_values)
            }
    
    total_issues = len(mismatches) + len(content_issues)
    passed = total_issues == 0 and len(missing_columns) == 0
    
    return {
        'check_type': 'data_types',
        'passed': passed,
        'mismatches': mismatches,
        'content_issues': content_issues,
        'missing_columns': missing_columns,
        'message': f"Data type check {'passed' if passed else 'failed'}: {len(mismatches)} dtype mismatches, {len(content_issues)} content issues, {len(missing_columns)} missing columns"
    }


def check_value_ranges(df: pd.DataFrame, rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check value ranges for numeric columns and allowed values for categorical columns.
    
    Args:
        df: DataFrame to validate
        rules: Dictionary mapping column names to validation rules
               Rules can contain:
               - 'min': minimum allowed value (numeric)
               - 'max': maximum allowed value (numeric)
               - 'allowed': list of allowed values (categorical)
               
    Returns:
        Dict containing validation results and violations
    """
    violations = {}
    
    for column, rule_set in rules.items():
        if column not in df.columns:
            violations[column] = {
                'error': f"Column '{column}' not found in DataFrame",
                'violation_count': 0,
                'violating_rows': []
            }
            continue
            
        column_violations = []
        
        # Check numeric range constraints
        if 'min' in rule_set:
            min_val = rule_set['min']
            mask = df[column] < min_val
            if mask.any():
                violating_indices = df[mask].index.tolist()
                column_violations.extend([
                    {
                        'row_index': idx,
                        'value': df.loc[idx, column],
                        'rule_violated': f'min_value >= {min_val}'
                    }
                    for idx in violating_indices
                ])
        
        if 'max' in rule_set:
            max_val = rule_set['max']
            mask = df[column] > max_val
            if mask.any():
                violating_indices = df[mask].index.tolist()
                column_violations.extend([
                    {
                        'row_index': idx,
                        'value': df.loc[idx, column],
                        'rule_violated': f'max_value <= {max_val}'
                    }
                    for idx in violating_indices
                ])
        
        # Check allowed values (categorical)
        if 'allowed' in rule_set:
            allowed_vals = rule_set['allowed']
            mask = ~df[column].isin(allowed_vals)
            if mask.any():
                violating_indices = df[mask].index.tolist()
                column_violations.extend([
                    {
                        'row_index': idx,
                        'value': df.loc[idx, column],
                        'rule_violated': f'value must be in {allowed_vals}'
                    }
                    for idx in violating_indices
                ])
        
        if column_violations:
            violations[column] = {
                'violation_count': len(column_violations),
                'violating_rows': column_violations[:10],  # Limit to first 10 for readability
                'total_violations': len(column_violations)
            }
    
    total_violations = sum(v.get('violation_count', 0) for v in violations.values())
    passed = total_violations == 0
    
    return {
        'check_type': 'value_ranges',
        'passed': passed,
        'violations': violations,
        'total_violations': total_violations,
        'message': f"Value range check {'passed' if passed else 'failed'}: {total_violations} total violations across {len(violations)} columns"
    }


def _check_content_validity(series: pd.Series, expected_type: str) -> List[Dict[str, Any]]:
    """
    Check if the actual content of a series matches the expected data type.
    
    Args:
        series: Pandas series to validate
        expected_type: Expected data type (int, float, str, bool, datetime)
        
    Returns:
        List of invalid values with their row indices
    """
    invalid_values = []
    
    for idx, value in series.items():
        # Skip NaN values as they're handled separately
        if pd.isna(value):
            continue
            
        value_str = str(value).strip()
        is_valid = True
        
        if expected_type == 'int':
            is_valid = _is_valid_integer(value_str)
        elif expected_type == 'float':
            is_valid = _is_valid_float(value_str)
        elif expected_type == 'datetime':
            is_valid = _is_valid_date(value_str)
        elif expected_type == 'bool':
            is_valid = _is_valid_boolean(value_str)
        # For 'str' type, everything is valid
        
        if not is_valid:
            invalid_values.append({
                'row_index': int(idx),
                'value': value,
                'issue': f'Invalid {expected_type}: "{value_str}"'
            })
    
    return invalid_values


def _is_valid_integer(value_str: str) -> bool:
    """Check if string represents a valid integer."""
    try:
        int(value_str)
        return True
    except ValueError:
        return False


def _is_valid_float(value_str: str) -> bool:
    """Check if string represents a valid float."""
    try:
        float(value_str)
        return True
    except ValueError:
        return False


def _is_valid_date(value_str: str) -> bool:
    """Check if string represents a valid date."""
    # Common date patterns
    date_patterns = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
    ]
    
    # First check if it matches common date patterns
    for pattern in date_patterns:
        if re.match(pattern, value_str):
            # Try to parse it
            try:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                    try:
                        datetime.strptime(value_str, fmt)
                        return True
                    except ValueError:
                        continue
            except ValueError:
                pass
    
    return False


def _is_valid_boolean(value_str: str) -> bool:
    """Check if string represents a valid boolean."""
    valid_bools = {'true', 'false', '1', '0', 'yes', 'no', 'y', 'n', 't', 'f'}
    return value_str.lower() in valid_bools


def check_data_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for general data consistency issues like missing values, 
    mixed data types within columns, and suspicious patterns.
    
    Args:
        df: DataFrame to check
        
    Returns:
        Dict containing consistency check results
    """
    issues = {}
    
    for column in df.columns:
        column_issues = []
        
        # Check for missing values
        missing_count = df[column].isna().sum()
        if missing_count > 0:
            column_issues.append({
                'type': 'missing_values',
                'count': int(missing_count),
                'percentage': round(missing_count / len(df) * 100, 2)
            })
        
        # Check for mixed data types (numeric and text mixed)
        if df[column].dtype == 'object':
            numeric_count = 0
            text_count = 0
            
            for value in df[column].dropna():
                value_str = str(value).strip()
                if _is_valid_float(value_str):
                    numeric_count += 1
                else:
                    text_count += 1
            
            if numeric_count > 0 and text_count > 0:
                column_issues.append({
                    'type': 'mixed_types',
                    'numeric_values': numeric_count,
                    'text_values': text_count,
                    'suggestion': 'Column contains both numeric and text values'
                })
        
        # Check for suspicious patterns
        unique_values = df[column].nunique()
        total_values = len(df[column].dropna())
        
        if unique_values == 1 and total_values > 1:
            column_issues.append({
                'type': 'constant_values',
                'message': 'All non-null values are identical'
            })
        
        if column_issues:
            issues[column] = column_issues
    
    passed = len(issues) == 0
    total_issues = sum(len(col_issues) for col_issues in issues.values())
    
    return {
        'check_type': 'data_consistency',
        'passed': passed,
        'issues': issues,
        'total_issues': total_issues,
        'message': f"Data consistency check {'passed' if passed else 'failed'}: {total_issues} issues found across {len(issues)} columns"
    }