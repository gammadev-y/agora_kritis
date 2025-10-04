Implementing "Kritis," the Agora AI Analyst

High-Level Objective:
To build the "Kritis" AI service within the agora-analyst-python project. Kritis's mission is to take a raw, chunked source document, perform a multi-stage analysis using the Map-Reduce pattern, and ultimately produce a complete, structured, and versioned legal entity in the agora.laws and related tables. All AI-generated insights will be stored in the agora.source_ai_analysis table, leaving the original agora.sources record untouched.
Part 1: 🏛️ The Data Flow & Architecture

The workflow is a sequential, multi-stage process triggered by an admin.

The Workflow Diagram:
[Source with Document Chunks] -> [Stage 1: Kritis "Map" Analysis] -> [Stage 2: Kritis "Reduce" Synthesis] -> [Stage 3: Law Ingestion]

Core Principle: We separate the Analysis (generating insights and summaries) from the Ingestion (creating the final law records). The analysis is stored first, providing an auditable trail of the AI's work before the final law records are created.
Part 2: 🧠 The Kritis AI Implementation Plan

Objective: To build the core logic of the Kritis pipeline.

File: /analysis/document_analyzer.py

2.1. Stage 1: The "Map" Phase - Per-Chunk Analysis

    Function: run_map_phase(source_id: str)

    User Story: As an admin, I want to trigger a deep analysis of each individual article (chunk) of a source document.

    Logic:

        The function receives a source_id.

        It fetches all document_chunks for that source.

        It calls the build_context_package(source_id) function (as previously designed) to perform the RAG and get the context.

        It iterates through each document_chunk and performs the following for each:

            Constructs the new "Kritis" Master Prompt (see below).

            Calls the Gemini API.

            Receives a structured JSON response.

            Database Action: INSERTs a new record into the agora.source_ai_analysis table.

                source_id: The ID of the parent source document.

                chunk_id: The ID of the specific chunk being analyzed.

                model_version: The identifier for the Gemini model used.

                analysis_data: The full JSON output from the AI.

        Result: The source_ai_analysis table is now populated with a detailed, structured analysis for every single article in the document.

The New "Kritis" Master Prompt (The "Map" Prompt):

    You are "Kritis," an expert legal analyst for the Agora platform. Your task is to deconstruct a legal text into a clear, structured JSON object. Your tone must be neutral, factual, and action-oriented.

    CRITICAL INSTRUCTIONS:

        DO NOT start any summary with phrases like "In summary" or "This text is about."

        BE CONCISE. The informal_summary_title must be a short, impactful headline.

        SEPARATE the narrative summary from the hard references.

    CONTEXTUAL INFORMATION:

        Document Type: [e.g., Decreto-Lei]

        Related Database Items: [Insert summaries of related promises/actions found via RAG]

    ARTICLE TEXT TO ANALYZE:
    [Insert the full text of the document_chunk.content]

    YOUR TASK:
    Return a single, valid JSON object with the following structure. Do not include any other text in your response.
    code JSON

        
    {
      "pt": {
        "informal_summary_title": "A very concise, 5-10 word title in Portuguese summarizing the core action of this article.",
        "informal_summary": "A brief, action-oriented summary in Portuguese explaining what this article does.",
        "key_references": [
          "A list item for each important date, legal article, or entity reference found in the text."
        ]
      },
      "en": {
        "informal_summary_title": "An English translation of the concise title.",
        "informal_summary": "An English translation of the action-oriented summary.",
        "key_references": [
          "An English translation of the key references."
        ]
      }
    }

      

2.2. Stage 2: The "Reduce" Phase - Document-Level Synthesis

    Function: run_reduce_phase(source_id: str)

    User Story: After all articles are analyzed, I want the system to generate a high-level summary for the entire law.

    Logic:

        The function receives a source_id.

        It fetches all source_ai_analysis records associated with that source_id.

        Token Management: It checks if the combined length of all the informal_summary fields exceeds the token limit.

            If NOT over limit: It concatenates all the summaries.

            If OVER limit (The "Second Map-Reduce"): It groups the summaries into batches that fit within the token limit. For each batch, it runs a "pre-reduce" prompt: "Summarize these summaries." It then takes the output of these pre-reduce calls and concatenates them.

        It constructs the "Kritis Reduce Prompt":

            "You are "Kritis," an expert editor. Here are the summaries for every article in a law. Your task is to synthesize them into a single, high-level informal_summary_title and informal_summary for the entire law. Capture its overall purpose and most significant impacts."

        It calls the Gemini API to get the final summary (in PT).

        It makes a final translation call to get the English version.

    Result: The function returns a final, structured JSON object for the entire document, ready for ingestion.

2.3. Stage 3: The Law Ingestion Workflow

    Function: ingest_law_from_analysis(source_id: str)

    User Story: As an admin, after Kritis has finished its analysis, I want to press a button to create the final, structured law in the database.

    Logic:

        The function receives a source_id.

        It calls run_reduce_phase(source_id) to get the final, top-level summary.

        It fetches the original metadata from agora.sources (official title, number, date).

        Database Action (Transaction):

            It begins a transaction.

            INSERT into agora.laws: Creates the main law record, populating the official_title and filling the translations column with the final "Reduce" phase summary.

            Loop through source_ai_analysis records: For each analyzed chunk:

                INSERT into agora.law_articles: Creates the abstract article record.

                INSERT into agora.law_article_versions: Creates the version record, populating official_text with document_chunks.content and the translations column with the analysis_data from the "Map" phase.

            It commits the transaction.

4.0. 🚀 The Final Implementation Plan for the AI Agent

    Refactor main.py: Create three distinct CLI commands:

        python main.py analyze-chunks --source-id <uuid> (Runs Stage 1: Map Phase)

        python main.py synthesize-summary --source-id <uuid> (Runs Stage 2: Reduce Phase)

        python main.py ingest-law --source-id <uuid> (Runs Stage 3: Ingestion)

    Build the document_analyzer.py Module: Implement the three core functions (build_context_package, run_map_phase, run_reduce_phase, ingest_law_from_analysis) with the logic described above.

    Create the Admin UI:

        On your /admin/crawler page, for each processed source (is_processed = true), add an "Analyze with Kritis" button.

        This button triggers the analyze-chunks workflow. The UI should show a "Processing..." status.

        Once complete, the button changes to "Review & Ingest."

        Clicking "Review & Ingest" takes the admin to a new validation page where they can see the proposed law and law_article_versions data (generated by calling synthesize-summary and fetching the per-chunk analyses).

        An "Approve & Create Law" button on this page triggers the final ingest-law workflow.

This detailed plan provides a clear, robust, and staged approach. It separates the concerns of analysis and ingestion, creates an auditable trail of AI's work, and provides a clear path to transforming your raw crawled data into the structured legal knowledge graph that is at the heart of the Agora project.