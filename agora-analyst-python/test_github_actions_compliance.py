#!/usr/bin/env python3
"""
GitHub Actions Compliance Test Script
Validates that all required files and modules are properly accessible
for GitHub Actions CI/CD pipeline execution.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_module_imports():
    """Test that all critical modules can be imported."""
    print("🧪 Testing Module Imports...")
    
    try:
        # Test lib module imports
        from lib.supabase_client import get_supabase_client, get_supabase_admin_client
        print("✅ lib.supabase_client import successful")
        
        # Test analysis module imports
        from analysis.kritis_analyzer_v40 import KritisAnalyzerV40
        print("✅ analysis.kritis_analyzer_v40 import successful")
        
        from analysis.kritis_analyzer_v31 import KritisAnalyzerV31
        print("✅ analysis.kritis_analyzer_v31 import successful")
        
        # Test main module
        import main
        print("✅ main module import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist and are accessible."""
    print("\n🗂️  Testing File Structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "validate_production.py",
        "lib/__init__.py",
        "lib/supabase_client.py",
        "analysis/__init__.py", 
        "analysis/kritis_analyzer_v40.py",
        "analysis/kritis_analyzer_v31.py",
        ".env.template"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    return len(missing_files) == 0

def test_git_tracking():
    """Test that essential files are tracked by git."""
    print("\n📝 Testing Git Tracking...")
    
    try:
        # Get list of tracked files
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        tracked_files = result.stdout.strip().split('\n')
        
        essential_patterns = [
            'lib/',
            'analysis/',
            'main.py',
            'requirements.txt'
        ]
        
        for pattern in essential_patterns:
            matching_files = [f for f in tracked_files if pattern in f]
            if matching_files:
                print(f"✅ Git tracking {pattern}: {len(matching_files)} files")
            else:
                print(f"❌ Git NOT tracking {pattern}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Git tracking test failed: {e}")
        return False

def test_requirements():
    """Test that requirements.txt is valid."""
    print("\n📦 Testing Requirements...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        essential_packages = [
            'supabase',
            'google-generativeai',
            'python-dotenv',
            'tiktoken'
        ]
        
        found_packages = []
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                package_name = req.split('>=')[0].split('==')[0].split('<')[0].strip()
                found_packages.append(package_name)
        
        for package in essential_packages:
            if any(package in found for found in found_packages):
                print(f"✅ Required package: {package}")
            else:
                print(f"❌ Missing package: {package}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_environment_template():
    """Test that environment template exists and has required variables."""
    print("\n🔧 Testing Environment Template...")
    
    try:
        if not Path('.env.template').exists():
            print("❌ .env.template file missing")
            return False
        
        with open('.env.template', 'r') as f:
            template_content = f.read()
        
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY', 
            'SUPABASE_ANON_KEY',
            'GEMINI_API_KEY'
        ]
        
        for var in required_vars:
            if var in template_content:
                print(f"✅ Environment variable template: {var}")
            else:
                print(f"❌ Missing environment variable: {var}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Environment template test failed: {e}")
        return False

def main():
    """Run all GitHub Actions compliance tests."""
    print("🚀 GitHub Actions Compliance Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_module_imports),
        ("Git Tracking", test_git_tracking),
        ("Requirements", test_requirements),
        ("Environment Template", test_environment_template)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - GitHub Actions ready!")
        return 0
    else:
        print("⚠️  Some tests failed - GitHub Actions may have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())