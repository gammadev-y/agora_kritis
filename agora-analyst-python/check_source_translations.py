"""Check the source translations structure."""
import json
from lib.supabase_client import get_supabase_admin_client

supabase = get_supabase_admin_client()

# Check the specific source that's failing
print("=" * 80)
print("SOURCE RECORD FOR: 5a60d00d-0b82-4afa-bb1f-4b97fd99fc0f")
print("=" * 80)
source_response = supabase.table('sources').select('id, slug, type_id, translations').eq('id', '5a60d00d-0b82-4afa-bb1f-4b97fd99fc0f').execute()
if source_response.data:
    source = source_response.data[0]
    print(f"ID: {source['id']}")
    print(f"Slug: {source['slug']}")
    print(f"Type ID: {source['type_id']}")
    print(f"\nTranslations:")
    print(json.dumps(source['translations'], indent=2))
    
    # Check the structure
    translations = source['translations']
    if 'pt' in translations:
        print(f"\nType of translations['pt']: {type(translations['pt'])}")
        if isinstance(translations['pt'], dict):
            print(f"Keys in translations['pt']: {list(translations['pt'].keys())}")
            if 'title' in translations['pt']:
                print(f"translations['pt']['title']: {translations['pt']['title']}")
        else:
            print(f"translations['pt'] value: {translations['pt']}")
else:
    print("Source not found")
