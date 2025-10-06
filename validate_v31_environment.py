#!/usr/bin/env python3
"""
Test script to validate the Kritis V3.1 implementation.
"""

import os
import sys
import uuid
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('/home/gamma/Documents/Agora_Analyst/agora-analyst-python')

from lib.supabase_client import get_supabase_admin_client

load_dotenv()

def test_database_connection():
    """Test basic database connectivity."""
    print("🔍 Testing database connection...")
    
    try:
        supabase = get_supabase_admin_client()
        
        # Test basic connection by querying a simple table
        response = supabase.table('law_version_statuses').select('id').limit(1).execute()
        print(f"✅ Database connection successful. Found {len(response.data)} status records.")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_required_tables():
    """Test that all required tables exist."""
    print("🔍 Testing required tables...")
    
    required_tables = [
        'sources',
        'document_chunks', 
        'pending_extractions',
        'source_ai_analysis',
        'laws',
        'law_article_versions',
        'law_version_statuses',
        'mandates',
        'government_entities'
    ]
    
    try:
        supabase = get_supabase_admin_client()
        
        for table in required_tables:
            try:
                response = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Table '{table}' exists")
            except Exception as e:
                print(f"❌ Table '{table}' missing or inaccessible: {e}")
                return False
        
        print("✅ All required tables exist")
        return True
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def test_reference_data():
    """Test that required reference data exists."""
    print("🔍 Testing reference data...")
    
    try:
        supabase = get_supabase_admin_client()
        
        # Check law version statuses
        statuses = supabase.table('law_version_statuses').select('id').execute()
        if 'ACTIVE' not in [s['id'] for s in statuses.data]:
            print("❌ Required status 'ACTIVE' not found")
            return False
        print(f"✅ Found {len(statuses.data)} law version statuses including 'ACTIVE'")
        
        # Check government entities
        entities = supabase.table('government_entities').select('id').limit(1).execute()
        if not entities.data:
            print("⚠️ No government entities found - will need to create test data")
        else:
            print(f"✅ Found {len(entities.data)} government entities")
        
        # Check mandates
        mandates = supabase.table('mandates').select('id').limit(1).execute()
        if not mandates.data:
            print("⚠️ No mandates found - will need to create test data")
        else:
            print(f"✅ Found {len(mandates.data)} mandates")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking reference data: {e}")
        return False

def test_environment_variables():
    """Test that all required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'SUPABASE_ANON_KEY',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Run all validation tests."""
    print("🚀 Kritis V3.1 Environment Validation")
    print("=" * 50)
    
    tests = [
        test_environment_variables,
        test_database_connection,
        test_required_tables,
        test_reference_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Environment is ready for Kritis V3.1!")
        return 0
    else:
        print("⚠️ Some issues found. Please address them before running Kritis V3.1.")
        return 1

if __name__ == "__main__":
    sys.exit(main())