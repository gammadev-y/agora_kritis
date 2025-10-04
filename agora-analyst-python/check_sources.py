#!/usr/bin/env python3
"""
Check existing sources in the database to see if we can test with existing data.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('/home/gamma/Documents/Agora_Analyst/agora-analyst-python')

from lib.supabase_client import get_supabase_admin_client

load_dotenv()

def check_existing_sources():
    """Check for existing sources with document chunks."""
    print("🔍 Checking existing sources...")
    
    try:
        supabase = get_supabase_admin_client()
        
        # Get sources with their chunks
        sources = supabase.table('sources').select('id, slug, translations, type_id').limit(10).execute()
        
        print(f"📊 Found {len(sources.data)} sources:")
        
        for source in sources.data:
            source_id = source['id']
            chunks = supabase.table('document_chunks').select('id').eq('source_id', source_id).execute()
            
            # Extract title from translations if available
            title = "No title"
            if source.get('translations'):
                translations = source['translations']
                if isinstance(translations, dict):
                    title = translations.get('pt', {}).get('title', translations.get('en', {}).get('title', 'No title'))
            
            print(f"   📄 {source.get('slug', 'No slug')}: {title[:50]}")
            print(f"      ID: {source_id}")
            print(f"      Type: {source.get('type_id', 'Unknown')}")
            print(f"      Chunks: {len(chunks.data)}")
            print()
        
        if sources.data:
            print("🎯 You can test Kritis V3.1 with any of these source IDs!")
            print("Example command:")
            print(f"   /home/gamma/Documents/Agora_Analyst/.venv/bin/python main.py v31-complete --source-id {sources.data[0]['id']}")
        
        return sources.data
        
    except Exception as e:
        print(f"❌ Error checking sources: {e}")
        return []

if __name__ == "__main__":
    check_existing_sources()