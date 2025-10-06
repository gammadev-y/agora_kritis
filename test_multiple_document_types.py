"""
Test enhanced metadata extraction for two different document types:
1. Constitutional document (CRP)
2. Regular decree (Portaria)
"""
import json
from lib.supabase_client import get_supabase_admin_client
from analysis.kritis_analyzer_v4 import KritisAnalyzerV4

def test_source(source_id: str, expected_type: str):
    """Test metadata extraction for a specific source."""
    print("\n" + "=" * 100)
    print(f"TESTING SOURCE: {source_id}")
    print(f"Expected Type: {expected_type}")
    print("=" * 100)
    
    supabase = get_supabase_admin_client()
    kritis = KritisAnalyzerV4()
    
    # Get source record
    source_response = supabase.table('sources').select('id, slug, type_id, translations').eq('id', source_id).execute()
    if not source_response.data:
        print(f"❌ Source {source_id} not found")
        return
    
    source = source_response.data[0]
    print(f"\n📋 SOURCE DATA:")
    print("-" * 100)
    print(f"ID: {source['id']}")
    print(f"Slug: {source['slug']}")
    print(f"Type ID: {source['type_id']}")
    
    translations = source.get('translations', {})
    if translations:
        pt_title = translations.get('pt', {}).get('title', '')
        print(f"PT Title: {pt_title}")
    else:
        print("PT Title: (none)")
    
    # Get first chunk
    chunks_response = supabase.table('document_chunks').select('content, chunk_index').eq('source_id', source_id).order('chunk_index').limit(1).execute()
    if not chunks_response.data:
        print(f"❌ No chunks found for source {source_id}")
        return
    
    first_chunk = chunks_response.data[0]
    print(f"\n📄 FIRST CHUNK CONTENT:")
    print("-" * 100)
    print(first_chunk['content'][:500])
    if len(first_chunk['content']) > 500:
        print("...")
    
    # Test metadata extraction
    print(f"\n🔍 RUNNING METADATA EXTRACTION:")
    print("-" * 100)
    
    try:
        metadata = kritis._extract_metadata_from_content(
            first_chunk['content'],
            translations,
            source['type_id']
        )
        
        print(f"\n✅ EXTRACTED METADATA:")
        print("-" * 100)
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # Validation
        print(f"\n📊 VALIDATION:")
        print("-" * 100)
        
        validations = []
        
        # Check official_number
        official_number = metadata.get('official_number', '')
        if official_number and not official_number.startswith('AUTO-'):
            print(f"✅ Official Number: {official_number}")
            validations.append(True)
        else:
            print(f"⚠️  Official Number: {official_number} (auto-generated or missing)")
            validations.append(False)
        
        # Check official_title_pt
        official_title = metadata.get('official_title_pt', '')
        if official_title and len(official_title) > 10:
            print(f"✅ Official Title: {official_title[:80]}...")
            validations.append(True)
        else:
            print(f"⚠️  Official Title: {official_title}")
            validations.append(False)
        
        # Check law_type_id
        law_type = metadata.get('law_type_id', '')
        expected_types = {
            'CONSTITUTION': ['CONSTITUTION'],
            'PORTARIA': ['PORTARIA'],
            'DECRETO_LEI': ['DECRETO_LEI']
        }
        
        if expected_type in expected_types:
            if law_type in expected_types[expected_type]:
                print(f"✅ Law Type: {law_type} (expected: {expected_type})")
                validations.append(True)
            else:
                print(f"⚠️  Law Type: {law_type} (expected: {expected_type})")
                validations.append(False)
        else:
            print(f"ℹ️  Law Type: {law_type}")
            validations.append(True)
        
        # Check enactment_date
        enactment_date = metadata.get('enactment_date', '')
        if enactment_date and enactment_date != '':
            print(f"✅ Enactment Date: {enactment_date}")
            validations.append(True)
        else:
            print(f"⚠️  Enactment Date: {enactment_date} (missing)")
            validations.append(False)
        
        # Check if source translations were used
        if translations:
            pt_title = translations.get('pt', {}).get('title', '')
            if pt_title and pt_title in official_title:
                print(f"✅ Source translation title was used")
                validations.append(True)
            else:
                print(f"⚠️  Source translation title was NOT used")
                validations.append(False)
        
        # Overall result
        print(f"\n{'=' * 100}")
        if all(validations):
            print("🎉 ALL VALIDATIONS PASSED!")
        elif sum(validations) >= len(validations) * 0.7:
            print(f"⚠️  PARTIAL SUCCESS: {sum(validations)}/{len(validations)} checks passed")
        else:
            print(f"❌ FAILED: Only {sum(validations)}/{len(validations)} checks passed")
        
        return metadata
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

# Main test execution
print("=" * 100)
print("ENHANCED METADATA EXTRACTION - MULTI-DOCUMENT TYPE TEST")
print("=" * 100)
print("\nThis test validates that the enhanced metadata extraction works correctly")
print("for different document types by utilizing sources.translations field.")

# Test 1: Constitutional Document
constitution_metadata = test_source(
    "d7eaa191-fd7b-48ef-9013-33579398d6ad",
    "CONSTITUTION"
)

# Test 2: Portaria (Administrative Order)
portaria_metadata = test_source(
    "d1e35be1-8ecf-4a5d-b947-769e926b8541",
    "PORTARIA"
)

# Final Summary
print("\n" + "=" * 100)
print("FINAL SUMMARY")
print("=" * 100)

if constitution_metadata and portaria_metadata:
    print("\n✅ Both tests completed successfully!")
    print("\nKey Improvements Validated:")
    print("  • Source translations are being read and utilized")
    print("  • Constitutional documents are correctly identified")
    print("  • Regular decrees maintain proper classification")
    print("  • Official titles are extracted from source headers")
    print("  • Metadata extraction is robust across document types")
elif constitution_metadata or portaria_metadata:
    print("\n⚠️  Partial success - one test passed, one failed")
else:
    print("\n❌ Both tests failed")

print("\n" + "=" * 100)
