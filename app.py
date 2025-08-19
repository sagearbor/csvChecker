"""Streamlit frontend for CSV data quality checker."""

import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
import json

from src.quality_pipeline import run_quality_checks, format_results_summary, get_detailed_issues


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="CSV Data Quality Checker",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 CSV Data Quality Checker")
    st.markdown("**Automatic outlier detection powered by intelligent data type inference.** Upload a CSV file and the tool will automatically analyze each column, infer the expected data types, and identify problematic values like invalid dates, non-numeric data in numeric columns, and inconsistent formats.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Minimum rows setting
        min_rows = st.number_input(
            "Minimum Required Rows",
            min_value=1,
            value=1,
            help="Minimum number of rows required in the CSV file"
        )
        
        # Schema configuration (now optional - automatic detection is primary)
        st.subheader("🔍 Automatic Quality Detection")
        st.info("The tool automatically infers data types and detects outliers. Manual schema is optional for additional validation.")
        
        schema_enabled = st.checkbox("Enable manual data type validation (advanced)")
        schema_json = ""
        if schema_enabled:
            st.warning("⚠️ Manual schema will override automatic detection. Only use if you need specific type constraints.")
            schema_json = st.text_area(
                "Manual Schema (JSON format)",
                value='{\n  "participant_id": "str",\n  "visit_date": "datetime",\n  "age": "int",\n  "gender": "str",\n  "blood_pressure": "str",\n  "diagnosis": "str"\n}',
                height=150,
                help="Define expected data types for columns. Supported types: int, float, str, bool, datetime"
            )
        
        # Rules configuration
        st.subheader("Value Validation Rules (Optional)")
        rules_enabled = st.checkbox("Enable value range/set validation")
        rules_json = ""
        if rules_enabled:
            rules_json = st.text_area(
                "Rules (JSON format)",
                value='{\n  "age": {"min": 0, "max": 120},\n  "gender": {"allowed": ["M", "F", "Other"]},\n  "diagnosis": {"allowed": ["Healthy", "Hypertension", "Diabetes", "Asthma"]}\n}',
                height=150,
                help="Define validation rules for columns. Use 'min'/'max' for numeric ranges, 'allowed' for categorical values"
            )
    
    # Main content area - CSV Input Options
    st.header("📄 CSV Input")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload CSV File", "Paste CSV Data"],
        help="Select how you want to provide your CSV data"
    )
    
    csv_data = None
    filename = None
    
    if input_method == "Upload CSV File":
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file to analyze its data quality"
        )
        
        if uploaded_file is not None:
            csv_data = uploaded_file.getvalue().decode('utf-8')
            filename = uploaded_file.name
    
    else:  # Paste CSV Data
        col1, col2 = st.columns([3, 1])
        
        # Initialize session state for example CSV
        if 'example_csv' not in st.session_state:
            st.session_state.example_csv = ""
        
        example_csv_content = """participant_id,visit_date,age,gender,blood_pressure,diagnosis
P001,2025-01-02,34,M,120/80,Healthy
P002,not_a_date,45,F,135/85,Hypertension
P003,2025-01-04,29,F,abc,Healthy
P004,2025-01-05,51,X,142/90,Diabetes
P005,2025-01-08,62,M,150/95,Hypertension
P006,2025-01-09,NaN,F,125/82,Healthy
P007,2025-01-11,41,M,138/88,Hypertension
P008,wrong_date,33,F,130/85,Healthy
P009,2025-01-14,27,F,127/83,Asthma
P010,2025-01-15,invalid_age,M,140/89,Diabetes"""
        
        with col1:
            csv_text = st.text_area(
                "Paste your CSV data here:",
                value=st.session_state.example_csv,
                height=200,
                placeholder="participant_id,visit_date,age,gender,blood_pressure,diagnosis\nP001,2025-01-02,34,M,120/80,Healthy\nP002,not_a_date,45,F,135/85,Hypertension\n...",
                help="Paste CSV data including headers"
            )
        
        with col2:
            st.write("**Example CSV:**")
            if st.button("📋 Load Example", help="Load example CSV with data quality issues"):
                st.session_state.example_csv = example_csv_content
                st.rerun()
            
            # Show example in expandable section
            with st.expander("👀 View Example CSV"):
                st.code(example_csv_content, language="csv")
                
                st.info("**Issues in this example:**\n"
                       "• Invalid dates: 'not_a_date', 'wrong_date'\n"
                       "• Invalid ages: 'NaN', 'invalid_age'\n"
                       "• Invalid blood pressure: 'abc'\n"
                       "• Click 'Load Example' button above to test!")
        
        if csv_text.strip():
            csv_data = csv_text
            filename = "pasted_data.csv"
    
    if csv_data is not None:
        # Save CSV data to temporary file (works for both upload and paste)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv", encoding='utf-8') as tmp_file:
            tmp_file.write(csv_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Parse configurations
            schema = None
            if schema_enabled and schema_json.strip():
                try:
                    schema = json.loads(schema_json)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid schema JSON: {e}")
                    return
            
            rules = None
            if rules_enabled and rules_json.strip():
                try:
                    rules = json.loads(rules_json)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid rules JSON: {e}")
                    return
            
            # Run quality checks
            with st.spinner("Running quality checks..."):
                results = run_quality_checks(
                    tmp_file_path,
                    schema=schema,
                    rules=rules,
                    min_rows=min_rows
                )
            
            # Display results
            display_results(results, filename)
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    else:
        # Show example/instructions when no data is provided
        st.info("👆 Please upload a CSV file or paste CSV data to begin quality analysis")
        
        with st.expander("📖 How to use this tool"):
            st.markdown("""
            ### Steps:
            1. **Provide CSV Data**: Either upload a file or paste CSV data
               - **Upload**: Select a .csv file from your computer
               - **Paste**: Copy and paste CSV data directly, or click 'Load Example'
            2. **Automatic Analysis**: The tool automatically detects data types and finds outliers
            3. **Optional Configuration**: Use the sidebar for additional validation rules:
               - **Minimum rows**: Set the minimum number of rows required  
               - **Manual schema**: Override automatic detection (advanced users)
               - **Value rules**: Set numeric ranges or allowed categorical values
            4. **Review results**: The tool automatically detects outliers and displays detailed analysis
            
            ### Example Schema:
            ```json
            {
              "id": "int",
              "name": "str", 
              "age": "int",
              "salary": "float"
            }
            ```
            
            ### Example Rules:
            ```json
            {
              "age": {"min": 0, "max": 120},
              "salary": {"min": 0, "max": 1000000},
              "department": {"allowed": ["HR", "IT", "Sales"]}
            }
            ```
            """)


def display_results(results: dict, filename: str):
    """Display quality check results in the Streamlit interface."""
    
    # Summary section
    st.header("📊 Summary Dashboard")
    
    if not results['load_success']:
        st.error("❌ Failed to load the CSV file")
        for error in results.get('errors', []):
            st.error(f"Error: {error}")
        return
    
    # Key metrics
    data_info = results.get('data_info', {})
    summary = results.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Rows", 
            data_info.get('row_count', 0),
            help="Total number of rows in the dataset"
        )
    
    with col2:
        st.metric(
            "Columns", 
            data_info.get('column_count', 0),
            help="Total number of columns in the dataset"
        )
    
    with col3:
        st.metric(
            "Checks Passed", 
            f"{summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)}",
            help="Number of quality checks that passed"
        )
    
    with col4:
        success_rate = summary.get('success_rate', 0)
        st.metric(
            "Success Rate", 
            f"{success_rate}%",
            delta=f"{success_rate - 100:.1f}%" if success_rate < 100 else None,
            help="Percentage of quality checks that passed"
        )
    
    # Overall status
    if summary.get('overall_passed', False):
        st.success("✅ All quality checks passed!")
    else:
        st.warning("⚠️ Some quality checks failed. See details below.")
    
    # Detailed results
    display_detailed_results(results)


