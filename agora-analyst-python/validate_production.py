#!/usr/bin/env python3
"""
Production validation script for Kritis 4.0
Tests all core components and validates the setup.
"""

import os
import sys
import uuid
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment variables and configuration."""
    logger.info("🧪 Testing Environment Configuration")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'SUPABASE_ANON_KEY',
        'GEMINI_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    logger.info("✅ Environment variables configured")
    return True

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("🧪 Testing Module Imports")
    
    try:
        from analysis.kritis_analyzer_v4 import KritisAnalyzerV4
        logger.info("✅ KritisAnalyzerV4 import successful")
        
        import supabase
        logger.info("✅ Supabase import successful")
        
        import google.generativeai as genai
        logger.info("✅ Google GenerativeAI import successful")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_uuid_validation():
    """Test UUID validation function."""
    logger.info("🧪 Testing UUID Validation")
    
    from main import validate_uuid
    
    # Valid UUIDs
    valid_uuids = [
        "f7abfa33-9de5-40c6-9faa-8b9575ef8de8",
        "7fd635ce-1a28-44e3-bf13-85b9b29fa610",
        str(uuid.uuid4())
    ]
    
    # Invalid UUIDs
    invalid_uuids = [
        "not-a-uuid",
        "12345",
        "",
        "f7abfa33-9de5-40c6-9faa-8b9575ef8de8-extra",
        None
    ]
    
    for valid_uuid in valid_uuids:
        if not validate_uuid(valid_uuid):
            logger.error(f"❌ Valid UUID failed validation: {valid_uuid}")
            return False
    
    for invalid_uuid in invalid_uuids:
        if validate_uuid(str(invalid_uuid) if invalid_uuid else ""):
            logger.error(f"❌ Invalid UUID passed validation: {invalid_uuid}")
            return False
    
    logger.info("✅ UUID validation working correctly")
    return True

def test_analyzer_initialization():
    """Test that the analyzer can be initialized."""
    logger.info("🧪 Testing Analyzer Initialization")
    
    try:
        from analysis.kritis_analyzer_v4 import KritisAnalyzerV4
        analyzer = KritisAnalyzerV4()
        logger.info("✅ KritisAnalyzerV4 initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Analyzer initialization failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity."""
    logger.info("🧪 Testing Database Connection")
    
    try:
        from analysis.kritis_analyzer_v4 import KritisAnalyzerV4
        analyzer = KritisAnalyzerV4()
        
        # Test simple query
        response = analyzer.supabase_admin.table('law_categories').select('id').limit(1).execute()
        if response.data:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.warning("⚠️ Database connected but no data returned")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all validation tests."""
    logger.info("🚀 Starting Kritis 4.0 Production Validation")
    
    tests = [
        ("Environment Configuration", test_environment),
        ("Module Imports", test_imports),
        ("UUID Validation", test_uuid_validation),
        ("Analyzer Initialization", test_analyzer_initialization),
        ("Database Connection", test_database_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info("=" * 50)
    logger.info(f"📊 Validation Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All validation tests PASSED! Production ready!")
        sys.exit(0)
    else:
        logger.error("❌ Some validation tests FAILED! Check configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()