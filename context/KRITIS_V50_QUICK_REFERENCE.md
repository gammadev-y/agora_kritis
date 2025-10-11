# Kritis V5.0 - Quick Reference Guide

**Version**: 5.0  
**Model**: Gemini 2.0 Flash  
**Last Updated**: October 11, 2025

---

## 🚀 Quick Start

```bash
# Run complete pipeline
python main.py --source-id <uuid> --pipeline v50-complete
```

---

## 📊 Pipeline Overview

```
INPUT → Stage 1: Extract → Stage 2: Analyze → Stage 3: Build Graph → OUTPUT
        (2-5 sec)        (30s - 20min)        (5-30 sec)
```

---

## 🔧 Key Functions by Stage

### Stage 1: Extraction
- **`run_enhanced_extractor_phase()`** - Main entry point
- **`_extract_metadata()`** - Extract type, number, dates
- **`_extract_preamble_and_articles()`** - Split document

### Stage 2: Analysis (Map Phase)
- **`run_enhanced_analyzer_phase()`** - Main entry point
- **`_analyze_with_kritis_v50()`** - Call Gemini AI per article
- Language validation, title duplication detection, copy detection

### Stage 3: Knowledge Graph (Reduce Phase)
- **`run_knowledge_graph_builder_phase()`** - Main entry point
- **`_create_parent_law_v50()`** - Create law record
- **`_process_articles_with_relationships_v50()`** - Create articles + link refs
- **`_aggregate_tags_v50()`** - Aggregate + translate tags + final summary
- **`_generate_comprehensive_law_summary()`** - Create law-level summary

---

## 📝 Output Structure

### laws Table
```json
{
  "id": "uuid",
  "official_number": "CRP",
  "slug": "constituicao-da-republica-portuguesa",
  "official_title": "Constituição da República Portuguesa",
  "url": "https://dre.pt/...",
  "tags": {
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
  },
  "translations": {
    "pt": {
      "informal_summary_title": "Constituição da República Portuguesa",
      "informal_summary": "A Constituição estabelece... [3-5 paragraphs]"
    },
    "en": {
      "informal_summary_title": "Constitution of the Portuguese Republic",
      "informal_summary": "The Constitution establishes... [3-5 paragraphs]"
    }
  }
}
```

### law_articles Table
```json
{
  "id": "uuid",
  "law_id": "uuid",
  "article_order": 1,
  "status_id": "ACTIVE",
  "valid_from": "2024-10-11",
  "valid_to": null,
  "official_text": "Article text with HTML...",
  "tags": {
    "person": ["Name"],
    "organization": ["Organization"],
    "concept": ["concept"]
  },
  "translations": {
    "pt": {
      "informal_summary_title": "Título",
      "informal_summary": "Resumo completo..."
    },
    "en": {
      "informal_summary_title": "Title",
      "informal_summary": "Complete summary..."
    }
  },
  "cross_references": [
    {
      "relationship": "cites",
      "type": "Lei",
      "number": "100/2024",
      "article_number": "5.º",
      "url": "https://..."
    }
  ]
}
```

---

## ⚡ Key Features

### ✅ Portuguese Character Normalization
```
"Constituição" → "constituicao"
"Açores" → "acores"
"São Paulo" → "sao-paulo"
```

### ✅ Multilingual Tags
```json
{
  "pt": ["direitos fundamentais", "soberania"],
  "en": ["fundamental rights", "sovereignty"]
}
```

### ✅ Comprehensive Law Summary
- Aggregates ALL article summaries
- Generates 3-5 paragraph overview
- Covers entire law, not article-by-article

### ✅ Smart Fallbacks
- Invalid translations → Extract from official text
- Title duplication → Auto-remove
- Incomplete summaries → Use more complete text
- Missing English → "Translation pending"

### ✅ Cross-Reference Linking
- Law-to-law relationships
- Article-to-article references
- Temporal consistency validation
- Auto-update status (SUPERSEDED/REVOKED)

---

## 🔍 Validation Checks

### Translation Quality
- ✓ Both PT and EN exist
- ✓ No language mixing
- ✓ Titles present
- ✓ Summaries complete (not "...")
- ✓ No copied text (>85% similarity)
- ✓ No title duplication in summary

### Cross-References
- ✓ Temporal consistency (can't amend future laws)
- ✓ Target law exists in database
- ✓ Target article found (if specified)

---

## 🐛 Error Handling

### Retry Logic
- Max 1 retry on failure
- Deletes incomplete law before retry
- Re-raises error if all attempts fail

### Fallback Logic
- Invalid AI response → Use official text
- Missing target law → Log warning, continue
- Temporal inconsistency → Skip reference, continue

---

## 📈 Performance

### Typical Times
- **Small law** (10 articles): 1-2 minutes total
- **Medium law** (50 articles): 3-6 minutes total
- **Large law** (300 articles): 16-22 minutes total

### Bottlenecks
- Stage 2 (AI analysis): 90% of processing time
- Gemini API: ~1-2 seconds per article

---

## 🔗 Database Tables

### Primary
- `laws` - Parent law records
- `law_articles` - Individual articles
- `law_relationships` - Law-to-law links
- `article_article_references` - Article-to-article links

### Intermediate
- `pending_extractions` - Stage 1 output
- `source_ai_analysis` - Stage 2 output

### Reference
- `law_types` - Static type definitions
- `article_statuses` - ACTIVE, SUPERSEDED, REVOKED

---

## 📚 Documentation Files

1. **KRITIS_V50_COMPLETE_DOCUMENTATION.md** - Full technical documentation
2. **KRITIS_V50_IMPROVEMENTS.md** - Recent improvements and fixes
3. **KRITIS_V50_REGEX_FIX.md** - Regex escape sequence fixes
4. **This file** - Quick reference guide

---

## 🆘 Common Issues

### "Translation pending" in both languages
**Cause**: AI returned invalid or mixed-language response  
**Solution**: Automatic fallback extracts PT from official text

### Title appears twice
**Cause**: AI repeats title in summary  
**Solution**: Auto-detected and removed

### Cross-reference not found
**Cause**: Target law not in database  
**Solution**: Logged as warning, processing continues

### Temporal inconsistency
**Cause**: Date validation failed  
**Solution**: Reference skipped with warning

---

## 🎯 Best Practices

1. **Always run complete pipeline** (`v50-complete`)
2. **Check logs** for validation warnings
3. **Monitor AI costs** (charged per article)
4. **Verify slug uniqueness** before processing similar laws
5. **Review cross-references** for accuracy

---

## 🔮 Future Enhancements

- [ ] Batch AI processing (multiple articles per call)
- [ ] Translation caching for similar content
- [ ] Parallel article processing
- [ ] Quality confidence scores
- [ ] Version tracking for law amendments

---

**Ready to process laws! 🚀**
