# Kritis V5.0 - Complete Documentation & Process Flow

**Last Updated**: October 11, 2025  
**Version**: 5.0  
**Model**: Gemini 2.0 Flash

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Pipeline Stages](#architecture--pipeline-stages)
3. [Stage 1: Enhanced Extractor](#stage-1-enhanced-extractor)
4. [Stage 2: Enhanced Analyzer (Map Phase)](#stage-2-enhanced-analyzer-map-phase)
5. [Stage 3: Knowledge Graph Builder (Reduce Phase)](#stage-3-knowledge-graph-builder-reduce-phase)
6. [AI Prompts & Analysis](#ai-prompts--analysis)
7. [Translation & Fallback Logic](#translation--fallback-logic)
8. [Tags Aggregation & Translation](#tags-aggregation--translation)
9. [Final Law Summary Generation](#final-law-summary-generation)
10. [Cross-Reference Processing](#cross-reference-processing)
11. [Error Handling & Recovery](#error-handling--recovery)
12. [Database Schema & Relations](#database-schema--relations)

---

## Overview

Kritis V5.0 is a three-stage pipeline that processes Portuguese legal documents (laws, decrees, constitutions) and creates a structured knowledge graph with:

- **Multilingual summaries** (PT-PT and EN)
- **Extracted tags** (persons, organizations, concepts) in both languages
- **Cross-references** between laws and articles
- **Relationship mapping** (cites, amends, revokes)
- **Temporal consistency** validation

### Key Improvements in V5.0

1. **Portuguese character normalization** in slugs (á→a, ç→c)
2. **URL field** populated from source
3. **Comprehensive law summary** by aggregating all articles
4. **Multilingual tags** with AI translation PT→EN
5. **Improved fallback logic** for invalid translations
6. **Title duplication detection** and removal from summaries

---

## Architecture & Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│                    KRITIS V5.0 PIPELINE                      │
└─────────────────────────────────────────────────────────────┘

INPUT: source_id (UUID from sources table)
  ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: ENHANCED EXTRACTOR                                  │
│ - Fetch document_chunks                                      │
│ - Extract metadata (type, dates, numbers)                    │
│ - Extract preamble text                                      │
│ - Extract individual articles with official_text            │
│ → Stores in: pending_extractions                            │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: ENHANCED ANALYZER (MAP PHASE)                      │
│ - For each article: Call Gemini AI                          │
│ - Generate: tags, translations (PT/EN), cross-refs          │
│ - Validate translation quality                              │
│ - Detect and fix title duplication                          │
│ → Stores in: source_ai_analysis                             │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: KNOWLEDGE GRAPH BUILDER (REDUCE PHASE)             │
│ Step 1: Create parent law record                            │
│ Step 2: Create law_articles (with immediate linking)        │
│ Step 3: Process cross-references → relationships            │
│ Step 4: Aggregate tags PT → Translate to EN                 │
│ Step 5: Generate comprehensive law summary                  │
│ → Stores in: laws, law_articles, law_relationships,         │
│              article_article_references                      │
└─────────────────────────────────────────────────────────────┘
  ↓
OUTPUT: Complete law knowledge graph with multilingual data
```

---

## Stage 1: Enhanced Extractor

**Function**: `run_enhanced_extractor_phase(source_id: str)`

### Purpose
Extract structured data from raw document chunks stored in the database.

### Process Flow

```python
1. Fetch all document_chunks for source_id (ordered by chunk_index)
   ↓
2. Combine chunks into full_text with "\n\n" separators
   ↓
3. Extract metadata from first chunk
   └─> _extract_metadata(first_chunk_text)
       - Extracts: type, official_number, enactment_date
       - Uses regex patterns for Portuguese legal docs
   ↓
4. Extract preamble and articles
   └─> _extract_preamble_and_articles(full_text)
       - Identifies preamble before first article
       - Splits articles by patterns: "Artigo", "Art.", "Article"
       - Preserves HTML formatting and links
   ↓
5. Store extraction results
   └─> pending_extractions table
       {
         source_id: UUID,
         status: 'COMPLETED',
         extracted_data: {
           preamble_text: string,
           articles: [{article_order, official_text}],
           metadata: {...},
           total_articles: int,
           has_preamble: bool
         }
       }
```

### Key Functions

#### `_extract_metadata(text: str) -> Dict`
Extracts document metadata using regex patterns:

```python
Patterns searched:
- Type: "Lei n.º", "Decreto-Lei", "Constituição"
- Number: r'n\.?º\s*(\d+/\d+)' or r'(\d{8,})'
- Date: r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}'

Returns:
{
  'type': 'Lei' | 'Decreto-Lei' | 'Constituição',
  'official_number': '123/2024',
  'enactment_date': '2024-10-11'
}
```

#### `_extract_preamble_and_articles(text: str) -> Dict`
Splits document into preamble and articles:

```python
Article detection patterns:
- r'(?:^|\n)(?:Artigo|Art\.|Article)\s+(\d+|[IVXLCDM]+)\.?º?'

Process:
1. Find first article position
2. Everything before = preamble
3. Split remaining by article patterns
4. Preserve formatting and HTML

Returns:
{
  'preamble_text': string,
  'articles': [
    {
      'article_order': 1,
      'official_text': 'Article text with HTML...'
    }
  ]
}
```

### Output Schema

Stored in `pending_extractions` table:

```json
{
  "source_id": "uuid",
  "status": "COMPLETED",
  "extracted_data": {
    "preamble_text": "Considering that...",
    "articles": [
      {
        "article_order": 1,
        "official_text": "Article 1\n- Content with <a> links"
      }
    ],
    "metadata": {
      "type": "Lei",
      "official_number": "123/2024",
      "enactment_date": "2024-10-11"
    },
    "total_articles": 50,
    "has_preamble": true,
    "extraction_timestamp": "2024-10-11T15:30:00Z"
  }
}
```

---

## Stage 2: Enhanced Analyzer (Map Phase)

**Function**: `run_enhanced_analyzer_phase(source_id: str)`

### Purpose
Use Gemini AI to analyze each article individually and extract structured information.

### Process Flow

```python
1. Fetch extraction data from pending_extractions
   ↓
2. For PREAMBLE (if exists):
   └─> _analyze_with_kritis_v50(preamble_text, 'preamble')
       - Generate translations and tags
       - Extract cross-references from preamble
   ↓
3. For EACH ARTICLE:
   └─> _analyze_with_kritis_v50(official_text, 'article', article_number)
       - Generate bilingual summaries (PT/EN)
       - Extract tags (person, organization, concept)
       - Identify cross-references with URLs
       - Validate translation quality
       - Fix common issues (title duplication, incomplete text)
   ↓
4. Store all analysis results
   └─> source_ai_analysis table
       {
         source_id: UUID,
         analysis_type: 'v50-enhanced',
         analysis_data: {
           analysis_results: [{
             content_type: 'article' | 'preamble',
             article_order: int,
             analysis: {...}
           }]
         }
       }
```

### AI Analysis Function

#### `_analyze_with_kritis_v50(content, content_type, article_number)`

**Input**: Article official text  
**Output**: Structured JSON with tags, translations, cross-references

**Prompt Structure**:

```
You are analyzing a Portuguese legal document. Provide:

1. LANGUAGE REQUIREMENTS:
   - PT field: Portuguese text only
   - EN field: English text only
   - DO NOT MIX LANGUAGES

2. FORMATTING:
   - Use \n for paragraph separation
   - Plain language, no legal jargon
   - Concise bullet points (-)
   - No intro phrases like "This article is about"

3. CROSS REFERENCES:
   - Extract ALL references to other laws/articles
   - Include: relationship, type, number, article_number, url
   - Internal refs (article number only): url = null
   - External refs: extract href from <a> tags

4. TAGS:
   - Language: pt-PT
   - Categories: person, organization, concept

ARTICLE TEXT:
{content}

OUTPUT JSON:
{
  "tags": {
    "person": ["Nome Próprio"],
    "organization": ["Organização"],
    "concept": ["conceito"]
  },
  "analysis": {
    "pt": {
      "informal_summary_title": "Título em Português",
      "informal_summary": "Resumo completo em Português"
    },
    "en": {
      "informal_summary_title": "Title in English",
      "informal_summary": "Complete summary in English"
    }
  },
  "cross_references": [
    {
      "relationship": "cites",
      "type": "Decreto",
      "number": "19478",
      "article_number": "14.º",
      "url": "https://..."
    }
  ]
}
```

### Validation & Post-Processing

After receiving AI response, the system validates and fixes common issues:

#### **1. Language Detection**
```python
pt_has_portuguese = bool(re.search(r'[àáâãçéêíóôõú]', pt_summary.lower()))
en_has_portuguese = bool(re.search(r'[àáâãçéêíóôõú]', en_summary.lower()))

if not pt_has_portuguese and len(pt_summary) > 50:
    logger.warning("⚠️ PT field appears to be in English!")
if en_has_portuguese and len(en_summary) > 50:
    logger.warning("⚠️ EN field appears to be in Portuguese!")
```

#### **2. Title Duplication Detection**
```python
# Remove markdown formatting
title_clean = re.sub(r'\*\*|\*|_|`', '', pt_title).strip()

# Check if summary starts with title
if title_clean and summary_normalized.startswith(title_clean):
    # Remove title from summary
    pt_summary_fixed = pt_summary[len(title_clean):].strip()
    # Clean leading punctuation
    pt_summary_fixed = re.sub(r'^[\s:;,.\-]+', '', pt_summary_fixed)
    # Update analysis
    analysis['analysis']['pt']['informal_summary'] = pt_summary_fixed
```

#### **3. Copy Detection**
```python
# Normalize for comparison
content_normalized = content.replace('\n\n', ' ').replace('\n', ' ').strip()
summary_normalized = pt_summary.replace('\n\n', ' ').replace('\n', ' ').strip()

# Calculate similarity
similarity = len(set(content_normalized.split()) & set(summary_normalized.split())) / 
             max(len(content_normalized.split()), len(summary_normalized.split()))

if similarity > 0.85:
    logger.warning("⚠️ AI returned copied text instead of summary")
    # Mark as invalid → triggers fallback
```

### Output Schema

Stored in `source_ai_analysis` table:

```json
{
  "source_id": "uuid",
  "analysis_type": "v50-enhanced",
  "model_version": "gemini-2.0-flash",
  "analysis_data": {
    "analysis_results": [
      {
        "content_type": "preamble",
        "article_order": null,
        "analysis": {
          "tags": {...},
          "analysis": {
            "pt": {"informal_summary_title": "...", "informal_summary": "..."},
            "en": {"informal_summary_title": "...", "informal_summary": "..."}
          },
          "cross_references": []
        }
      },
      {
        "content_type": "article",
        "article_order": 1,
        "analysis": {
          "tags": {
            "person": ["António Costa"],
            "organization": ["Assembleia da República"],
            "concept": ["direitos fundamentais"]
          },
          "analysis": {
            "pt": {
              "informal_summary_title": "Soberania Popular",
              "informal_summary": "O poder político pertence ao povo..."
            },
            "en": {
              "informal_summary_title": "Popular Sovereignty",
              "informal_summary": "Political power belongs to the people..."
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
      }
    ]
  }
}
```

---

## Stage 3: Knowledge Graph Builder (Reduce Phase)

**Function**: `run_knowledge_graph_builder_phase(source_id: str)`

### Purpose
Create the final knowledge graph by:
1. Creating parent law record
2. Creating article records with immediate relationship linking
3. Aggregating tags and translating to English
4. Generating comprehensive law-level summary

### Process Flow

```python
1. Check if law already exists for source_id
   └─> If exists: Delete via delete_law_by_law_id()
   
2. Fetch extraction + analysis data
   ├─> pending_extractions
   └─> source_ai_analysis
   
3. CREATE PARENT LAW
   └─> _create_parent_law_v50()
       - Extract official_number (special logic for CRP)
       - Extract official_title from sources.translations.pt
       - Generate normalized slug (Portuguese chars → ASCII)
       - Map law type
       - Add URL from sources.main_url
       → Returns: law_id
   
4. PROCESS ARTICLES WITH RELATIONSHIPS
   └─> _process_articles_with_relationships_v50()
       For each article:
         a) Validate translations (check for invalid data)
         b) Apply fallback if needed
         c) Create law_article record
         d) IMMEDIATELY process cross-references
            └─> _process_and_link_references()
                - Find target laws/articles
                - Create law_relationships
                - Create article_article_references
                - Update article status if revoked/amended
   
5. PROCESS PREAMBLE REFERENCES
   └─> _process_preamble_references()
       - Extract law-to-law relationships from preamble
       - No article-level references
   
6. AGGREGATE TAGS AND GENERATE FINAL SUMMARY
   └─> _aggregate_tags_v50()
       a) Collect all tags from articles (Portuguese)
       b) Translate tags PT → EN using AI
       c) Create multilingual tags structure
       d) Collect all article summaries
       e) Generate comprehensive law summary
       f) Update laws record with:
          - Multilingual tags
          - Comprehensive translations
```

### Key Functions Detail

#### `_create_parent_law_v50(source_id, extraction_data)`

**Purpose**: Create the parent law record

**Process**:

```python
1. Fetch source data
   query = sources.select('translations, published_at, main_url')
   
2. Extract official_title
   └─> From sources.translations.pt.title
   └─> Clean special chars: Remove #$@&*
   └─> Normalize Portuguese: "Constituição" → "constituicao"
   
3. Extract official_number
   └─> _extract_official_number_v50()
       Priority order:
       a) Check if CRP (Constitution) → use "CRP"
       b) Isolated number from last chunk (e.g., "119617986")
       c) Parse from title: "Lei n.º 123/2024"
       d) Fallback: source_id
   
