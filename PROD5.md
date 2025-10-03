"Kritis" AI Analyst & Ingestion Pipeline (Version 3.0)

High-Level Objective:
To perform a major refactor of the entire AI Ingestion Pipeline to correctly handle the "preamble" (non-article) text of legal documents, improve metadata extraction, enrich the AI's analytical output, and implement an intelligent, entity-driven tagging system.
Part 1: 🏛️ Foundational Database & Schema Changes

Objective: To prepare the database to support the new, more granular data requirements.

1.1. agora.tags Table Enhancement by adding a  "type" column to the agora.tags table (DONE)
      

Part 2: 🧠 The "Extractor" AI - Handling the Preamble

Objective: To upgrade the Extractor AI to differentiate between the introductory text of a law and its numbered articles.

Action: The prompt and the logic for the "Extractor AI" (Stage 2) must be updated.

New "Extractor" Master Prompt:

    You are a meticulous legal document parser. Your task is to identify and separate the introductory "preamble" from the numbered articles in the provided text.

    CRITICAL INSTRUCTIONS:

        The preamble is all the text that comes before the first line that starts with "Artigo 1.º".

        Identify every distinct article (Artigo X.º) and its complete text.

        Return a single, valid JSON object. The JSON object must have two keys: preamble_text and articles.

    TEXT CHUNK TO PARSE:
    [Insert the full text of the document_chunk.content]

    YOUR TASK:
    Return a JSON object with the following structure:
    code JSON

        
    {
      "preamble_text": "All the text from the beginning of the chunk up to the first 'Artigo 1.º'...",
      "articles": [
        { "article_number": "Artigo 1.º", "official_text": "..." },
        { "article_number": "Artigo 2.º", "official_text": "..." }
      ]
    }

      

Implementation (pending_extractions):

    The extracted_data column in agora.pending_extractions will now store this new, richer JSON structure.

Part 3: 🧠 The "Kritis" Analyst AI - A More Demanding Analysis

Objective: To refactor the Analyst AI to produce a more structured output, derive better metadata, and handle token limits more gracefully.

Action: The prompt for "Kritis" (the "Map" phase) must be significantly enhanced.

New "Kritis" Master Prompt (The "Map" Prompt v3.0):

    You are "Kritis," an expert legal and financial analyst for the Agora platform. Your task is to deconstruct a legal article into a highly structured JSON object.

    CONTEXT:

        Master Category List: ['FISCAL', 'LABOR', 'HEALTH', 'ENVIRONMENTAL', ...]

        This Article Belongs To: [Insert the official_title of the parent law]

        Law Preamble: [Insert the preamble_text from the Extractor's output]

    ARTICLE TEXT TO ANALYZE:
    [Insert a single article's official_text here]

    YOUR TASK:
    Return a single, valid JSON object with the following structure. Do not include any other text.
    code JSON

        
    {
      "suggested_category_id": "From the master list, choose the single best category ID for this article's content.",
      "analysis": {
        "pt": {
          "informal_summary_title": "A very concise, 5-10 word action-oriented title in Portuguese summarizing the core action.",
          "informal_summary": "A brief, action-oriented summary in Portuguese explaining what this article does. **Ensure the summary is complete and does not end in '...'.**",
          "key_dates": {
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          },
          "key_entities": [
            {"type": "person", "name": "Marcelo Rebelo de Sousa"},
            {"type": "organization", "name": "Secretariado da Reforma Administrativa"},
            {"type": "concept", "name": "assistance in sickness"},
            {"type": "concept", "name": "pension"}
          ],
          "cross_references": [
            {"type": "Decreto-Lei", "number": "26334"},
            {"type": "Decreto", "number": "16563"}
          ]
        },
        "en": { /* English translations of the above fields */ }
      }
    }

      

Key Prompt Improvements:

    Preamble as Context: The AI now receives the law's preamble, giving it crucial context for understanding the purpose of individual articles.

    Complete Summary: The prompt explicitly instructs the AI not to truncate its summary.

    Enriched key_entities: The prompt now guides the AI to extract not just people and organizations, but also key concepts like "taxes," "social housing," etc. This is the foundation for the new tagging system.

Part 4: 🛠️ The Ingestion & Linking Logic (The "Knowledge Graph Builder")

Objective: To upgrade the final ingestion script to use the AI's new, richer output to correctly populate all fields and create intelligent links.

Action: The ingest-law server action or Python script requires a significant logic upgrade.

The New Ingestion Workflow:

    Create the Parent Law Record:

        Logic: It first processes the first document_chunk using the New "Extractor" Prompt from Part 2.

        It uses the JSON output to populate the agora.laws table:

            official_number & official_title: Use the official_number extracted by the AI.

            slug: Generate a slug from the official_number and enactment_date (e.g., dl-49031-19690527).

            enactment_date: Use the enactment_date from the AI's output.

        The translations field for the law itself is left NULL for now. It will be populated at the end of the process.

    Loop Through All Articles (from all chunks):

        The system now iterates through the full list of articles extracted from all chunks. For each article:

            A) Create Core Records: It creates the law_articles and law_article_versions records. The official_text comes from the Extractor AI, and the translations (summary) comes from the Analyst AI's output for that specific article.

            B) The New Intelligent Tagging:

                It takes the key_entities array from the AI's analysis.

                For each entity (e.g., { "type": "person", "name": "Marcelo Rebelo de Sousa" }):

                    It performs an UPSERT into agora.tags on the name column, setting the type field.

                    It then creates the link in the agora.law_article_version_tags table.

            C) Relational Linking (Cross-References):

                It takes the cross_references array.

                For each reference, it queries agora.laws to find the target_law_id.

                It then creates the record in agora.law_relationships.

                Directional & Status Check: The logic now includes the crucial check. It compares the enactment_date of the source and target laws. If the source law is newer and contains keywords like "revokes," it will trigger another function, updateArticleVersionStatus(target_article_id, new_status, valid_to_date), which updates the old article's status to 'REVOKED'.

    The Final "Reduce" Phase (Law-Level Summary):

        Logic: After all articles have been ingested, the "Reduce" phase runs as planned.

        Crucial Improvement: The input for this final summary is no longer the raw text, but the collection of high-quality, concise informal_summary strings (in English) generated for each article. This is far more token-efficient and leads to a better high-level summary.

        Data Action: The final output of the Reduce phase is used to UPDATE the translations column of the parent agora.laws record, completing the process.

This revised and deeply detailed plan creates a powerful, self-correcting feedback loop. The AI provides more structured suggestions, and the database logic uses that structure to perform intelligent, rule-based operations, building a rich, accurate, and interconnected knowledge graph.