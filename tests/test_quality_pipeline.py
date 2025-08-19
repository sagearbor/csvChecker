"""Unit tests for quality checking pipeline."""

import pytest
import tempfile
import os
from pathlib import Path

from src.quality_pipeline import run_quality_checks, format_results_summary, get_detailed_issues


@pytest.fixture
def sample_csv():
    """Create a sample CSV file for testing."""
    content = """id,name,age,salary,country
1,Alice,25,50000.0,USA
2,Bob,30,60000.0,CAN
3,Charlie,35,70000.0,USA
4,Diana,28,55000.0,MEX
5,Eve,32,65000.0,USA"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def problematic_csv():
    """Create a CSV file with data quality issues."""
    content = """id,name,age,salary,country
1,Alice,150,50000.0,INVALID
2,Bob,-5,60000.0,CAN
3,Charlie,35,1000000.0,USA"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def empty_csv():
    """Create an empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        f.flush()
        yield f.name
    os.unlink(f.name)


class TestRunQualityChecks:
    
    def test_successful_load_no_checks(self, sample_csv):
        """Test pipeline with successful load but no additional checks."""
        results = run_quality_checks(sample_csv)
        
        assert results['load_success'] == True
        assert results['file_path'] == sample_csv
        assert len(results['errors']) == 0
        assert results['data_info']['row_count'] == 5
        assert results['data_info']['column_count'] == 5
        
        # Should have at least row count check
        assert len(results['checks']) == 1
        assert results['checks'][0]['check_type'] == 'row_count'
        assert results['summary']['total_checks'] == 1
        assert results['summary']['passed_checks'] == 1
    
    def test_with_schema_validation(self, sample_csv):
        """Test pipeline with schema validation."""
        schema = {
            'id': 'int',
            'name': 'str',
            'age': 'int',
            'salary': 'float',
            'country': 'str'
        }
        
        results = run_quality_checks(sample_csv, schema=schema)
        
        assert results['load_success'] == True
        assert len(results['checks']) == 2  # row_count + data_types
        
        # Find the data types check
        type_check = next(c for c in results['checks'] if c['check_type'] == 'data_types')
        assert type_check['passed'] == True
        
        assert results['summary']['total_checks'] == 2
        assert results['summary']['passed_checks'] == 2
        assert results['summary']['overall_passed'] == True
    
    def test_with_value_rules(self, sample_csv):
        """Test pipeline with value range rules."""
        rules = {
            'age': {'min': 20, 'max': 40},
            'salary': {'min': 40000, 'max': 80000},
            'country': {'allowed': ['USA', 'CAN', 'MEX']}
        }
        
        results = run_quality_checks(sample_csv, rules=rules)
        
        assert results['load_success'] == True
        assert len(results['checks']) == 2  # row_count + value_ranges
        
        # Find the value ranges check
        range_check = next(c for c in results['checks'] if c['check_type'] == 'value_ranges')
        assert range_check['passed'] == True
        
        assert results['summary']['overall_passed'] == True
    
    def test_comprehensive_checks_all_pass(self, sample_csv):
        """Test pipeline with all checks enabled and passing."""
        schema = {
            'id': 'int',
            'name': 'str',
            'age': 'int',
            'salary': 'float',
            'country': 'str'
        }
        
        rules = {
            'age': {'min': 20, 'max': 40},
            'salary': {'min': 40000, 'max': 80000},
            'country': {'allowed': ['USA', 'CAN', 'MEX']}
        }
        
        results = run_quality_checks(sample_csv, schema=schema, rules=rules, min_rows=3)
        
        assert results['load_success'] == True
        assert len(results['checks']) == 3  # row_count + data_types + value_ranges
        assert results['summary']['total_checks'] == 3
        assert results['summary']['passed_checks'] == 3
        assert results['summary']['overall_passed'] == True
        assert results['summary']['success_rate'] == 100.0
    
    def test_with_data_quality_issues(self, problematic_csv):
        """Test pipeline with data that has quality issues."""
        rules = {
            'age': {'min': 0, 'max': 100},
            'salary': {'max': 100000},
            'country': {'allowed': ['USA', 'CAN', 'MEX']}
        }
        
        results = run_quality_checks(problematic_csv, rules=rules)
        
        assert results['load_success'] == True
        assert len(results['checks']) == 2  # row_count + value_ranges
        
        # Row count should pass
        row_check = next(c for c in results['checks'] if c['check_type'] == 'row_count')
        assert row_check['passed'] == True
        
        # Value ranges should fail
        range_check = next(c for c in results['checks'] if c['check_type'] == 'value_ranges')
        assert range_check['passed'] == False
        assert range_check['total_violations'] > 0
        
        assert results['summary']['overall_passed'] == False
        assert results['summary']['failed_checks'] > 0
    
    def test_row_count_failure(self, sample_csv):
        """Test pipeline with row count failure."""
        results = run_quality_checks(sample_csv, min_rows=10)
        
        assert results['load_success'] == True
        
        row_check = next(c for c in results['checks'] if c['check_type'] == 'row_count')
        assert row_check['passed'] == False
        
        assert results['summary']['overall_passed'] == False
    
    def test_file_load_failure(self):
        """Test pipeline with file that can't be loaded."""
        results = run_quality_checks("nonexistent.csv")
        
        assert results['load_success'] == False
        assert len(results['errors']) > 0
        assert 'Failed to load CSV' in results['errors'][0]
        assert results['summary']['total_checks'] == 0
    
    def test_empty_file_handling(self, empty_csv):
        """Test pipeline with empty CSV file."""
        results = run_quality_checks(empty_csv)
        
        assert results['load_success'] == False
        assert len(results['errors']) > 0


