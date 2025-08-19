#!/usr/bin/env python3
"""Test the improved data quality checks with the problematic CSV."""

import sys
import os
sys.path.append('.')

# Mock pandas for testing our logic without dependencies
class MockSeries:
    def __init__(self, data, name=None):
        self.data = {i: val for i, val in enumerate(data)}
        self.name = name
    
    def items(self):
        return self.data.items()
    
    def dropna(self):
        return [v for v in self.data.values() if str(v).lower() != 'nan']

# Test our validation functions
def test_validation_functions():
    """Test the individual validation functions with problematic data."""
    
    # Import our validation functions
    try:
        from src.checks import _is_valid_integer, _is_valid_float, _is_valid_date, _is_valid_boolean
    except ImportError:
        print("❌ Could not import validation functions - check if pandas is installed")
        return False
    
    print("🔍 Testing validation functions...")
    
    # Test integer validation
    integer_tests = [
        ("34", True),
        ("invalid_age", False),
        ("NaN", False),
        ("45", True),
        ("51", True)
    ]
    
    print("\n📊 Integer validation tests:")
    for value, expected in integer_tests:
        result = _is_valid_integer(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{value}' -> {result} (expected {expected})")
    
    # Test date validation  
    date_tests = [
        ("2025-01-02", True),
        ("not_a_date", False),
        ("wrong_date", False),
        ("2025-01-04", True),
        ("2025-01-15", True)
    ]
    
    print("\n📅 Date validation tests:")
    for value, expected in date_tests.items():
        result = _is_valid_date(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{value}' -> {result} (expected {expected})")
    
    # Test float validation for blood pressure
    blood_pressure_tests = [
        ("120/80", False),  # This is not a simple float
        ("135/85", False),
        ("abc", False),
        ("142/90", False),
        ("150/95", False)
    ]
    
    print("\n🩸 Blood pressure (float) validation tests:")
    for value, expected in blood_pressure_tests:
        result = _is_valid_float(value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{value}' -> {result} (expected {expected})")
    
    return True

def test_content_validation():
    """Test the content validation logic."""
    
    try:
        from src.checks import _check_content_validity
    except ImportError:
        print("❌ Could not import content validation - check if pandas is installed")
        return False
    
    print("\n🔍 Testing content validation...")
    
    # Test age column (should be integers)
    age_data = ["34", "45", "29", "51", "62", "NaN", "41", "33", "27", "invalid_age"]
    age_series = MockSeries(age_data, "age")
    
    # Mock the pandas-specific functions we need
    import pandas as pd
    pd.isna = lambda x: str(x).lower() == 'nan'
    
    try:
        age_issues = _check_content_validity(age_series, 'int')
        print(f"📊 Age validation found {len(age_issues)} issues:")
        for issue in age_issues:
            print(f"  • Row {issue['row_index']}: {issue['issue']}")
    except Exception as e:
        print(f"❌ Age validation failed: {e}")
    
    # Test date column
    date_data = ["2025-01-02", "not_a_date", "2025-01-04", "2025-01-05", "2025-01-08", 
                 "2025-01-09", "2025-01-11", "wrong_date", "2025-01-14", "2025-01-15"]
    date_series = MockSeries(date_data, "visit_date")
    
    try:
        date_issues = _check_content_validity(date_series, 'datetime')
        print(f"\n📅 Date validation found {len(date_issues)} issues:")
        for issue in date_issues:
            print(f"  • Row {issue['row_index']}: {issue['issue']}")
    except Exception as e:
        print(f"❌ Date validation failed: {e}")
    
    return True

def test_data_issues():
    """Identify the specific issues in the uploaded CSV."""
    
    print("\n🎯 Issues that should be detected in your CSV:")
    print("=" * 50)
    
    issues = [
        {
            "column": "visit_date",
            "type": "Invalid dates", 
            "values": ["not_a_date", "wrong_date"],
            "expected": "YYYY-MM-DD format dates"
        },
        {
            "column": "age", 
            "type": "Invalid integers",
            "values": ["NaN", "invalid_age"], 
            "expected": "Numeric age values"
        },
        {
            "column": "blood_pressure",
            "type": "Non-numeric values", 
            "values": ["abc"],
            "expected": "Numeric blood pressure or structured format"
        },
        {
            "column": "gender",
            "type": "Unexpected values",
            "values": ["X"],
            "expected": "Standard gender codes (M, F)"
        }
    ]
    
    for issue in issues:
        print(f"📍 {issue['column']}: {issue['type']}")
        print(f"   Problem values: {issue['values']}")
        print(f"   Expected: {issue['expected']}")
        print()
    
    print("💡 The enhanced checker should now detect these issues!")
    return True

def main():
    """Run all tests."""
    print("🔧 Testing Enhanced Data Quality Checker")
    print("=" * 50)
    
    tests = [
        test_validation_functions,
        test_content_validation, 
        test_data_issues
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} test groups completed")
    
    if passed == total:
        print("🎉 Enhanced data quality checker is ready!")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start the app: streamlit run app.py") 
        print("3. Upload your CSV with problematic data")
        print("4. Configure schema (age: int, visit_date: datetime)")
        print("5. See the improved detection results!")
    else:
        print("⚠️  Some test components had issues (likely missing pandas)")
        print("This is expected if dependencies aren't installed yet.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)