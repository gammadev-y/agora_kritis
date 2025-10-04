"""Test the enhanced metadata extraction with source translations."""
import json
from analysis.kritis_analyzer_v4 import KritisAnalyzerV4

# Initialize analyzer
kritis = KritisAnalyzerV4()

# Test source translations
source_translations = {
    "pt": {
        "title": "Constituição da República Portuguesa - CRP - Título I",
        "description": ""
    },
    "en": {
        "title": "[EN] Constituição da República Portuguesa - CRP - Título I",
        "description": ""
    }
}

# Test content
test_content = """### Título I

**Princípios gerais**

Artigo 1.º
Igualdade perante a lei

Todos os cidadãos são iguais perante a lei."""

print("=" * 80)
print("TESTING ENHANCED METADATA EXTRACTION")
print("=" * 80)
print(f"\nSource translations title: {source_translations['pt']['title']}")
print(f"Source type: OFFICIAL_PUBLICATION")
print(f"\nContent preview: {test_content[:100]}...")

try:
    metadata = kritis._extract_metadata_from_content(
        test_content, 
        source_translations, 
        "OFFICIAL_PUBLICATION"
    )
    
    print("\n" + "=" * 80)
    print("EXTRACTED METADATA:")
    print("=" * 80)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("=" * 80)
    print(f"✓ Official Number: {metadata.get('official_number')} (expected: CRP)")
    print(f"✓ Official Title: {metadata.get('official_title_pt', '')[:80]}...")
    print(f"✓ Law Type: {metadata.get('law_type_id')} (expected: CONSTITUTION)")
    print(f"✓ Enactment Date: {metadata.get('enactment_date')} (expected: 1976-04-02)")
    
    # Check if all values are correct
    checks = [
        metadata.get('official_number') == 'CRP',
        'Constituição' in metadata.get('official_title_pt', ''),
        metadata.get('law_type_id') == 'CONSTITUTION',
        metadata.get('enactment_date') == '1976-04-02'
    ]
    
    if all(checks):
        print("\n✅ ALL CHECKS PASSED!")
    else:
        print("\n⚠️ Some checks failed:")
        if not checks[0]:
            print("  - Official number is not 'CRP'")
        if not checks[1]:
            print("  - Official title doesn't contain 'Constituição'")
        if not checks[2]:
            print("  - Law type is not 'CONSTITUTION'")
        if not checks[3]:
            print("  - Enactment date is not '1976-04-02'")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
