#!/usr/bin/env python3
"""Basic test to verify project structure and logic without external dependencies."""

import sys
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist."""
    base_dir = Path('.')
    
    required_files = [
        'README.md',
        'requirements.txt',
        'developer_checklist.yaml',
        'app.py',
        'src/__init__.py',
        'src/data_loader.py',
        'src/checks.py',
        'src/quality_pipeline.py',
        'tests/__init__.py',
        'tests/test_data_loader.py',
        'tests/test_checks.py',
        'tests/test_quality_pipeline.py',
        'tests/test_app.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (base_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_python_syntax():
    """Test that all Python files have valid syntax."""
    python_files = [
        'app.py',
        'src/data_loader.py', 
        'src/checks.py',
        'src/quality_pipeline.py',
        'tests/test_data_loader.py',
        'tests/test_checks.py', 
        'tests/test_quality_pipeline.py',
        'tests/test_app.py'
    ]
    
    import ast
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
    
    if syntax_errors:
        print(f"❌ Syntax errors: {syntax_errors}")
        return False
    else:
        print("✅ All Python files have valid syntax")
        return True

def test_requirements_file():
    """Test requirements.txt contains expected dependencies."""
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_deps = ['pandas', 'streamlit', 'pytest']
    missing_deps = []
    
    for dep in required_deps:
        if dep not in content:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"❌ Missing dependencies in requirements.txt: {missing_deps}")
        return False
    else:
        print("✅ All required dependencies listed in requirements.txt")
        return True

def main():
    """Run all basic tests."""
    print("🔍 Running basic project validation tests...")
    print()
    
    tests = [
        test_project_structure,
        test_python_syntax,
        test_requirements_file
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic validation tests passed!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run unit tests: python -m pytest tests/ -v")
        print("3. Start the app: streamlit run app.py")
        return True
    else:
        print("❌ Some validation tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)