class TestFormatResultsSummary:
    
    def test_format_successful_results(self, sample_csv):
        """Test formatting of successful quality check results."""
        results = run_quality_checks(sample_csv)
        summary = format_results_summary(results)
        
        assert "✅" in summary
        assert "Quality Check Summary" in summary
        assert "rows × " in summary
        assert "passed" in summary
        assert Path(sample_csv).name in summary
    
    def test_format_failed_results(self, problematic_csv):
        """Test formatting of failed quality check results."""
        rules = {'age': {'min': 0, 'max': 100}}
        results = run_quality_checks(problematic_csv, rules=rules)
        summary = format_results_summary(results)
        
        assert "❌" in summary
        assert "Quality Check Summary" in summary
        assert "Value Ranges" in summary
    
    def test_format_load_failure(self):
        """Test formatting when file fails to load."""
        results = run_quality_checks("nonexistent.csv")
        summary = format_results_summary(results)
        
        assert "❌ Failed to load file" in summary
    
    def test_format_with_errors(self, sample_csv):
        """Test formatting when there are errors during processing."""
        results = run_quality_checks(sample_csv)
        results['errors'].append("Test error message")
        
        summary = format_results_summary(results)
        
        assert "⚠️  Errors:" in summary
        assert "Test error message" in summary


class TestGetDetailedIssues:
    
    def test_detailed_issues_extraction(self, problematic_csv):
        """Test extraction of detailed issue information."""
        schema = {'age': 'int', 'salary': 'float'}
        rules = {
            'age': {'min': 0, 'max': 100},
            'salary': {'max': 100000},
            'country': {'allowed': ['USA', 'CAN', 'MEX']}
        }
        
        results = run_quality_checks(problematic_csv, schema=schema, rules=rules)
        issues = get_detailed_issues(results)
        
        assert 'data_type_issues' in issues
        assert 'value_range_issues' in issues
        assert 'row_count_issues' in issues
        assert issues['total_issue_count'] > 0
        
        # Should have value range violations
        assert len(issues['value_range_issues']) > 0
    
    def test_detailed_issues_no_problems(self, sample_csv):
        """Test detailed issues extraction when no issues exist."""
        results = run_quality_checks(sample_csv)
        issues = get_detailed_issues(results)
        
        assert issues['total_issue_count'] == 0
        assert len(issues['data_type_issues']) == 0
        assert len(issues['value_range_issues']) == 0
        assert len(issues['row_count_issues']) == 0
    
    def test_detailed_issues_row_count_problem(self, sample_csv):
        """Test detailed issues extraction for row count problems."""
        results = run_quality_checks(sample_csv, min_rows=10)
        issues = get_detailed_issues(results)
        
        assert len(issues['row_count_issues']) > 0
        assert 'actual_rows' in issues['row_count_issues']
        assert 'required_rows' in issues['row_count_issues']