def display_detailed_results(results: dict):
    """Display detailed quality check results."""
    
    st.header("🔍 Detailed Results")
    
    # Check results
    for i, check in enumerate(results.get('checks', [])):
        check_type = check.get('check_type', 'unknown').replace('_', ' ').title()
        passed = check.get('passed', False)
        
        with st.expander(
            f"{'✅' if passed else '❌'} {check_type} Check", 
            expanded=not passed
        ):
            st.write(f"**Status**: {'Passed' if passed else 'Failed'}")
            st.write(f"**Message**: {check.get('message', 'No message')}")
            
            # Display specific details based on check type
            if check.get('check_type') == 'row_count':
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Actual Rows", check.get('row_count', 0))
                with col2:
                    st.metric("Required Minimum", check.get('min_rows_required', 1))
            
            elif check.get('check_type') == 'data_types':
                mismatches = check.get('mismatches', {})
                missing = check.get('missing_columns', [])
                
                if mismatches:
                    st.subheader("Type Mismatches")
                    mismatch_data = []
                    for col, details in mismatches.items():
                        mismatch_data.append({
                            'Column': col,
                            'Expected Type': details['expected'],
                            'Actual Type': details['actual'],
                            'Sample Values': str(details['sample_values'][:3])
                        })
                    st.dataframe(pd.DataFrame(mismatch_data), use_container_width=True)
                
                if missing:
                    st.subheader("Missing Columns")
                    st.write(", ".join(missing))
                
                # Display content issues (new feature)
                content_issues = check.get('content_issues', {})
                if content_issues:
                    st.subheader("Content Issues")
                    for col, issue_info in content_issues.items():
                        st.write(f"**{col}** ({issue_info['total_invalid']} invalid values):")
                        if issue_info.get('invalid_values'):
                            issue_df = pd.DataFrame(issue_info['invalid_values'])
                            st.dataframe(issue_df, use_container_width=True)
            
            elif check.get('check_type') == 'value_ranges':
                violations = check.get('violations', {})
                
                if violations:
                    st.subheader(f"Violations ({check.get('total_violations', 0)} total)")
                    
                    for column, violation_info in violations.items():
                        if 'error' in violation_info:
                            st.error(f"**{column}**: {violation_info['error']}")
                            continue
                        
                        st.write(f"**{column}**: {violation_info['violation_count']} violations")
                        
                        if violation_info.get('violating_rows'):
                            violation_df = pd.DataFrame(violation_info['violating_rows'])
                            st.dataframe(violation_df, use_container_width=True)
            
            elif check.get('check_type') == 'data_consistency':
                issues = check.get('issues', {})
                
                if issues:
                    st.subheader(f"Consistency Issues ({check.get('total_issues', 0)} total)")
                    
                    for column, column_issues in issues.items():
                        st.write(f"**{column}**:")
                        for issue in column_issues:
                            issue_type = issue.get('type', 'unknown')
                            
                            if issue_type == 'missing_values':
                                st.write(f"  • Missing values: {issue['count']} ({issue['percentage']}%)")
                            elif issue_type == 'mixed_types':
                                st.write(f"  • Mixed data types: {issue['numeric_values']} numeric, {issue['text_values']} text values")
                            elif issue_type == 'constant_values':
                                st.write(f"  • All values are identical: {issue['message']}")
                            else:
                                st.write(f"  • {issue}")
            
            elif check.get('check_type') == 'automatic_quality':
                column_analysis = check.get('column_analysis', {})
                
                if check.get('total_outliers', 0) > 0:
                    st.subheader(f"🎯 Automatic Outlier Detection ({check.get('total_outliers', 0)} outliers found)")
                    
                    for column, analysis in column_analysis.items():
                        outliers = analysis.get('outliers', [])
                        if outliers:
                            inferred_type = analysis.get('inferred_type', 'unknown')
                            confidence = analysis.get('confidence', 0) * 100
                            
                            st.write(f"**{column}** (inferred type: {inferred_type}, confidence: {confidence:.1f}%)")
                            
                            # Show outliers in a table
                            outlier_df = pd.DataFrame(outliers)
                            if not outlier_df.empty:
                                st.dataframe(outlier_df[['row_index', 'value', 'issue']], use_container_width=True)
                else:
                    st.subheader("🎯 Automatic Outlier Detection")
                    st.success("No outliers detected! All data appears consistent with inferred types.")
                    
                    # Show inferred types for each column
                    st.write("**Inferred Column Types:**")
                    for column, analysis in column_analysis.items():
                        inferred_type = analysis.get('inferred_type', 'unknown')
                        confidence = analysis.get('confidence', 0) * 100
                        patterns = analysis.get('type_percentages', {})
                        
                        # Create a simple breakdown
                        pattern_str = ", ".join([f"{k}: {v:.0f}%" for k, v in patterns.items() if v > 0])
                        st.write(f"  • **{column}**: {inferred_type} ({confidence:.1f}% confidence) - {pattern_str}")
    
    # Raw results (for debugging)
    with st.expander("🔧 Raw Results (JSON)", expanded=False):
        st.json(results)
    
    # Download options
    st.header("💾 Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download results as JSON
        results_json = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📄 Download Results (JSON)",
            data=results_json,
            file_name=f"quality_results_{Path(results['file_path']).stem}.json",
            mime="application/json",
            help="Download the complete quality check results as JSON"
        )
    
    with col2:
        # Download formatted summary
        summary_text = format_results_summary(results)
        st.download_button(
            label="📋 Download Summary (TXT)",
            data=summary_text,
            file_name=f"quality_summary_{Path(results['file_path']).stem}.txt",
            mime="text/plain",
            help="Download a formatted summary of the quality check results"
        )


if __name__ == "__main__":
    main()