4. Extract enactment_date
   └─> From metadata or fallback to sources.published_at
   
5. Map law type
   └─> _map_law_type()
       - CRP → CONSTITUTION
       - "Lei" → LEI
       - "Decreto-Lei" → DECRETO_LEI
       - etc.
   
6. Generate slug
   └─> _generate_slug(official_title)
       - Normalize: unicodedata.normalize('NFKD', ...)
       - ASCII encode: á→a, ç→c, ã→a
       - Remove non-word chars
       - Replace spaces/hyphens: single hyphen
       - Truncate to 150 chars
       - NO UUID suffix
   
7. Insert law record
   {
     id: UUID,
     source_id: UUID,
     government_entity_id: '3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f', // Portugal
     official_number: 'CRP' | '123/2024',
     slug: 'constituicao-da-republica-portuguesa',
     type_id: 'CONSTITUTION',
     category_id: 'ADMINISTRATIVE',  // Updated later
     enactment_date: '2024-10-11',
     official_title: 'Constituição da República Portuguesa',
     url: 'https://dre.pt/...',  // from sources.main_url
     translations: {},  // Filled by aggregate_tags
     tags: {}  // Filled by aggregate_tags
   }
```

#### `_process_articles_with_relationships_v50(law_id, law_enactment_date, extraction_data, analysis_data)`

**Purpose**: Create article records and link relationships immediately

**Process**:

```python
For each article in analysis_results:
  
  1. Get official_text from extraction_data
  
  2. Validate translations
     └─> Check if valid:
         - translations must have pt and en
         - summaries not empty, not "...", not "[Translation pending]"
         - titles must exist
         - summaries must not end with "..."
     
     └─> If invalid: Apply fallback
         - Extract title from official_text (first 60 chars)
         - Use first 300 chars as summary
         - PT: full text, EN: "Translation pending"
         - Remove title duplication from summary
  
  3. Create law_article record
     {
       id: UUID,
       law_id: UUID,
       article_order: int,
       mandate_id: '50259b5a-054e-4bbf-a39d-637e7d1c1f9f',
       status_id: 'ACTIVE',
       valid_from: law_enactment_date,  // Law's date, not today!
       valid_to: null,
       official_text: string,
       tags: {person: [], organization: [], concept: []},
       translations: {
         pt: {informal_summary_title, informal_summary},
         en: {informal_summary_title, informal_summary}
       },
       cross_references: [{relationship, type, number, article_number, url}]
     }
  
  4. IMMEDIATELY process cross-references
     └─> _process_and_link_references(article_id, law_id, cross_refs)
         For each cross_reference:
           a) Find target law (_find_target_law_v50)
              - Search by URL or official_number
           b) Find target article (_find_target_article_v50)
              - Match by law_id + article text pattern
           c) Create law_relationship (if law-to-law)
              {
                source_law_id: UUID,
                target_law_id: UUID,
                relationship_type: 'cites' | 'amends' | 'revokes'
              }
           d) Create article_article_reference
              {
                source_article_id: UUID,
                target_article_id: UUID,
                relationship_type: 'cites' | 'amends' | 'revokes'
              }
           e) Update target article status if amended/revoked
              └─> _update_article_status()
                  - revokes → status = REVOKED
                  - amends → status = SUPERSEDED
                  - valid_to = day before source law enactment

