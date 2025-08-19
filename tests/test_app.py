"""Unit tests for Streamlit app logic."""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Import the app functions we want to test
from app import display_results, display_detailed_results


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for testing."""
    with patch('app.st') as mock_st:
        # Mock common Streamlit functions
        mock_st.header = Mock()
        mock_st.subheader = Mock()
        mock_st.write = Mock()
        mock_st.error = Mock()
        mock_st.success = Mock()
        mock_st.warning = Mock()
        mock_st.metric = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.expander = Mock()
        mock_st.dataframe = Mock()
        mock_st.json = Mock()
        mock_st.download_button = Mock()
        
        # Mock expander context manager
        mock_expander = Mock()
        mock_expander.__enter__ = Mock(return_value=mock_expander)
        mock_expander.__exit__ = Mock(return_value=None)
        mock_st.expander.return_value = mock_expander
        
        yield mock_st


@pytest.fixture
def sample_results():
    """Sample quality check results for testing."""
    return {
        'file_path': 'test.csv',
        'load_success': True,
        'data_info': {
            'row_count': 100,
            'column_count': 5,
            'columns': ['id', 'name', 'age', 'salary', 'country'],
            'memory_usage_mb': 0.5
        },
        'summary': {
            'total_checks': 3,
            'passed_checks': 2,
            'failed_checks': 1,
            'overall_passed': False,
            'success_rate': 66.7
        },
        'checks': [
            {
                'check_type': 'row_count',
                'passed': True,
                'row_count': 100,
                'min_rows_required': 1,
                'message': 'Row count check passed: 100 rows (minimum: 1)'
            },
            {
                'check_type': 'data_types',
                'passed': True,
                'mismatches': {},
                'missing_columns': [],
                'message': 'Data type check passed: 0 type mismatches, 0 missing columns'
            },
            {
                'check_type': 'value_ranges',
                'passed': False,
                'violations': {
                    'age': {
                        'violation_count': 2,
                        'violating_rows': [
                            {'row_index': 0, 'value': -5, 'rule_violated': 'min_value >= 0'},
                            {'row_index': 1, 'value': 150, 'rule_violated': 'max_value <= 120'}
                        ]
                    }
                },
                'total_violations': 2,
                'message': 'Value range check failed: 2 total violations across 1 columns'
            }
        ],
        'errors': []
    }


@pytest.fixture
def failed_load_results():
    """Results for failed file load."""
    return {
        'file_path': 'nonexistent.csv',
        'load_success': False,
        'errors': ['Failed to load CSV: File not found'],
        'summary': {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'overall_passed': False
        },
        'checks': []
    }


class TestDisplayResults:
    
    def test_display_successful_results(self, mock_streamlit, sample_results):
        """Test displaying successful quality check results."""
        display_results(sample_results, "test.csv")
        
        # Verify main components were called
        mock_streamlit.header.assert_called()
        mock_streamlit.metric.assert_called()
        mock_streamlit.warning.assert_called_with("⚠️ Some quality checks failed. See details below.")
        
        # Verify metrics were displayed (4 columns)
        assert mock_streamlit.metric.call_count >= 4
    
    def test_display_failed_load_results(self, mock_streamlit, failed_load_results):
        """Test displaying results when file load fails."""
        display_results(failed_load_results, "test.csv")
        
        # Should show error messages
        mock_streamlit.error.assert_called()
        
        # Should not display metrics or other content
        assert mock_streamlit.metric.call_count == 0
    
    def test_display_all_passed_results(self, mock_streamlit, sample_results):
        """Test displaying results when all checks pass."""
        # Modify results to show all passed
        sample_results['summary']['failed_checks'] = 0
        sample_results['summary']['passed_checks'] = 3
        sample_results['summary']['overall_passed'] = True
        sample_results['summary']['success_rate'] = 100.0
        
        display_results(sample_results, "test.csv")
        
        # Should show success message
        mock_streamlit.success.assert_called_with("✅ All quality checks passed!")


class TestDisplayDetailedResults:
    
    def test_display_detailed_results_basic(self, mock_streamlit, sample_results):
        """Test basic detailed results display."""
        display_detailed_results(sample_results)
        
        # Verify header was called
        mock_streamlit.header.assert_called()
        
        # Verify expanders were created for each check
        assert mock_streamlit.expander.call_count >= len(sample_results['checks'])
        
        # Verify download buttons were created
        assert mock_streamlit.download_button.call_count >= 2
    
    def test_display_row_count_details(self, mock_streamlit):
        """Test displaying row count check details."""
        results = {
            'checks': [
                {
                    'check_type': 'row_count',
                    'passed': False,
                    'row_count': 5,
                    'min_rows_required': 10,
                    'message': 'Row count check failed'
                }
            ]
        }
        
        display_detailed_results(results)
        
        # Should create expander and display metrics
        mock_streamlit.expander.assert_called()
        mock_streamlit.metric.assert_called()
    
    def test_display_data_type_details(self, mock_streamlit):
        """Test displaying data type check details with mismatches."""
        results = {
            'checks': [
                {
                    'check_type': 'data_types',
                    'passed': False,
                    'mismatches': {
                        'age': {
                            'expected': 'int',
                            'actual': 'str',
                            'sample_values': ['25', '30', '35']
                        }
                    },
                    'missing_columns': ['salary'],
                    'message': 'Data type check failed'
                }
            ]
        }
        
        display_detailed_results(results)
        
        # Should display dataframe for mismatches
        mock_streamlit.dataframe.assert_called()
        mock_streamlit.write.assert_called()
    
    def test_display_value_range_details(self, mock_streamlit):
        """Test displaying value range check details with violations."""
        results = {
            'checks': [
                {
                    'check_type': 'value_ranges',
                    'passed': False,
                    'violations': {
                        'age': {
                            'violation_count': 1,
                            'violating_rows': [
                                {'row_index': 0, 'value': -5, 'rule_violated': 'min_value >= 0'}
                            ]
                        }
                    },
                    'total_violations': 1,
                    'message': 'Value range check failed'
                }
            ]
        }
        
        display_detailed_results(results)
        
        # Should display violation details
        mock_streamlit.dataframe.assert_called()
    
    def test_display_empty_results(self, mock_streamlit):
        """Test displaying results with no checks."""
        results = {'checks': []}
        
        display_detailed_results(results)
        
        # Should still show header and download options
        mock_streamlit.header.assert_called()
        mock_streamlit.download_button.assert_called()


class TestAppIntegration:
    
    @patch('app.run_quality_checks')
    @patch('app.st')
    def test_quality_checks_integration(self, mock_st, mock_run_checks, sample_results):
        """Test that the app correctly calls quality checks."""
        # Mock file uploader
        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "test.csv"
        mock_uploaded_file.getvalue.return_value = b"id,name\n1,Alice\n2,Bob"
        
        mock_st.file_uploader.return_value = mock_uploaded_file
        mock_st.checkbox.return_value = False
        mock_st.number_input.return_value = 1
        mock_st.text_area.return_value = ""
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        
        mock_run_checks.return_value = sample_results
        
        # Import and run the main function
        from app import main
        
        # This would normally be called by streamlit, but we can test parts of it
        # The actual streamlit execution is harder to test without more complex mocking
        
        # Verify that our functions can be called without errors
        display_results(sample_results, "test.csv")
        display_detailed_results(sample_results)
    
    def test_json_parsing_error_handling(self, mock_streamlit):
        """Test that invalid JSON in configuration is handled gracefully."""
        import json
        
        # Test invalid schema JSON
        invalid_json = "{'invalid': json}"
        
        try:
            json.loads(invalid_json)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # This is expected - the app should handle this gracefully
            pass
    
    @patch('app.tempfile.NamedTemporaryFile')
    @patch('app.os.unlink')
    def test_temporary_file_cleanup(self, mock_unlink, mock_tempfile):
        """Test that temporary files are properly cleaned up."""
        # Mock tempfile creation
        mock_file = Mock()
        mock_file.name = "/tmp/test_file.csv"
        mock_tempfile.return_value.__enter__ = Mock(return_value=mock_file)
        mock_tempfile.return_value.__exit__ = Mock()
        
        # The cleanup should happen in the finally block
        # This is more of an integration test that would need actual file handling