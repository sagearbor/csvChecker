"""Unit tests for data quality checks."""

import pytest
import pandas as pd
import numpy as np

from src.checks import check_row_count, check_data_types, check_value_ranges


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'salary': [50000.0, 60000.0, 70000.0, 55000.0, 65000.0],
        'active': [True, False, True, True, False],
        'country': ['USA', 'CAN', 'USA', 'MEX', 'USA']
    })


@pytest.fixture
def empty_df():
    """Create an empty DataFrame."""
    return pd.DataFrame()


class TestRowCountCheck:
    
    def test_row_count_pass_default(self, sample_df):
        """Test row count check with default minimum (1)."""
        result = check_row_count(sample_df)
        
        assert result['check_type'] == 'row_count'
        assert result['passed'] == True
        assert result['row_count'] == 5
        assert result['min_rows_required'] == 1
        assert 'passed' in result['message']
    
    def test_row_count_pass_custom_minimum(self, sample_df):
        """Test row count check with custom minimum."""
        result = check_row_count(sample_df, min_rows=3)
        
        assert result['passed'] == True
        assert result['row_count'] == 5
        assert result['min_rows_required'] == 3
    
    def test_row_count_fail(self, sample_df):
        """Test row count check failure."""
        result = check_row_count(sample_df, min_rows=10)
        
        assert result['passed'] == False
        assert result['row_count'] == 5
        assert result['min_rows_required'] == 10
        assert 'failed' in result['message']
    
    def test_row_count_empty_dataframe(self, empty_df):
        """Test row count check with empty DataFrame."""
        result = check_row_count(empty_df)
        
        assert result['passed'] == False
        assert result['row_count'] == 0
        assert result['min_rows_required'] == 1


class TestDataTypeCheck:
    
    def test_data_types_all_correct(self, sample_df):
        """Test data type check with all correct types."""
        schema = {
            'id': 'int',
            'name': 'str',
            'age': 'int',
            'salary': 'float',
            'active': 'bool'
        }
        
        result = check_data_types(sample_df, schema)
        
        assert result['check_type'] == 'data_types'
        assert result['passed'] == True
        assert len(result['mismatches']) == 0
        assert len(result['missing_columns']) == 0
        assert 'passed' in result['message']
    
    def test_data_types_with_mismatches(self, sample_df):
        """Test data type check with type mismatches."""
        schema = {
            'id': 'str',  # Should be int
            'age': 'float',  # Should be int
            'name': 'int'  # Should be str
        }
        
        result = check_data_types(sample_df, schema)
        
        assert result['passed'] == False
        assert len(result['mismatches']) == 3
        assert 'id' in result['mismatches']
        assert 'age' in result['mismatches']
        assert 'name' in result['mismatches']
        
        # Check mismatch details
        assert result['mismatches']['id']['expected'] == 'str'
        assert 'int' in result['mismatches']['id']['actual']
    
    def test_data_types_missing_columns(self, sample_df):
        """Test data type check with missing columns."""
        schema = {
            'id': 'int',
            'missing_col': 'str',
            'another_missing': 'float'
        }
        
        result = check_data_types(sample_df, schema)
        
        assert result['passed'] == False
        assert len(result['missing_columns']) == 2
        assert 'missing_col' in result['missing_columns']
        assert 'another_missing' in result['missing_columns']
    
    def test_data_types_empty_schema(self, sample_df):
        """Test data type check with empty schema."""
        result = check_data_types(sample_df, {})
        
        assert result['passed'] == True
        assert len(result['mismatches']) == 0
        assert len(result['missing_columns']) == 0


class TestValueRangeCheck:
    
    def test_value_ranges_all_pass(self, sample_df):
        """Test value range check with all valid values."""
        rules = {
            'age': {'min': 20, 'max': 40},
            'salary': {'min': 40000, 'max': 80000},
            'country': {'allowed': ['USA', 'CAN', 'MEX']}
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['check_type'] == 'value_ranges'
        assert result['passed'] == True
        assert result['total_violations'] == 0
        assert len(result['violations']) == 0
        assert 'passed' in result['message']
    
    def test_value_ranges_min_violations(self, sample_df):
        """Test value range check with minimum value violations."""
        rules = {
            'age': {'min': 30}  # Alice (25) and Diana (28) violate this
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['passed'] == False
        assert result['total_violations'] == 2
        assert 'age' in result['violations']
        assert result['violations']['age']['violation_count'] == 2
        
        # Check violation details
        violations = result['violations']['age']['violating_rows']
        ages = [v['value'] for v in violations]
        assert 25 in ages
        assert 28 in ages
    
    def test_value_ranges_max_violations(self, sample_df):
        """Test value range check with maximum value violations."""
        rules = {
            'salary': {'max': 60000}  # Charlie (70000) and Eve (65000) violate this
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['passed'] == False
        assert result['total_violations'] == 2
        assert 'salary' in result['violations']
    
    def test_value_ranges_allowed_values_violations(self, sample_df):
        """Test value range check with allowed values violations."""
        rules = {
            'country': {'allowed': ['USA', 'CAN']}  # MEX is not allowed
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['passed'] == False
        assert result['total_violations'] == 1
        assert 'country' in result['violations']
        
        violation = result['violations']['country']['violating_rows'][0]
        assert violation['value'] == 'MEX'
    
    def test_value_ranges_missing_column(self, sample_df):
        """Test value range check with missing column."""
        rules = {
            'missing_col': {'min': 0, 'max': 100}
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['passed'] == False
        assert 'missing_col' in result['violations']
        assert 'not found' in result['violations']['missing_col']['error']
    
    def test_value_ranges_combined_rules(self, sample_df):
        """Test value range check with multiple rule types on same column."""
        rules = {
            'age': {'min': 25, 'max': 32}  # Should allow Alice, Bob, Diana, Eve but not Charlie
        }
        
        result = check_value_ranges(sample_df, rules)
        
        assert result['passed'] == False
        assert result['total_violations'] == 1
        
        violation = result['violations']['age']['violating_rows'][0]
        assert violation['value'] == 35  # Charlie's age
    
    def test_value_ranges_empty_rules(self, sample_df):
        """Test value range check with empty rules."""
        result = check_value_ranges(sample_df, {})
        
        assert result['passed'] == True
        assert result['total_violations'] == 0
        assert len(result['violations']) == 0