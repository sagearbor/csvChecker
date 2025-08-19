#!/usr/bin/env python3
"""Debug the content validation to see why it's not detecting issues."""

# Test the validation functions manually
def test_validation_functions():
    """Test individual validation functions."""
    
    # Test integer validation
    def test_is_valid_integer(value_str: str) -> bool:
        try:
            int(value_str)
            return True
        except ValueError:
            return False
    
    # Test date validation with regex
    import re
    def test_is_valid_date(value_str: str) -> bool:
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value_str):
                try:
                    from datetime import datetime
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                        try:
                            datetime.strptime(value_str, fmt)
                            return True
                        except ValueError:
                            continue
                except ImportError:
                    return True  # Assume valid if datetime not available
        return False
    
    print("Testing individual validation functions:")
    print("=" * 50)
    
    # Test problematic values from the CSV
    test_cases = [
        ("Integer validation", test_is_valid_integer, [
            ("34", True),
            ("invalid_age", False), 
            ("NaN", False),
            ("45", True)
        ]),
        ("Date validation", test_is_valid_date, [
            ("2025-01-02", True),
            ("not_a_date", False),
            ("wrong_date", False),
            ("2025-01-15", True)
        ])
    ]
    
    for test_name, test_func, cases in test_cases:
        print(f"\n{test_name}:")
        for value, expected in cases:
            result = test_func(value)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{value}' -> {result} (expected {expected})")
    
    return True

def test_content_validation_logic():
    """Test the content validation logic with mock data."""
    
    print("\nTesting content validation logic:")
    print("=" * 50)
    
    # Mock the validation function
    def mock_check_content_validity(data_list, expected_type):
        invalid_values = []
        
        for idx, value in enumerate(data_list):
            if str(value).strip().lower() in ['nan', 'null', '']:
                continue  # Skip NaN values
                
            value_str = str(value).strip()
            is_valid = True
            
            if expected_type == 'int':
                try:
                    int(value_str)
                except ValueError:
                    is_valid = False
            elif expected_type == 'datetime':
                # Simple date pattern check
                import re
                date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                is_valid = bool(re.match(date_pattern, value_str))
            
            if not is_valid:
                invalid_values.append({
                    'row_index': idx,
                    'value': value,
                    'issue': f'Invalid {expected_type}: "{value_str}"'
                })
        
        return invalid_values
    
    # Test with data from your CSV
    age_data = ["34", "45", "29", "51", "62", "NaN", "41", "33", "27", "invalid_age"]
    date_data = ["2025-01-02", "not_a_date", "2025-01-04", "2025-01-05", "2025-01-08", 
                 "2025-01-09", "2025-01-11", "wrong_date", "2025-01-14", "2025-01-15"]
    
    print("Age validation (expecting int):")
    age_issues = mock_check_content_validity(age_data, 'int')
    for issue in age_issues:
        print(f"  • Row {issue['row_index']}: {issue['issue']}")
    
    print(f"\nDate validation (expecting datetime):")
    date_issues = mock_check_content_validity(date_data, 'datetime')
    for issue in date_issues:
        print(f"  • Row {issue['row_index']}: {issue['issue']}")
    
    print(f"\nSummary:")
    print(f"  Age issues found: {len(age_issues)}")
    print(f"  Date issues found: {len(date_issues)}")
    
    if len(age_issues) > 0 and len(date_issues) > 0:
        print("✅ Content validation logic is working correctly")
        return True
    else:
        print("❌ Content validation logic has issues")
        return False

def simulate_pipeline_run():
    """Simulate what should happen when your CSV is processed."""
    
    print("\nSimulating pipeline with your CSV data:")
    print("=" * 50)
    
    csv_data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007', 'P008', 'P009', 'P010'],
        'visit_date': ['2025-01-02', 'not_a_date', '2025-01-04', '2025-01-05', '2025-01-08', '2025-01-09', '2025-01-11', 'wrong_date', '2025-01-14', '2025-01-15'],
        'age': [34, 45, 29, 51, 62, 'NaN', 41, 33, 27, 'invalid_age'],
        'gender': ['M', 'F', 'F', 'X', 'M', 'F', 'M', 'F', 'F', 'M'],
        'blood_pressure': ['120/80', '135/85', 'abc', '142/90', '150/95', '125/82', '138/88', '130/85', '127/83', '140/89'],
        'diagnosis': ['Healthy', 'Hypertension', 'Healthy', 'Diabetes', 'Hypertension', 'Healthy', 'Hypertension', 'Healthy', 'Asthma', 'Diabetes']
    }
    
    schema = {
        'participant_id': 'str',
        'visit_date': 'datetime', 
        'age': 'int',
        'gender': 'str',
        'blood_pressure': 'str',
        'diagnosis': 'str'
    }
    
    print("Expected issues to be detected:")
    print("1. visit_date column:")
    print("   - Row 1: 'not_a_date' (invalid datetime)")
    print("   - Row 7: 'wrong_date' (invalid datetime)")
    print("2. age column:")
    print("   - Row 5: 'NaN' (invalid int)")
    print("   - Row 9: 'invalid_age' (invalid int)")
    print("3. Consistency check should flag:")
    print("   - Missing values in various columns")
    print("   - Mixed types in age column (numbers + text)")
    
    return True

def main():
    """Run all debug tests."""
    print("🔧 Debugging Content Validation")
    print("=" * 50)
    
    tests = [
        test_validation_functions,
        test_content_validation_logic,
        simulate_pipeline_run
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Make sure you enable 'Data Type Schema' checkbox in the web interface")
    print("2. Use the pre-filled schema that matches your CSV columns")
    print("3. The enhanced validation should now detect all the issues")
    print("4. If issues persist, check the browser console for JavaScript errors")

if __name__ == "__main__":
    main()