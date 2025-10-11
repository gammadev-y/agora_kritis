# 🚀 PROD Document: Implementing "Kritis" V6.0 - The Production Analyst

## High-Level Objective
Perform the final production refactor of the agora-kritis-python project to optimize cost and efficiency by offloading translation locally, implement a token-aware Reduce phase for law summaries, and enforce a human-centric, plain-language AI output.

---

## Key Improvements in V6.0
- **AI Efficiency:** Use Gemini API only for analysis in the source language (Portuguese from portugal).  
- **Local Translation:** Use argos-translate locally with googletrans fallback to reduce API calls and cost.  
- **Intelligent Summarization:** Token-aware Reduce phase that synthesizes article summaries (not concatenation).  
- **Perfected AI Persona:** Upgraded "Kritis" prompt with style guide and few-shot examples to enforce concise, human-centric output.  
- **Multilingual Tag Aggregation:** Translate conceptual tags while preserving proper nouns.

---

## Part 1 — The Foundational Refactor (Python Project)

### 1.1 Update Dependencies
File: `/agora-kritis-python/requirements.txt`

Add:
```text
argostranslate
googletrans==4.0.0-rc1
```

Post-install step (include in Dockerfile or setup script):
```bash
python -c "from argostranslate import package; package.update_package_index(); available_packages = package.get_available_packages(); package.install_from_path(next(filter(lambda x: x.from_code == 'pt' and x.to_code == 'en', available_packages)).download())"
```

### 1.2 Create the Translation Module
File: `/lib/translator.py`

- Implement `translate_text(text: str) -> str`:
    - Try argos-translate first.
    - On failure, log a warning and fall back to googletrans.
- Implement `translate_analysis_object(analysis: dict) -> dict`:
    - Translate `informal_summary_title` and `informal_summary`.
    - Return a bilingual analysis object containing both `pt` and `en` keys.

---
Main language is portuguese from portugal pt-pt.

## Part 2 — The "Kritis" AI Pipeline (Core Refactor)

### 2.1 "Kritis" Master Prompt (Map Phase v5.2)
- Output language: Portuguese only (translation handled locally).
- Role: "Kritis," an expert legal analyst. Deconstruct a Portuguese legal article into a structured JSON object.
- STYLE GUIDE (CRITICAL):
    - Plain language — avoid legal jargon.
    - Use bullet points (-) for conditions/lists.
    - Helpful tone; explain in normal human language as to a friend that does not understand politics.
    - No intros — go straight to the core explanation (NO referencing like "This article...", and just go straight to the action and objective)
    - Use markdown to highlight in italic, bold and paragraphs.
- Example informal summary (perfect):
```text
O limite de idade para cargos públicos é ignorado se:
- Tiver tido serviço prévio contínuo ao estado;
- As interrupções de serviço não tiverem sido por sua culpa e duraram menos de 60 dias.
```
- ARTICLE TEXT TO ANALYZE: `{content}`

- Return one valid JSON (all text in Portuguese) with structure:
```json
{
    "tags": {
        "person": ["Nome da Pessoa"],
        "organization": ["Nome da Organização"],
        "concept": ["Conceito Chave"]
    },
    "informal_summary_title": "Um título muito conciso e orientado para a ação.",
    "informal_summary": "Um resumo breve e centrado no ser humano que segue o guia de estilo.",
    "cross_references": [
        { "relationship": "cites", "type": "Decreto", "number": "19478", "article_number": "14.º", "url": "..." }
    ]
}
```

### 2.2 "Kritis" Reduce Prompt (Final Law Summary)
- Output language: Portuguese only.
- Role: "Kritis," an expert editor. Given article summaries, synthesize a single high-level overview.
- STYLE GUIDE: same as Map phase.
- Input: concatenated Portuguese `informal_summary` texts from Map phase.
- Return one valid JSON (all text in Portuguese):
```json
{
    "suggested_category_id": "From this master list, choose the single best category ID: ['FISCAL', 'LABOR', ...]",
    "final_analysis": {
        "informal_summary_title": "Um título conciso para toda a lei.",
        "informal_summary": "Um resumo de alto nível sobre o propósito e os principais impactos da lei."
    }
}
```

---

## Part 3 — The Ingestion Logic: Final Workflow

Modify the ingest-law script to implement the following workflow.

### Overall Flow
1. Create parent law record (unchanged).
2. Run Map phase:
     - Iterate all extracted articles (preamble + numbered).
     - For each article: call the Kritis Master Prompt to get a Portuguese-only analysis JSON.
     - Store all PT-only analysis objects in a list.
3. Loop through and ingest articles:
     - For each PT analysis object:
         - Translate via `_translate_analysis_object` in `/lib/translator.py` to produce a bilingual object.
         - INSERT into `agora.law_articles`:
             - Save bilingual analysis in `translations` column.
             - Save `tags` object into `tags` column.
         - Process cross-references as before.
4. Post-processing & final updates:
     A) Aggregate & Translate Tags
     - Query tags from the created `law_articles`.
     - Aggregate unique Portuguese tags into `{ "person": [...], "organization": [...], "concept": [...] }`.
     - Call `_translate_tags` to translate only the `concept` values; copy `person` and `organization` unchanged.
     - Assemble multilingual tags: `{ "pt": {...}, "en": {...} }`.
     - UPDATE parent `agora.laws` record `tags` column.

     B) Synthesize Final Summary (Reduce Phase with Token Management)
     - Gather Portuguese `informal_summary` strings from all article analyses.
     - Token limit logic:
         - Determine model token limit; use a safe internal limit (e.g., 1,000,000 tokens).
         - Combine summaries and count tokens.
         - If under limit: call Kritis Reduce once.
         - If over limit: split summaries into batches that fit the limit, run a pre-summarization prompt per batch, then run final Reduce on pre-summaries.
     - Translate final Portuguese summary with local `_translate_text`.
     - UPDATE parent `agora.laws` record:
         - Set `translations` column with final law-level bilingual summary.
         - Set `category_id` with `suggested_category_id`.

---

## Notes & Rationale
- This design keeps the AI focused on high-value analysis in Portuguese while deterministic translation is local and free.
- Token-aware Reduce prevents excessive model calls and enables scalable synthesis for very large laws.