Returns: {law_relationships: int, article_references: int}
```

#### `_aggregate_tags_v50(law_id, analysis_data)`

**Purpose**: 
1. Aggregate tags from all articles
2. Translate Portuguese tags to English
3. Generate comprehensive law-level summary
4. Update laws record

**Process**:

```python
1. COLLECT TAGS FROM ARTICLES
   query = law_articles.select('tags, translations, article_order')
           .eq('law_id', law_id)
           .order('article_order')
   
   For each article:
     - Aggregate unique tags (PT only) into sets
     - Collect article summaries for final aggregation
   
   Result:
   aggregated_tags_pt = {
     'person': ['João Silva', 'Maria Santos'],
     'organization': ['Assembleia da República', 'Governo'],
     'concept': ['direitos fundamentais', 'soberania']
   }
   
   article_summaries_pt = [
     "Art. 1: O poder político pertence ao povo...",
     "Art. 2: Portugal é uma República...",
     ...
   ]

2. TRANSLATE TAGS TO ENGLISH
   └─> _translate_tags_to_english(aggregated_tags_pt)
       
       Prompt to Gemini:
       "Translate the following Portuguese tags to English. 
        Keep proper names as-is.
        
        Portuguese tags:
        {
          "person": ["João Silva"],
          "organization": ["Assembleia da República"],
          "concept": ["direitos fundamentais"]
        }
        
        Return JSON:
        {
          "person": ["João Silva"],  // Proper names unchanged
          "organization": ["Assembly of the Republic"],
          "concept": ["fundamental rights"]
        }"
   
   Result:
   tags_en = {
     'person': ['João Silva', 'Maria Santos'],
     'organization': ['Assembly of the Republic', 'Government'],
     'concept': ['fundamental rights', 'sovereignty']
   }

