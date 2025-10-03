"Kritis" AI Analyst (Version 2.0)

High-Level Objective:
To perform a complete refactor of the "Kritis" AI pipeline. This will fix the metadata extraction failures and implement a sophisticated, multi-step analysis process to handle categorization, tagging, and the creation of historical and relational links between legal documents.
2.0. Stage 1 & 2: The "Extractor" AI - A More Demanding Role

Objective: To fix the metadata failures by giving the Extractor AI a more demanding, structured task.

Action: The prompt for the Extractor AI (which runs on the first chunk of every document) must be fundamentally changed. It is no longer just finding text; it is parsing the document's identity.

New "Extractor" Master Prompt (for the first chunk):

    You are a meticulous legal document parser. Analyze the following text, which is the beginning of an official government publication. Your task is to extract the core metadata. Return a single, valid JSON object with the following structure. Do not include any other text in your response.
    code JSON

        
    {
      "official_number": "The official number of this law (e.g., 'Decreto-Lei n.º 30/2017').",
      "official_title_pt": "The full, official title in Portuguese.",
      "law_type_id": "The ID of the law type based on the title (e.g., 'DECRETO_LEI').",
      "enactment_date": "The primary date of the law in YYYY-MM-DD format.",
      "summary_pt": "The text from the 'SUMÁRIO' section."
    }

      

Implementation:

    The crawler will now use this specialized prompt only on the first document_chunk (chunk_index = 0).

    The JSON output will be used to create the agora.laws and agora.sources records with correct, non-placeholder data. This solves the slug, title, and number issues immediately.

3.0. Stage 3: The "Analyst" AI ("Kritis") - A Richer, More Structured Analysis

Objective: To refactor the analysis stage to produce a highly structured, machine-readable JSON output that separates different types of information.

Action: The prompt and the expected output for the "Kritis" Analyst (which runs on every chunk) must be significantly enhanced.

New "Kritis" Master Prompt (The "Map" Prompt):

    You are "Kritis," an expert legal analyst. Your task is to deconstruct the following legal article text into a structured JSON object.

    CONTEXT:

        Master Category List: [Provide a comma-separated list of all agora.law_categories names]

        This Article Belongs To: [Insert the official_title of the parent law]

    ARTICLE TEXT TO ANALYZE:
    [Insert document_chunk.content]

    YOUR TASK: Return a single, valid JSON object with the following structure:
    code JSON

        
    {
      "suggested_category_id": "From the master list, choose the single best category ID for this article's content (e.g., 'FISCAL').",
      "analysis": {
        "pt": {
          "informal_summary_title": "A concise, 5-10 word action-oriented title in Portuguese.",
          "informal_summary": "A brief, action-oriented summary in Portuguese.",
          "key_dates": {
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          },
          "key_entities": [
            {"type": "person", "name": "Marcelo Rebelo de Sousa"},
            {"type": "organization", "name": "Conselho Superior da Guarda Nacional Republicana"}
          ],
          "cross_references": [
            {"type": "Decreto-Lei", "number": "30/2017", "article": "140"}
          ]
        },
        "en": {
          // English translations of the above fields
        }
      }
    }

      

Implementation:

    The AI's JSON output is now much richer and more structured.

    This entire JSON object is saved into the agora.source_ai_analysis.analysis_data column. This preserves the AI's complete thought process for each article.

4.0. Stage 4: The Ingestion & Linking Logic (The "Knowledge Graph Builder")

Objective: To transform the AI's rich analysis into final, interconnected database records.

Action: The ingest-law server action (or Python script) will now perform a much more sophisticated set of operations after the admin's approval.

The New Ingestion Workflow:

    Create the Core Records:

        The system creates the agora.laws, agora.law_articles, and agora.law_article_versions records as before.

        The translations field on law_article_versions is now populated with just the informal_summary_title and informal_summary from the AI's analysis object.

    Perform Automated Tagging (Simple Search):

        Logic: For each new law_article_versions record, the system takes its official_text.

        It queries the agora.tags table (SELECT name FROM agora.tags).

        It then performs a simple string search for each tag name within the official_text.

        If a match is found, it creates the link in the agora.law_article_version_tags junction table.

    Perform Relational Linking (The "Kritis" Assisted Logic):

        Logic: For each new law_article_versions record, the system looks at the cross_references array in its analysis_data.

        For each reference (e.g., { "type": "Decreto-Lei", "number": "30/2017" }):

            It performs a SELECT query on the agora.laws table to find the id of the law where official_number is LIKE '%30/2017%'.

            If a match is found, it creates the record in the agora.law_relationships table, linking the new law to the old one.

            Directional Check: The system checks the enactment_date of both laws. A law can only AMEND or REVOKE a law with an earlier date. This prevents logical errors.

            "Kritis" for Ambiguity: If the text contains ambiguous keywords like "revokes" or "amends," this is where a final, targeted AI call can be made.

                Prompt: "Here are two law articles, A (new) and B (old). The text of A says it 'alters' B. Based on this, is the correct relationship AMENDS or SUPERSEDES? Return a single word."

    Perform Status Updates (Historical Logic):

        Logic: After creating the new law_article_versions record and its AMENDS or REVOKES relationships, the system must update the historical record.

        It takes the target_article_version_id from the newly created relationship.

        It performs an UPDATE on that old law_article_versions record, setting its status_id to 'SUPERSEDED' and its valid_to date to the day before the new version's valid_from date.

This revised and deeply detailed plan creates a powerful feedback loop. The AI provides structured suggestions, and the database logic uses those suggestions to perform intelligent, rule-based operations, building a rich, accurate, and interconnected knowledge graph of your country's entire legal history.