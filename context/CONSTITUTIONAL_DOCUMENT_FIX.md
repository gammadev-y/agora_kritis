# Constitutional Document Processing Enhancement

**Date**: 2025-10-04  
**Commit**: fc0734a

## Problem Identified

The Kritis V4.0 pipeline was failing to properly process constitutional documents due to:

1. **Missing Title**: Not reading `sources.translations` field which contains the correct title from the crawler
2. **Wrong Official Number**: Generated as `None` instead of `CRP`
3. **Wrong Slug**: Generated as `ttulo-iprincpios-gerais` instead of proper slug based on constitution
4. **Missing Type**: `law_type_id` set to `None` instead of `CONSTITUTION`
5. **Missing Date**: `enactment_date` set to `None` instead of `1976-04-02`

### Example Case

**Source ID**: `d7eaa191-fd7b-48ef-9013-33579398d6ad`

**Source Translations** (correct):
```json
{
  "pt": {
    "title": "Constituição da República Portuguesa - CRP - Título I"
  }
}
```

**Generated Law Record** (incorrect):
- Official Number: `None`
- Official Title: `Título I\n\nPrincípios gerais`
- Slug: `ttulo-iprincpios-gerais`
- Type: `None`
- Enactment Date: `None`

## Root Cause

The metadata extraction process only analyzed document chunks (content) but ignored the `sources.translations` field that contains the page header title captured by the crawler. For constitutional documents, the header contains the full title while chunks only have article content.

## Solution Implemented

### 1. Read Source Translations at Pipeline Start

```python
# Get source record with translations (header data from crawler)
source_response = self.supabase_admin.table('sources').select(
    'id, slug, type_id, translations'
).eq('id', source_id).execute()

source_record = source_response.data[0]
source_translations = source_record.get('translations', {})
source_type_id = source_record.get('type_id')
```

### 2. Enhanced Metadata Extraction

Pass source translations to metadata extraction:

```python
metadata = self._extract_metadata_from_content(
    chunks[0]['content'], 
    source_translations, 
    source_type_id
)
```

### 3. AI Prompt Enhancement

Added context hints to AI prompts:

```python
IMPORTANT CONTEXT FROM SOURCE METADATA:
- The official title from the document header is: "Constituição da República Portuguesa - CRP - Título I"
- This title should be used as the primary reference for official_title_pt
- Use this to determine the correct official_number and law_type_id
- DETECTED: This is a CONSTITUTIONAL document. Set law_type_id to 'CONSTITUTION'
```

### 4. Post-Processing Overrides

Override AI extraction with source translations when more complete:

```python
if source_translations:
    pt_data = source_translations.get('pt', {})
    source_title = pt_data.get('title', '')
    
    # Use source title if more complete
    if source_title and len(source_title) > len(metadata.get('official_title_pt', '')):
        metadata['official_title_pt'] = source_title
        
        # Detect constitutional documents
        if 'constituição' in source_title.lower() or 'crp' in source_title.lower():
            metadata['official_number'] = 'CRP'
            metadata['law_type_id'] = 'CONSTITUTION'
            
            # Set default constitution date if not found
            if not metadata.get('enactment_date'):
                metadata['enactment_date'] = '1976-04-02'
```

### 5. Enhanced Fallback Handling

Use source translations in error fallback:

```python
except (json.JSONDecodeError, ValueError) as e:
    fallback_title = "Documento Legal"
    fallback_type = "DECRETO_LEI"
    
    if source_translations:
        pt_data = source_translations.get('pt', {})
        source_title = pt_data.get('title', '')
        if source_title:
            fallback_title = source_title
            if 'constituição' in source_title.lower():
                fallback_type = 'CONSTITUTION'
```

## Testing Results

### Test Input
- **Source Title**: "Constituição da República Portuguesa - CRP - Título I"
- **Source Type**: "OFFICIAL_PUBLICATION"
- **Content**: "Título I\n\nPrincípios gerais..."

### Test Output
```json
{
  "official_number": "CRP",
  "official_title_pt": "Constituição da República Portuguesa - CRP - Título I",
  "law_type_id": "CONSTITUTION",
  "enactment_date": "1976-04-02"
}
```

✅ **All checks passed!**

## Impact

This enhancement ensures that:

1. **Constitutional documents** are properly identified and classified
2. **Source metadata** from crawlers (page headers) is utilized effectively
3. **Official numbers** are correctly extracted or defaulted for constitutions
4. **Law types** are accurately set to `CONSTITUTION` when applicable
5. **Enactment dates** use reasonable defaults for well-known constitutions
6. **Slugs** are generated from correct official numbers, not chunk content
7. **Backward compatibility** maintained for non-constitutional documents

## Files Modified

- `agora-analyst-python/analysis/kritis_analyzer_v4.py` (+90 lines, -10 lines)
  - Enhanced `run_enhanced_extractor_with_preamble()` to read source translations
  - Updated `_extract_metadata_from_content()` signature to accept translations
  - Added source translations context to AI prompts
  - Implemented post-processing overrides for constitutional documents
  - Enhanced fallback handling with source translations

## Deployment

**Status**: ✅ Deployed to GitHub (commit fc0734a)

The fix is backward-compatible and will automatically apply to all future constitutional document processing. Existing constitutional documents may need to be reprocessed to benefit from the enhanced metadata extraction.