3. CREATE MULTILINGUAL TAGS STRUCTURE
   multilingual_tags = {
     'pt': aggregated_tags_pt,
     'en': tags_en
   }

4. EXTRACT PREAMBLE TRANSLATIONS
   For analysis_item in analysis_results:
     if content_type == 'preamble':
       law_translations = analysis_item['analysis']['analysis']
       break

5. GENERATE COMPREHENSIVE LAW SUMMARY
   └─> _generate_comprehensive_law_summary(
         article_summaries_pt,
         article_summaries_en,
         existing_preamble_translations
       )
       
       Prompt to Gemini:
       "You are analyzing a Portuguese law. Below are summaries 
        of all individual articles.
        
        PORTUGUESE ARTICLE SUMMARIES:
        Art. 1: O poder político pertence ao povo...
        Art. 2: Portugal é uma República...
        [... all articles ...]
        
        ENGLISH ARTICLE SUMMARIES:
        Art. 1: Political power belongs to the people...
        Art. 2: Portugal is a Republic...
        [... all articles ...]
        
        Create a comprehensive, high-level summary of the 
        ENTIRE LAW (not article-by-article).
        
        Requirements:
        1. Captures main purpose and scope of the law
        2. Highlights key provisions across all articles
        3. Provides context and practical implications
        4. Written in clear, accessible style
        5. 3-5 paragraphs
        
        Return JSON:
        {
          'pt': {
            'informal_summary_title': 'Título da lei completa',
            'informal_summary': 'Resumo abrangente (3-5 parágrafos)'
          },
          'en': {
            'informal_summary_title': 'Complete law title',
            'informal_summary': 'Comprehensive summary (3-5 paragraphs)'
          }
        }"
       
       Result: Comprehensive law-level translations

6. UPDATE LAWS RECORD
   laws.update({
     tags: multilingual_tags,
     translations: comprehensive_translations
   }).eq('id', law_id)

Final laws.tags structure:
{
  "pt": {
    "person": ["João Silva", "Maria Santos"],
    "organization": ["Assembleia da República", "Governo de Portugal"],
    "concept": ["direitos fundamentais", "soberania popular"]
  },
  "en": {
    "person": ["João Silva", "Maria Santos"],
    "organization": ["Assembly of the Republic", "Government of Portugal"],
    "concept": ["fundamental rights", "popular sovereignty"]
  }
}

Final laws.translations structure:
{
  "pt": {
    "informal_summary_title": "Constituição da República Portuguesa",
    "informal_summary": "A Constituição estabelece os princípios fundamentais 
                         do Estado português... [3-5 paragraphs covering entire law]"
  },
  "en": {
    "informal_summary_title": "Constitution of the Portuguese Republic",
    "informal_summary": "The Constitution establishes the fundamental principles 
                         of the Portuguese State... [3-5 paragraphs covering entire law]"
  }
}
```

---

## Translation & Fallback Logic

### Valid Translation Criteria

A translation is considered **VALID** if ALL of the following are true:

```python
✓ translations.pt exists and is not empty
✓ translations.en exists and is not empty
✓ pt.informal_summary is not "", "...", or "Translation pending"
✓ en.informal_summary is not "", "...", or "Translation pending"
✓ pt.informal_summary_title exists and is not empty
✓ en.informal_summary_title exists and is not empty
✓ pt.informal_summary does NOT end with "..."
✓ en.informal_summary does NOT end with "..."
```

### Invalid Translation Detection

```python
is_invalid_translation = False

if not translations or (not translations.get('pt') and not translations.get('en')):
    is_invalid_translation = True
else:
    pt_summary = (pt_dict.get('informal_summary') or '').strip()
    en_summary = (en_dict.get('informal_summary') or '').strip()
    pt_title = (pt_dict.get('informal_summary_title') or '').strip()
    en_title = (en_dict.get('informal_summary_title') or '').strip()
    
    # Check for invalid summaries
    if pt_summary in ['', '...'] or en_summary in ['', '...']:
        is_invalid_translation = True
    # Check for missing titles
    elif not pt_title or not en_title:
        is_invalid_translation = True
    # Check for incomplete summaries
    elif pt_summary.endswith('...') or en_summary.endswith('...'):
        is_invalid_translation = True
```

### Fallback Logic

When translation is invalid, the system applies intelligent fallbacks:

```python
if is_invalid_translation:
    # 1. Create PT summary from official text
    fallback_summary_pt = official_text[:300].rstrip()
    # Don't add "..." to make it look complete
    
    # 2. Extract title from official text
    fallback_title_pt = "Sem título"
    fallback_title_en = "Untitled"
    
    # Look for text in parentheses as title
    title_match = re.search(r'\*\*\((.*?)\)\*\*', official_text)
    if title_match:
        fallback_title_pt = title_match.group(1)
    else:
        # Extract from content
        text_clean = re.sub(r'^[-–]\s*', '', official_text)  # Remove leading dash
        text_clean = re.sub(r'^\d+\s*[-–]\s*', '', text_clean)  # Remove "1 - "
        
        first_line = text_clean.split('\n')[0]
        first_sentence = re.split(r'[,\.]', first_line)[0].strip()
        
        if first_sentence:
            fallback_title_pt = first_sentence[:60].rstrip()
            if len(first_sentence) > 60:
                fallback_title_pt += '...'
    
    # 3. Remove title duplication from summary
    fallback_summary_clean = fallback_summary_pt
    if fallback_title_pt != "Sem título":
        title_clean = fallback_title_pt.replace('...', '').strip()
        if fallback_summary_pt.startswith(title_clean):
            remaining = fallback_summary_pt[len(title_clean):].strip()
            if remaining:
                fallback_summary_clean = remaining
    
    # 4. Create fallback translations structure
    translations = {
        'pt': {
            'informal_summary_title': fallback_title_pt,
            'informal_summary': fallback_summary_clean
        },
        'en': {
            'informal_summary_title': 'Translation pending',
            'informal_summary': 'Translation pending'
        }
    }
