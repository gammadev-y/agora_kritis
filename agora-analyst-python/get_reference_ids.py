#!/usr/bin/env python3
"""
Script to get actual reference IDs from the database for use in Kritis V3.1.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('/home/gamma/Documents/Agora_Analyst/agora-analyst-python')

from lib.supabase_client import get_supabase_admin_client

load_dotenv()

def get_reference_ids():
    """Get actual reference IDs from the database."""
    print("🔍 Getting reference IDs from database...")
    
    try:
        supabase = get_supabase_admin_client()
        
        # Get government entity ID
        entities = supabase.table('government_entities').select('id').limit(1).execute()
        government_entity_id = entities.data[0]['id'] if entities.data else None
        
        # Get mandate ID
        mandates = supabase.table('mandates').select('id').limit(1).execute()
        mandate_id = mandates.data[0]['id'] if mandates.data else None
        
        print(f"📋 Reference IDs:")
        print(f"   Government Entity ID: {government_entity_id}")
        print(f"   Mandate ID: {mandate_id}")
        print()
        print("🔧 Use these IDs in your Kritis V3.1 analyzer:")
        print(f"   metadata['government_entity_id'] = '{government_entity_id}'")
        print(f"   version_data['mandate_id'] = '{mandate_id}'")
        
        return government_entity_id, mandate_id
        
    except Exception as e:
        print(f"❌ Error getting reference IDs: {e}")
        return None, None

if __name__ == "__main__":
    get_reference_ids()