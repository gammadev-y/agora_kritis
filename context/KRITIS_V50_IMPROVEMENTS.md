# Kritis V5.0 Improvements - October 11, 2025

## Issues Fixed

### 1. Slug Generation with Portuguese Characters ✅
**Problem**: Slugs were being created with invalid characters when official titles contained Portuguese accented characters (á, í, à, ç, ã, etc.). Also, UUID suffix was being added unnecessarily.

**Solution**: 
- Added `unicodedata` import
- Modified `_generate_slug()` to normalize accented characters using Unicode NFKD normalization
- **Removed UUID suffix** - slug now uses only the official title
- Increased max length from 100 to 150 characters
- Example: "Constituição da República Portuguesa" → "constituicao-da-republica-portuguesa"

**Code Location**: Lines 16, 743-755

---

### 2. URL Field for Laws Table ✅
**Problem**: The `url` from sources was not being added to laws records

**Solution**:
- Updated sources query to include `main_url` field
- Added `url` field to law_data dictionary when creating law records
- URL is now populated from `sources.main_url`

**Code Location**: Lines 524-526, 577-580

**Note**: Requires `url` column in laws table. If column doesn't exist, the insert will fail gracefully.

---

### 3. Final Summary for laws.translations ✅
**Problem**: The final summary for laws.translations wasn't being filled properly. The reducer wasn't grouping all articles into a comprehensive law-level summary.

**Solution**:
- Completely rewrote `_aggregate_tags_v50()` function
- Added new function `_generate_comprehensive_law_summary()` that:
  - Collects all article summaries (PT and EN)
  - Uses Gemini AI to create a comprehensive law-level summary
  - Generates proper "big picture" overview of entire law (3-5 paragraphs)
- Properly updates laws.translations with comprehensive summary

**Code Location**: Lines 1257-1458

---

### 4. Tags Translation and Multilingual Structure ✅
**Problem**: Tags were only in Portuguese. Need bilingual tags structure with proper English translations.

**Solution**:
- Added new function `_translate_tags_to_english()` that uses Gemini AI to translate Portuguese tags
- Tags now stored in multilingual JSONB structure:
  ```json
  {
    "pt": {
      "person": ["João Silva"],
      "organization": ["Assembleia da República"],
      "concept": ["direitos fundamentais"]
    },
    "en": {
      "person": ["João Silva"],
      "organization": ["Assembly of the Republic"],
      "concept": ["fundamental rights"]
    }
  }
  ```

**Code Location**: Lines 1319-1368

---

### 5. Article Translation Issues ✅
**Problem**: Multiple issues with article translations:
- "[Translation pending]" appearing in both languages
- Both PT and EN fields containing Portuguese text
- Summaries ending with "..." (incomplete)
- Title text being duplicated in the summary

**Solutions**:

#### A. Removed "[Translation pending]" prefix
- Changed fallback to use "Translation pending" as the full EN text instead of prefixing it
- English title: "Translation pending" (not "[Translation pending] Portuguese text")
- English summary: "Translation pending" (not "[Translation pending] Portuguese summary")

**Code Location**: Lines 975-980, 992-996

#### B. Detect title duplication in summary
- Added logic to detect when title text appears at start of summary
- Automatically removes duplicate title from summary
- Cleans up leading punctuation after removal
- Applied to both PT and EN translations

**Code Location**: Lines 393-421

#### C. Detect incomplete summaries ending with "..."
- Added validation check for summaries ending with "..."
- Marks these as invalid translations requiring fallback
- Ensures summaries are more complete in fallback mode

**Code Location**: Lines 947-950

#### D. Better fallback summaries
- Increased fallback summary length from 200 to 300 characters
- Removes title duplication from fallback summaries
- No longer adds "..." to fallback summaries (more complete)

**Code Location**: Lines 957-997

---

## Testing Recommendations

1. **Test Portuguese Characters in Slugs**:
   - Create law with title: "Constituição da República Portuguesa"
   - Verify slug is normalized: "constituicao-da-republica-portuguesa" (no UUID suffix)

2. **Test URL Field**:
   - Create law from source with `main_url`
   - Verify `laws.url` is populated
   - Check database schema has `url` column

3. **Test Comprehensive Law Summary**:
   - Process a law with multiple articles
   - Verify `laws.translations` contains comprehensive summary (not just preamble)
   - Check summary is 3-5 paragraphs covering entire law

4. **Test Multilingual Tags**:
   - Process law with Portuguese tags
   - Verify `laws.tags` has both PT and EN versions
   - Check translations are accurate

5. **Test Article Translation Quality**:
   - Verify no "[Translation pending]" prefixes
   - Check PT and EN have different content (no language mixing)
   - Verify summaries don't end with "..."
   - Verify title text isn't duplicated in summary

---

## Database Schema Note

The code now attempts to populate a `url` field in the `laws` table. If this column doesn't exist in your database schema, you should add it:

```sql
ALTER TABLE agora.laws ADD COLUMN url text;
```

If the column doesn't exist, the insert will fail. You may want to handle this gracefully or ensure the column exists before deploying.

---

## Summary of Changes

- **Files Modified**: 1
  - `/agora-analyst-python/analysis/kritis_analyzer_v50.py`

- **Functions Modified**: 4
  - `_generate_slug()` - Added Unicode normalization
  - `_create_parent_law_v50()` - Added URL field support
  - `_analyze_with_kritis_v50()` - Added title duplication detection
  - `_process_articles_with_relationships_v50()` - Enhanced translation validation

- **Functions Added**: 2
  - `_translate_tags_to_english()` - Translate Portuguese tags to English
  - `_generate_comprehensive_law_summary()` - Create law-level summary from articles

- **Total Lines Changed**: ~250 lines