```

### Post-AI Validation & Fixes

Even when AI returns valid JSON, additional validation catches common issues:

#### **Title Duplication Fix**

```python
# Problem: AI sometimes repeats the title at the start of the summary
# Example:
#   title: "Soberania Popular"
#   summary: "**Soberania Popular**\n\nO poder político pertence..."

# Solution:
pt_title = pt_data.get('informal_summary_title', '')
pt_summary = pt_data.get('informal_summary', '')

# Remove markdown formatting from title
title_clean = re.sub(r'\*\*|\*|_|`', '', pt_title).strip()

# Check if summary starts with title
if title_clean and pt_summary.startswith(title_clean):
    # Remove title from summary
    pt_summary_fixed = pt_summary[len(title_clean):].strip()
    # Clean leading punctuation
    pt_summary_fixed = re.sub(r'^[\s:;,.\-]+', '', pt_summary_fixed)
    
    if pt_summary_fixed:
        logger.info("🔧 Removed duplicate title text from PT summary")
        analysis['analysis']['pt']['informal_summary'] = pt_summary_fixed
```

---

## Tags Aggregation & Translation

### Collection Phase

Tags are collected from ALL articles in Portuguese (pt-PT):

```python
aggregated_tags_pt = {
    'person': [],
    'organization': [],
    'concept': []
}

unique_tags_pt = {
    'person': set(),
    'organization': set(),
    'concept': set()
}

for article in law_articles:
    if article.get('tags'):
        tags = article['tags']
        for category in ['person', 'organization', 'concept']:
            if category in tags:
                for tag in tags[category]:
                    if tag and tag not in unique_tags_pt[category]:
                        unique_tags_pt[category].add(tag)
                        aggregated_tags_pt[category].append(tag)
```

### Translation Phase

Portuguese tags are translated to English using Gemini AI:

```python
def _translate_tags_to_english(tags_pt):
    prompt = f"""Translate the following Portuguese tags to English. 
Keep proper names as-is.

Return ONLY a JSON object:

{{
    "person": ["English translation"],
    "organization": ["English translation"],
    "concept": ["English translation"]
}}

Portuguese tags to translate:
{json.dumps(tags_pt, ensure_ascii=False, indent=2)}
"""
    
    response = self.model.generate_content(prompt)
    tags_en = json.loads(response.text)
    return tags_en
```

**Example Translation**:

```json
Input (PT):
{
  "person": ["João Silva", "Maria Santos"],
  "organization": ["Assembleia da República", "Governo de Portugal"],
  "concept": ["direitos fundamentais", "soberania popular", "estado de direito"]
}

Output (EN):
{
  "person": ["João Silva", "Maria Santos"],  // Names preserved
  "organization": ["Assembly of the Republic", "Government of Portugal"],
  "concept": ["fundamental rights", "popular sovereignty", "rule of law"]
}
```

### Final Structure

Tags are stored in `laws.tags` as multilingual JSONB:

```json
{
  "pt": {
    "person": ["António Costa", "Marcelo Rebelo de Sousa"],
    "organization": ["Assembleia da República", "Tribunal Constitucional"],
    "concept": ["direitos fundamentais", "separação de poderes"]
  },
  "en": {
    "person": ["António Costa", "Marcelo Rebelo de Sousa"],
    "organization": ["Assembly of the Republic", "Constitutional Court"],
    "concept": ["fundamental rights", "separation of powers"]
  }
}
```

---

## Final Law Summary Generation

### Purpose

Create a **comprehensive, high-level summary** of the entire law by aggregating all article summaries. This is NOT a simple concatenation but a thoughtful synthesis.

### Collection Phase

```python
article_summaries_pt = []
article_summaries_en = []

for article in law_articles (ordered by article_order):
    if article.translations:
        pt_summary = article.translations.pt.informal_summary
        en_summary = article.translations.en.informal_summary
        
        if pt_summary and pt_summary != 'Translation pending':
            article_summaries_pt.append(f"Art. {article_order}: {pt_summary}")
        
        if en_summary and en_summary != 'Translation pending':
            article_summaries_en.append(f"Art. {article_order}: {en_summary}")
```

### Synthesis Phase

```python
def _generate_comprehensive_law_summary(article_summaries_pt, article_summaries_en, existing_translations):
    """Generate law-level summary by aggregating article summaries."""
    
    combined_pt = "\n".join(article_summaries_pt)
    combined_en = "\n".join(article_summaries_en)
    
    # Skip if insufficient content
    if len(combined_pt) < 100 and len(combined_en) < 100:
        return existing_translations or {}
    
    prompt = f"""You are analyzing a Portuguese law. Below are summaries of all individual articles.

Your task: Create a comprehensive, high-level summary of the ENTIRE LAW (not individual articles).

**PORTUGUESE ARTICLE SUMMARIES:**
{combined_pt}

**ENGLISH ARTICLE SUMMARIES:**
{combined_en}

Create a comprehensive summary that:
1. Captures the main purpose and scope of the law
2. Highlights key provisions across all articles
3. Provides context and practical implications
4. Is written in a clear, accessible style (not article-by-article)
5. 3-5 paragraphs covering the entire law

Return ONLY a JSON object:

{{
    "pt": {{
        "informal_summary_title": "Título descritivo da lei completa em português",
        "informal_summary": "Resumo abrangente e completo da lei inteira em português (3-5 parágrafos)"
    }},
    "en": {{
        "informal_summary_title": "Descriptive title of the complete law in English",
        "informal_summary": "Comprehensive summary of the entire law in English (3-5 paragraphs)"
    }}
}}
"""
    
    response = self.model.generate_content(prompt)
    comprehensive = json.loads(response.text)
    
    if comprehensive.get('pt') and comprehensive.get('en'):
        return comprehensive
    else:
        return existing_translations or {}
