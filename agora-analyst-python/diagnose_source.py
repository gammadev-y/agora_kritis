"""Diagnostic script to inspect source data for official_number extraction."""
import json
from lib.supabase_client import get_supabase_admin_client

supabase = get_supabase_admin_client()
source_id = '5a60d00d-0b82-4afa-bb1f-4b97fd99fc0f'

# Check source data
print("=" * 80)
print("SOURCE DATA:")
print("=" * 80)
source_response = supabase.table('sources').select('id, type_id, translations, published_at').eq('id', source_id).execute()
if source_response.data:
    source = source_response.data[0]
    print(f"Type ID: {source['type_id']}")
    print(f"Published At: {source['published_at']}")
    print(f"\nTranslations:")
    print(json.dumps(source['translations'], indent=2))

# Check last chunk
print("\n" + "=" * 80)
print("LAST DOCUMENT CHUNK:")
print("=" * 80)
last_chunk_response = supabase.table('document_chunks').select('content, chunk_index').eq('source_id', source_id).order('chunk_index', desc=True).limit(1).execute()
if last_chunk_response.data:
    chunk = last_chunk_response.data[0]
    print(f"Chunk Index: {chunk['chunk_index']}")
    print(f"Content (last 500 chars):\n{chunk['content'][-500:]}")

# Check first chunk
print("\n" + "=" * 80)
print("FIRST DOCUMENT CHUNK:")
print("=" * 80)
first_chunk_response = supabase.table('document_chunks').select('content, chunk_index').eq('source_id', source_id).order('chunk_index').limit(1).execute()
if first_chunk_response.data:
    chunk = first_chunk_response.data[0]
    print(f"Chunk Index: {chunk['chunk_index']}")
    print(f"Content (first 500 chars):\n{chunk['content'][:500]}")

# Check pending extraction metadata
print("\n" + "=" * 80)
print("EXTRACTION METADATA:")
print("=" * 80)
extraction_response = supabase.table('pending_extractions').select('extracted_data').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
if extraction_response.data:
    extracted_data = extraction_response.data[0]['extracted_data']
    metadata = extracted_data.get('metadata', {})
    print(f"Metadata:")
    print(json.dumps(metadata, indent=2))
