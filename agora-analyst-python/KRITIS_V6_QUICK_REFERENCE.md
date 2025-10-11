# Kritis V6.0 Quick Reference

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install argostranslate Portuguese→English package
python3 -c "
from argostranslate import package
package.update_package_index()
available = package.get_available_packages()
pt_en = next(filter(lambda x: x.from_code == 'pt' and x.to_code == 'en', available))
package.install_from_path(pt_en.download())
"
```

## Commands

### Complete Pipeline (Recommended)
```bash
python3 main.py --source-id <UUID> v6-complete
```

### Individual Stages
```bash
# Stage 1: Extract preamble and articles
python3 main.py --source-id <UUID> v6-extract

# Stage 2: Analyze in Portuguese (Map phase)
python3 main.py --source-id <UUID> v6-map

# Stage 3: Translate locally and build knowledge graph
python3 main.py --source-id <UUID> v6-build-graph
```

### With Background Job Tracking
```bash
python3 main.py --source-id <UUID> --job-id <JOB_UUID> v6-complete
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     KRITIS V6.0 PIPELINE                      │
└─────────────────────────────────────────────────────────────┘

Stage 1: EXTRACTION
  Input: document_chunks → Output: pending_extractions
  ├─ Extract preamble
  └─ Extract articles with HTML preservation

Stage 2: MAP PHASE (Portuguese-only AI)
  Input: pending_extractions → Output: source_ai_analysis
  ├─ Analyze each article in PT
  ├─ Extract tags (person, organization, concept)
  ├─ Extract cross-references
  └─ Create informal summaries (PT only)
  
  💰 Cost Optimization: Single language analysis

Stage 3: BUILD GRAPH (Local translation + Reduce)
  Input: source_ai_analysis → Output: laws + law_articles
  ├─ Create parent law record
  ├─ For each article:
  │  ├─ Translate PT → EN locally (argos/googletrans)
  │  ├─ Insert law_articles with bilingual translations
  │  └─ Process cross-references
  ├─ Aggregate tags & translate locally
  └─ Token-aware Reduce:
     ├─ Count tokens in article summaries
     ├─ If under limit: single Reduce call
     ├─ If over limit: batch → pre-summarize → final Reduce
     ├─ Translate final summary locally
     └─ Update law with category_id

  💰 Cost Optimization: Free local translation
  🧠 Smart: Token-aware batching for large laws
```

## Key Features

### Cost Optimization
- **50% reduction** in AI analysis costs (PT-only vs bilingual)
- **100% reduction** in translation costs (local vs API)
- Token-aware processing prevents errors

### Quality Improvements
- Enhanced AI persona with strict style guide
- Plain language, no jargon
- Action-oriented summaries
- Few-shot examples in prompts

### Robustness
- Dual translation fallback (argos → googletrans)
- Automatic token management
- Batch pre-summarization for large laws

## Translation Stack

1. **Primary**: argostranslate
   - Offline neural translation
   - Fast and private
   - No API costs

2. **Fallback**: googletrans
   - Online translation
   - More accurate
   - Requires internet

## Token Limits

- Model limit: 1,000,000 tokens
- Safe limit: 800,000 tokens (leaves margin)
- Estimation: ~4 chars per token (Portuguese)
- Batch size: ~50 articles per pre-summary

## Database Schema

### law_articles.translations
```json
{
  "pt": {
    "informal_summary_title": "Título em Português",
    "informal_summary": "Resumo em Português"
  },
  "en": {
    "informal_summary_title": "Title in English",
    "informal_summary": "Summary in English"
  }
}
```

### laws.tags
```json
{
  "pt": {
    "person": ["Nome da Pessoa"],
    "organization": ["Nome da Organização"],
    "concept": ["conceito em português"]
  },
  "en": {
    "person": ["Nome da Pessoa"],
    "organization": ["Nome da Organização"],
    "concept": ["concept in english"]
  }
}
```

## Testing

```bash
# Run test suite
python3 test_v6_implementation.py

# Test specific source
python3 main.py --source-id <UUID> v6-complete

# Check logs
tail -f /var/log/kritis.log
```

## Troubleshooting

### Translation Not Working
```bash
# Check argostranslate installation
python3 -c "import argostranslate; print('OK')"

# Check googletrans installation
python3 -c "import googletrans; print('OK')"

# Reinstall if needed
pip install argostranslate googletrans==4.0.0-rc1
```

### Token Limit Exceeded
- V6 automatically handles this with batching
- Check logs for "batch pre-summarization" messages
- Adjust `safe_token_limit` if needed

### Portuguese Prompt Issues
- Ensure source documents are in Portuguese
- Check model has Portuguese language support
- Verify prompt encoding (UTF-8)

## Performance Metrics

### Expected Performance (per document)
- **Extraction**: ~30 seconds
- **Map Phase**: ~2-5 minutes (depends on article count)
- **Build Graph**: ~1-3 minutes (depends on article count + translation)
- **Total**: ~4-9 minutes

### Cost Comparison (100 articles)
- V5.0: ~$0.50 (bilingual AI analysis + AI translation)
- V6.0: ~$0.25 (PT-only AI analysis + local translation)
- **Savings**: ~50%

## Migration from V5.0

V6.0 is fully compatible with V5.0 database schema:
- Same tables (laws, law_articles, law_relationships)
- Same relationship types
- Same status management
- Enhanced with bilingual support

## Support

- Documentation: KRITIS_V6_IMPLEMENTATION.md
- Specifications: PROD11_v6.md
- Test Suite: test_v6_implementation.py
- Issues: Check logs and error messages