```

### Example Output

**Input**: 50 article summaries covering constitutional principles

**Output**:

```json
{
  "pt": {
    "informal_summary_title": "Constituição da República Portuguesa",
    "informal_summary": "A Constituição Portuguesa, aprovada em 1976, estabelece os fundamentos do Estado democrático português. Define a República como um Estado de direito democrático, baseado na soberania popular e nos direitos fundamentais.\n\nO documento organiza-se em quatro partes principais: princípios fundamentais, direitos e deveres, organização económica, e organização do poder político. Garante direitos civis, políticos, económicos, sociais e culturais a todos os cidadãos, com especial atenção à dignidade humana e igualdade.\n\nEm termos de organização política, estabelece a separação de poderes entre Presidente da República, Assembleia da República, Governo e Tribunais. Define mecanismos de fiscalização constitucional e procedimentos de revisão. A Constituição também prevê o estatuto especial das regiões autónomas dos Açores e Madeira, garantindo-lhes autonomia política e administrativa."
  },
  "en": {
    "informal_summary_title": "Constitution of the Portuguese Republic",
    "informal_summary": "The Portuguese Constitution, approved in 1976, establishes the foundations of the Portuguese democratic state. It defines the Republic as a democratic rule of law, based on popular sovereignty and fundamental rights.\n\nThe document is organized into four main parts: fundamental principles, rights and duties, economic organization, and political power organization. It guarantees civil, political, economic, social and cultural rights to all citizens, with special attention to human dignity and equality.\n\nIn terms of political organization, it establishes the separation of powers between the President of the Republic, Assembly of the Republic, Government and Courts. It defines mechanisms for constitutional review and amendment procedures. The Constitution also provides for the special status of the autonomous regions of the Azores and Madeira, guaranteeing them political and administrative autonomy."
  }
}
```

### Integration

The comprehensive summary is stored in `laws.translations`, replacing or merging with preamble translations:

```python
# Priority: Comprehensive summary > Preamble translations > Empty
if comprehensive_summary and comprehensive_summary.get('pt') and comprehensive_summary.get('en'):
    law_translations = comprehensive_summary
elif preamble_translations:
    law_translations = preamble_translations
else:
    law_translations = {}

# Update laws record
laws.update({
    translations: law_translations
}).eq('id', law_id)
```

---

## Cross-Reference Processing

### Types of References

Kritis V5.0 handles multiple types of cross-references:

1. **Law-to-Law** (stored in `law_relationships`)
   - Source law references target law
   - Example: "Lei 100/2024 revoga a Lei 50/2020"

2. **Article-to-Article** (stored in `article_article_references`)
   - Specific article references specific article
   - Example: "Artigo 10 altera o artigo 5.º do Decreto-Lei 123/2024"

3. **Internal References**
   - References within the same law
   - Example: "nos termos do n.º 2 do artigo anterior"
   - url = null

4. **External References**
   - References to other laws with URL
   - Example: Link to DiarioRepublica.pt
   - url = extracted href

### Relationship Types

```python
RELATIONSHIP_TYPES = [
    'cites',              # General reference
    'amends',             # Modifies/updates
    'revokes',            # Cancels/repeals
    'implements',         # Implements provisions
    'references_internal' # Internal reference (same law)
]
```

### Processing Flow

#### `_process_and_link_references(article_id, law_id, law_enactment_date, cross_references)`

```python
For each cross_reference in article's cross_references:
    
    1. FIND TARGET LAW
       └─> _find_target_law_v50(url, official_number)
           - Search by URL if present
           - Search by official_number as fallback
           - Returns: {id, enactment_date} or None
    
    2. IF TARGET LAW NOT FOUND:
       └─> Skip (log warning)
    
    3. FIND TARGET ARTICLE (if article_number specified)
       └─> _find_target_article_v50(target_law_id, article_number)
           - Match by article number pattern
           - Example: "5.º", "Art. 10", "Article 3"
           - Returns: article_id or None
    
    4. VALIDATE TEMPORAL CONSISTENCY
       └─> For 'amends' and 'revokes':
           Check: source_enactment_date > target_enactment_date
           Reason: Can't amend/revoke future laws
           If invalid: Skip with warning
    
    5. CREATE LAW RELATIONSHIP (if law-to-law)
       INSERT INTO law_relationships:
       {
         source_law_id: article's law_id,
         target_law_id: found target_law_id,
         relationship_type: 'cites' | 'amends' | 'revokes'
       }
       Note: Use upsert (on conflict do nothing)
    
    6. CREATE ARTICLE REFERENCE (if article-to-article)
       INSERT INTO article_article_references:
       {
         source_article_id: article_id,
         target_article_id: found target_article_id,
         target_law_id: target_law_id,
         relationship_type: 'cites' | 'amends' | 'revokes',
         context_text: snippet from official_text (optional)
       }
    
    7. UPDATE TARGET ARTICLE STATUS (if amends/revokes)
       └─> _update_article_status(target_article_id, relationship, source_enactment_date)
           If relationship == 'revokes':
             - status_id = 'REVOKED'
             - valid_to = day before source law enactment
           If relationship == 'amends':
             - status_id = 'SUPERSEDED'
             - valid_to = day before source law enactment

Returns: {
    law_relationships: count,
    article_references: count
}
```

### Target Finding Logic

#### Finding Target Law

```python
def _find_target_law_v50(url, official_number):
    """Find target law by URL or official_number."""
    
    # Priority 1: Search by URL
    if url:
        # Extract law identifier from URL
        # Example: https://dre.pt/.../decreto-lei/123-2024-...
        url_patterns = [
            r'/(\d+)-(\d{4})',  # "123-2024"
            r'n[º°]?\s*(\d+/\d{4})'  # "n.º 123/2024"
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url)
            if match:
                # Try to find law with this pattern
                result = laws.select('id, enactment_date')
                              .ilike('official_number', f'%{match.group(0)}%')
                              .execute()
                if result.data:
                    return result.data[0]
    
    # Priority 2: Search by official_number
    if official_number:
        result = laws.select('id, enactment_date')
                     .eq('official_number', official_number)
                     .execute()
        if result.data:
            return result.data[0]
    
    return None
