Refactoring the "Kritis" AI Ingestion Pipeline (V3.1)

**High-Level Objective:**
To perform a complete architectural refactor of the Agora Laws Module and the corresponding agora-analyst-python service. This refactor will simplify the database schema, improve data integrity, and enhance the AI's analytical output to be more structured and directly usable for intelligent tagging and relationship mapping.

### **Part 1: 🏛️ The Database Refactor: From Complex to Consolidated**

Objective: To simplify the database schema by removing redundant tables and consolidating information into a more efficient and intuitive structure.

**1.1. Summary of Schema Changes:**

    agora.law_articles (Table): This intermediate table is DEPRECATED. The concept of an "article" will now be directly represented by a record in the main versions table.

    agora.law_article_versions (Table): This table is EVOLVED into the new, central table for all article content.

    agora.tags & agora.law_article_version_tags (Tables): These tables are DEPRECATED. The tagging information will be consolidated directly onto the article and law records as a JSONB field.

**"Before" vs. "After" Schema:**
Before (Old Schema)	After (New Schema)	Rationale
laws -> law_articles -> law_article_versions	laws -> law_article_versions	Simplifies the relationship. A law is now a direct collection of its versions.
law_article_versions has article_id	law_article_versions has law_id + article_order	More direct and efficient. article_order (0 for preamble, 1 for Art. 1, etc.) defines the sequence.
tags & law_article_version_tags (Junction)	tags (jsonb) column on law_article_versions and laws	Simplifies queries and keeps tag data directly with the content it describes.
law_article_references links version_id to version_id	law_article_references links version_id to version_id	No change, but the table is rebuilt to ensure foreign key integrity.


### **Part 2: 🧠 The "Kritis" AI Refactor**

**Objective:** To update the Python service to work with the new database schema and to produce the new, more structured analytical output.

**2.1. The "Extractor" AI - Now with Preamble Awareness**

*   **Task:** The Extractor's prompt must be updated to differentiate between the law's introductory text and its numbered articles.
*   **Prompt Instruction:** Modify the prompt to return a JSON object with two top-level keys:
    1.  **`preamble_text`**: A string containing all text *before* the first "Artigo 1.º".
    2.  **`articles`**: An array of objects, where each object has an `article_number` and `official_text`.
*   **Output:** The `extracted_data` in `agora.pending_extractions` will now store this `{ "preamble_text": "...", "articles": [...] }` structure.

**2.2. The "Kritis" Analyst AI - The New Structured Output**

*   **Task:** The Analyst's prompt must be updated to produce a richer, more structured JSON, including the new `tags` array.
*   **Prompt Instruction:** Modify the prompt given to "Kritis" to require the following JSON output structure for **each article** it analyzes:

    ```json
    {
      "article_number": "Artigo 1.º",
      "suggested_category_id": "FISCAL",
      "tags": [
        {"type": "person", "name": "Marcelo Rebelo de Sousa"},
        {"type": "concept", "name": "Public Administration"}
      ],
      "analysis": {
        "pt": {
          "informal_summary_title": "...",
          "informal_summary": "...",
          "cross_references": [
            {"type": "Decreto-Lei", "number": "30/2017"}
          ]
        },
        "en": { /* ... */ }
      }
    }
    ```
*   **Key Change:** The `key_entities` and `key_dates` are now replaced by the more structured `tags` and `cross_references` arrays.

**2.3. The Ingestion Logic (`ingest-law` command)**

*   **Task:** This is the most critical part of the refactor. The final script that writes to the database must be completely rewritten to follow this new logic.
*   **New Workflow:**
    1.  **START TRANSACTION.**
    2.  **Create Parent `law` Record:**
        *   `INSERT` into `agora.laws`.
        *   **`source_id`:** Must be passed as an argument to the function.
        *   **`official_title` & `slug`:** Use the metadata extracted from the first chunk.
        *   `tags` and `translations` fields are left `NULL` for now.
        *   Get the `law_id` of the newly created record.
    3.  **Process and Insert the Preamble:**
        *   Take the `preamble_text` from the Extractor's output.
        *   Call the "Kritis" Analyst AI on this text to get its analysis (summary, tags, etc.).
        *   `INSERT` one record into `agora.law_article_versions`.
            *   `law_id`: The ID from the step above.
            *   `article_order`: **`0`**. This is the explicit identifier for the preamble.
            *   `official_text`: The `preamble_text`.
            *   `tags`: The `tags` JSON array from the Kritis analysis.
            *   `translations`: The `analysis` object from the Kritis analysis.
    4.  **Loop Through Numbered Articles:**
        *   Iterate through the `articles` array from the Extractor's output.
        *   For each article (e.g., at index `i`):
            *   Get the corresponding analysis from the Kritis output.
            *   `INSERT` one record into `agora.law_article_versions`.
                *   `law_id`: The parent `law_id`.
                *   `article_order`: `i + 1`. (So "Artigo 1.º" is order 1, "Artigo 2.º" is order 2, etc.).
                *   `official_text`: The article's text.
                *   `tags` and `translations`: The structured JSON from the Kritis analysis for this specific article.
    5.  **Post-Processing & Final Updates:**
        *   **Aggregate Tags:** After the loop, query all the `tags` from all the `law_article_versions` just created for this `law_id`. Compile a unique, aggregated list of all tags. `UPDATE` the parent `agora.laws` record, setting its `tags` column to this new aggregated array.
        *   **Synthesize Summary (Reduce Phase):** Run the final "Reduce" phase as planned, using the individual article summaries to generate a high-level summary for the entire law. `UPDATE` the parent `agora.laws` record, setting its `translations` column with this final summary.
    6.  **COMMIT TRANSACTION.**

This refined PROD document provides a clear, unambiguous, and technically sound roadmap. It resolves the architectural entropy, improves data integrity, and sets a solid foundation for the next stage of your AI-powered analysis features.

  