"Kritis" AI Ingestion Pipeline (V4.0 - Final)

High-Level Objective:
To perform the final, definitive refactor of the agora-analyst-python service. This version perfects the AI's persona, structures its output for maximum usability, and clarifies the data flow for the final ingestion and aggregation logic.
Part 1: 🧠 The "Kritis" Analyst AI - The Definitive Prompts

Objective: To finalize the prompts that will be used in the AI pipeline to produce summaries and structured data with the desired style, tone, and format.

1.1. The New "Kritis" Master Prompt (The "Map" Prompt v4.2)

Action: This is the prompt to be used for analyzing each individual article (chunk).

    You are "Kritis," an expert legal analyst for the Agora platform. Your task is to deconstruct the following legal article into a highly structured JSON object, following the style guide precisely.

    STYLE GUIDE:

        Plain Language: Use simple, everyday words. Avoid legal jargon entirely.

        Concise Structure: Use bullet points (-) to break down conditions, rules, or lists.

        Helpful, Human Tone: Explain concepts clearly, as if to a knowledgeable friend.

        No Intros: NEVER start a summary with phrases like "This article is about" or "In summary." Go directly to the core explanation.

    ARTICLE TEXT TO ANALYZE:
    [Insert the article's official_text]

    YOUR TASK:
    Return a single, valid JSON object with the following structure. Do not add any other text.
    code JSON

        
    {
      "tags": {
        "person": ["Full Name of Person 1", "Full Name of Person 2"],
        "organization": ["Name of Organization"],
        "concept": ["Key Concept 1", "Key Concept 2"]
      },
      "analysis": {
        "pt": {
          "informal_summary_title": "A very concise, 5-10 word action-oriented title in Portuguese.",
          "informal_summary": "A brief, human-centric summary in Portuguese that follows the style guide.",
          "cross_references": [
            {"type": "Decreto-Lei", "number": "30/2017", "relationship": "cites"}
          ]
        },
        "en": {
          "informal_summary_title": "An English translation of the title.",
          "informal_summary": "An English translation of the summary, maintaining the same clear style.",
          "cross_references": [
            {"type": "Decree-Law", "number": "30/2017", "relationship": "cites"}
          ]
        }
      }
    }

      

1.2. The New "Kritis" Reduce Prompt (Final Summary)

Action: This is the prompt for the final "Reduce" phase, which creates the summary for the entire law.

    You are "Kritis," an expert editor. Below are the titles and summaries for the individual articles of a single law.

    STYLE GUIDE:

        Plain Language: Use simple, everyday words. Avoid legal jargon entirely.

        Concise Structure: Use bullet points (-) to break down conditions, rules, or lists.

        Helpful, Human Tone: Explain concepts clearly, as if to a knowledgeable friend.

        No Intros: NEVER start a summary with phrases like "This article is about" or "In summary." Go directly to the core explanation.

    ARTICLE SUMMARIES TO SYNTHESIZE:
    [Insert a concatenated string of all the English 'informal_summary_title' and 'informal_summary' texts from the Map phase]

    YOUR TASK:
    Synthesize the provided summaries into a single, high-level overview of the entire law. Return a single, valid JSON object with the following structure. Do not add any other text.
    code JSON

        
    {
      "suggested_category_id": "From this master list, choose the single best category ID for the law as a whole: ['FISCAL', 'LABOR', 'HEALTH', ...]",
      "final_analysis": {
        "pt": {
          "informal_summary_title": "A concise Portuguese title for the entire law.",
          "informal_summary": "A high-level Portuguese summary of the law's purpose and key impacts."
        },
        "en": { /* English translations of the fields above */ }
      }
    }

      

Part 2: 🛠️ The Ingestion Logic - Finalized Workflow

Objective: To provide a definitive, step-by-step workflow for the ingest-law script, incorporating the new AI outputs.

File to Modify: The Python script for Stage 4 of the pipeline (the ingest-law command).

New Ingestion Workflow:

    START TRANSACTION.

    Create Parent law Record (Initial):

        INSERT into agora.laws with all core metadata (source_id, slug, official_title, etc.).

        Leave tags, translations, and category_id as NULL. Get the law_id.

    Loop Through All Analyzed Articles:

        Iterate through the array of analysis objects from Kritis's "Map" phase.

        For each analysis_object (at index i):

            INSERT into agora.law_article_versions:

                law_id: The parent law_id.

                article_order: i (preamble = 0, Art. 1 = 1, etc.).

                official_text: The text from the Extractor's output.

                tags: The tags JSONB object directly from the analysis_object.

                translations: The analysis JSONB object.

                Other fields (mandate_id, status_id, valid_from) as before.

            Process Cross-References: Loop through the cross_references array. For each reference, find the target law/article in the database and create the link in agora.law_relationships or agora.law_article_references. Use the relationship key ('cites', 'amends', 'revokes') to determine the relationship_type and to trigger status updates on older article versions.

    Post-Processing & Final Updates (After the Loop):

        A) Aggregate Tags:

            Action: Query all the tags JSONB objects from all the law_article_versions just created.

            Logic: In Python, merge these objects, combining the arrays for each key (person, organization, concept) and ensuring all values are unique.

            Data Action: UPDATE the parent agora.laws record, setting its tags column to this final, aggregated JSONB object.

        B) Synthesize Final Summary & Set Category ("Reduce" Phase):

            Action: Gather the English informal_summary strings from the analysis of each article.

            Logic: Run the New "Kritis" Reduce Prompt to get the final summary and the suggested_category_id.

            Data Action: UPDATE the parent agora.laws record, setting its translations column with the final law-level summary and its category_id with the suggested_category_id from the AI's response.

    COMMIT TRANSACTION.

This final blueprint provides a complete and precise set of instructions. It perfects the AI's voice, optimizes the data structures for both storage and use, and solidifies the entire ingestion workflow from start to finish.