```

#### Finding Target Article

```python
def _find_target_article_v50(target_law_id, article_number):
    """Find specific article within target law."""
    
    if not article_number:
        return None
    
    # Normalize article number
    # Examples: "5.º", "Art. 10", "Artigo 3", "Article 5"
    article_patterns = [
        rf'(?:Artigo|Art\.|Article)\s+{re.escape(article_number)}',
        rf'^{re.escape(article_number)}\s*[-–]',  # Start of text
        rf'\b{re.escape(article_number)}\b'  # Word boundary
    ]
    
    # Get all articles from target law
    articles = law_articles.select('id, official_text')
                           .eq('law_id', target_law_id)
                           .execute()
    
    for article in articles.data:
        official_text = article['official_text']
        for pattern in article_patterns:
            if re.search(pattern, official_text, re.IGNORECASE):
                return article['id']
    
    return None
```

### Temporal Consistency Validation

```python
def _validate_temporal_consistency(relationship, source_date, target_date):
    """Ensure laws can only amend/revoke earlier laws."""
    
    if relationship not in ['amends', 'revokes']:
        return True  # No validation needed for 'cites'
    
    if not source_date or not target_date:
        return True  # Can't validate without dates
    
    # Source law must be enacted AFTER target law
    if source_date <= target_date:
        logger.warning(
            f"⚠️ Temporal inconsistency: {relationship} requires "
            f"source_date ({source_date}) > target_date ({target_date})"
        )
        return False
    
    return True
```

### Status Update Logic

```python
def _update_article_status(target_article_id, relationship, source_enactment_date):
    """Update target article status when superseded or revoked."""
    
    # Determine new status
    if relationship == 'revokes':
        new_status = 'REVOKED'
    elif relationship == 'amends':
        new_status = 'SUPERSEDED'
    else:
        return  # No status change needed
    
    # Calculate valid_to (day before source enactment)
    enactment = datetime.fromisoformat(source_enactment_date).date()
    valid_to = (enactment - timedelta(days=1)).isoformat()
    
    # Update article
    law_articles.update({
        'status_id': new_status,
        'valid_to': valid_to
    }).eq('id', target_article_id).execute()
    
    logger.info(f"📝 Updated article {target_article_id} to {new_status}, valid_to: {valid_to}")
```

---

## Error Handling & Recovery

### Retry Logic

Knowledge graph building has built-in retry logic:

```python
max_retries = 1
retry_count = 0

while retry_count <= max_retries:
    try:
        # Process articles and aggregate tags
        relationships = _process_articles_with_relationships_v50(...)
        _aggregate_tags_v50(...)
        break  # Success
        
    except Exception as e:
        retry_count += 1
        logger.error(f"❌ Error (attempt {retry_count}/{max_retries + 1}): {e}")
        
        if retry_count <= max_retries:
            # Delete law and retry
            logger.info(f"🔄 Deleting law {law_id} and retrying...")
            supabase_admin.rpc('delete_law_by_law_id', {'p_law_id': law_id}).execute()
        else:
            # Final failure - re-raise
            raise e
```

### Transaction Safety

The pipeline uses a **delete-before-create** pattern:

```python
# STEP 0: Check if law already exists
existing_law = laws.select('id').eq('source_id', source_id).execute()

if existing_law.data:
    existing_law_id = existing_law.data[0]['id']
    logger.warning(f"⚠️ Law already exists. Deleting...")
    
    # Use RPC function for safe cascading delete
    supabase_admin.rpc('delete_law_by_law_id', {'p_law_id': existing_law_id}).execute()
    
    logger.info(f"🗑️ Deleted existing law {existing_law_id}")

# Now safe to create new law
law_id = _create_parent_law_v50(...)
```

### Validation at Each Stage

**Stage 1 Validation**:
```python
if not chunks_response.data:
    raise ValueError(f"No document chunks found for source {source_id}")

if not extraction_result["articles"]:
    logger.warning("⚠️ No articles extracted from document")
```

**Stage 2 Validation**:
```python
if not extraction_data or not analysis_data:
    raise ValueError(f"Missing extraction or analysis data for source {source_id}")

# Language detection
pt_has_portuguese = bool(re.search(r'[àáâãçéêíóôõú]', pt_summary.lower()))
if not pt_has_portuguese:
    logger.warning("⚠️ PT field appears to be in English!")
```

**Stage 3 Validation**:
```python
# Temporal consistency
if source_date <= target_date:
    logger.warning("⚠️ Temporal inconsistency detected")
    continue  # Skip this reference

# Target not found
if not target_law:
    logger.warning(f"⚠️ Target law not found for reference")
    continue
```

---

## Database Schema & Relations

### Core Tables

#### `laws`
```sql
CREATE TABLE agora.laws (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  official_number text UNIQUE,
  slug text NOT NULL UNIQUE,
  type_id text,
  category_id text,
  enactment_date date,
  official_title text NOT NULL,
  url text,  -- NEW: Source URL
  translations jsonb,  -- {pt: {title, summary}, en: {title, summary}}
  source_id uuid UNIQUE,
  tags jsonb,  -- {pt: {person, org, concept}, en: {person, org, concept}}
  FOREIGN KEY (government_entity_id) REFERENCES government_entities(id),
  FOREIGN KEY (type_id) REFERENCES law_types(id),
  FOREIGN KEY (category_id) REFERENCES law_categories(id),
  FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

#### `law_articles`
```sql
CREATE TABLE agora.law_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  law_id uuid NOT NULL,
  article_order integer NOT NULL,
  mandate_id uuid NOT NULL,
  status_id text NOT NULL DEFAULT 'ACTIVE',
  valid_from date,
  valid_to date,
  official_text text NOT NULL,
  tags jsonb,  -- {person: [], organization: [], concept: []}
  translations jsonb,  -- {pt: {title, summary}, en: {title, summary}}
  cross_references jsonb,  -- [{relationship, type, number, article_number, url}]
  FOREIGN KEY (law_id) REFERENCES laws(id) ON DELETE CASCADE,
  FOREIGN KEY (mandate_id) REFERENCES mandates(id),
  FOREIGN KEY (status_id) REFERENCES article_statuses(id),
  UNIQUE (law_id, article_order)
);
```

#### `law_relationships`
```sql
CREATE TABLE agora.law_relationships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_law_id uuid NOT NULL,
  target_law_id uuid NOT NULL,
  relationship_type text NOT NULL,
  created_at timestamp DEFAULT now(),
  FOREIGN KEY (source_law_id) REFERENCES laws(id) ON DELETE CASCADE,
  FOREIGN KEY (target_law_id) REFERENCES laws(id) ON DELETE CASCADE,
  UNIQUE (source_law_id, target_law_id, relationship_type)
);
```

#### `article_article_references`
```sql
CREATE TABLE agora.article_article_references (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_article_id uuid NOT NULL,
  target_article_id uuid NOT NULL,
  target_law_id uuid NOT NULL,
  relationship_type text NOT NULL,
  context_text text,
  created_at timestamp DEFAULT now(),
  FOREIGN KEY (source_article_id) REFERENCES law_articles(id) ON DELETE CASCADE,
  FOREIGN KEY (target_article_id) REFERENCES law_articles(id) ON DELETE CASCADE,
  FOREIGN KEY (target_law_id) REFERENCES laws(id) ON DELETE CASCADE,
  UNIQUE (source_article_id, target_article_id, relationship_type)
);
```

### Intermediate Tables

#### `pending_extractions`
```sql
CREATE TABLE agora.pending_extractions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL UNIQUE,
  status text NOT NULL,
  extracted_data jsonb NOT NULL,
  created_at timestamp DEFAULT now(),
  FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

#### `source_ai_analysis`
```sql
CREATE TABLE agora.source_ai_analysis (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  analysis_type text NOT NULL,
  model_version text,
  analysis_data jsonb NOT NULL,
  created_at timestamp DEFAULT now(),
  FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

### Reference Data

#### `law_types`
```sql
-- Static reference data
DECRETO_LEI, LEI, LEI_CONSTITUCIONAL, LEI_ORGANICA, DECRETO, 
CONSTITUTION, OTHER, etc.
```

#### `article_statuses`
```sql
-- Static reference data
ACTIVE, SUPERSEDED, REVOKED, SUSPENDED
```

---

## Complete Example Run

### Input
```
source_id: "28619175-a2da-4bac-a03e-9de790c458f5"
Document: Constituição da República Portuguesa (296 articles)
```

### Stage 1: Extraction
```
✅ Extracted:
   - Preamble: "A Assembleia Constituinte reunida..."
   - 296 articles with HTML preserved
   - Metadata: {type: "Constituição", number: "CRP", date: "1976-04-02"}
```

### Stage 2: Analysis (Map)
```
Processing 296 articles + 1 preamble = 297 AI calls

Article 1:
  Input: "Artigo 1.º\n(República Portuguesa)\nPortugal é uma República..."
  Output: {
    tags: {person: [], organization: ["República Portuguesa"], concept: ["soberania"]},
    analysis: {
      pt: {title: "República Portuguesa", summary: "Portugal é uma República..."},
      en: {title: "Portuguese Republic", summary: "Portugal is a Republic..."}
    },
    cross_references: []
  }

[... 295 more articles ...]

✅ All 297 items analyzed and stored
```

### Stage 3: Knowledge Graph (Reduce)
```
Step 1: Create law
  ✅ law_id: "abc-123-..."
  ✅ slug: "constituicao-da-republica-portuguesa"
  ✅ official_number: "CRP"
  ✅ url: "https://dre.pt/..."

Step 2: Create 296 articles
  ✅ All articles inserted with translations
  ✅ Cross-references processed: 150 law relationships, 320 article references
  ✅ 12 articles marked as SUPERSEDED/REVOKED

Step 3: Aggregate tags
  ✅ Collected 45 unique tags in Portuguese
  ✅ Translated to English
  ✅ Stored multilingual structure

Step 4: Generate comprehensive summary
  ✅ Combined 296 article summaries
  ✅ Generated 5-paragraph law overview (PT and EN)
  ✅ Updated laws.translations

Final output:
  - 1 law record
  - 296 article records
  - 150 law-to-law relationships
  - 320 article-to-article references
  - Multilingual tags and summaries
```

---

## Performance Metrics

### Typical Processing Times

- **Stage 1 (Extraction)**: 2-5 seconds
- **Stage 2 (Analysis)**: 
  - Small law (10 articles): 30-60 seconds
  - Medium law (50 articles): 2-5 minutes
  - Large law (300 articles): 15-20 minutes
- **Stage 3 (Knowledge Graph)**: 5-30 seconds

### API Calls

- **Gemini AI calls**: articles + preamble + 2 aggregation calls
  - Example: 50-article law = 52 AI calls
- **Database operations**: ~10 per article + relationships

### Error Rates

- **Invalid translations**: ~5% (handled by fallback)
- **Missing cross-references**: ~10% (logged as warnings)
- **Temporal inconsistencies**: ~2% (skipped with validation)

---

## Troubleshooting

### Common Issues

**Issue**: "Translation pending" in both languages
- **Cause**: AI returned invalid JSON or language mixing
- **Solution**: Fallback logic creates PT from official_text, EN as "Translation pending"

**Issue**: Title duplicated in summary
- **Cause**: AI repeats title at start of summary
- **Solution**: Auto-detected and removed

**Issue**: Summary ends with "..."
- **Cause**: AI truncated response
- **Solution**: Detected and triggers fallback

**Issue**: Cross-reference not found
- **Cause**: Target law not in database or URL pattern mismatch
- **Solution**: Logged as warning, processing continues

**Issue**: Temporal inconsistency
- **Cause**: Newer law trying to amend older law
- **Solution**: Validated and skipped with warning

---

## Future Enhancements

1. **Batch Processing**: Process multiple articles in single AI call
2. **Caching**: Cache translations for similar articles
3. **Parallel Processing**: Process articles concurrently
4. **Smart Retry**: Retry only failed articles, not entire law
5. **Quality Scoring**: Add confidence scores to translations
6. **Version Tracking**: Track law amendments over time

---

**End of Documentation**

For questions or issues, refer to the logs at each stage for detailed debugging information.
