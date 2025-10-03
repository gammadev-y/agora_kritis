Implementing Multi-Article Chunk Processing

High-Level Objective:
To refactor the Agora AI Ingestion Pipeline to correctly identify, extract, and analyze multiple distinct articles that may exist within a single document_chunk. The system must be able to parse a chunk containing several articles and produce a separate, structured analysis for each one, leading to the correct creation of multiple law_articles records in the database.
Part 1: 🔬 The "Extractor" AI - The Smart Parser

Objective: To upgrade the Extractor AI's role from a simple text grabber to a sophisticated structural parser.

Action: The prompt and the expected output for the "Extractor AI" (Stage 2) must be fundamentally changed.

New "Extractor" Master Prompt:

    You are a meticulous legal document parser. Your sole purpose is to identify and separate distinct articles within a given block of text from an official government publication.

    CRITICAL INSTRUCTIONS:

        Scan the text for article delimiters, which are lines that start with Artigo X.º or a similar pattern.

        For each distinct article you find, extract its article_number and its complete, verbatim official_text.

        Return a single, valid JSON object. Do not include any other text or explanations. The JSON object must contain a single key, articles, which is an array of objects.

    TEXT CHUNK TO PARSE:
    [Insert the full text of the document_chunk.content]

    YOUR TASK:
    Return a JSON object with the following structure:
    code JSON

        
    {
      "articles": [
        {
          "article_number": "Artigo 1.º",
          "official_text": "The full, verbatim text of the first article found in the chunk..."
        },
        {
          "article_number": "Artigo 2.º",
          "official_text": "The full, verbatim text of the second article found in the chunk..."
        },
        {
          "article_number": "Artigo 3.º",
          "official_text": "The full, verbatim text of the third article found in the chunk..."
        }
      ]
    }

      

Implementation (pending_extractions):

    The extracted_data column in agora.pending_extractions will now store this JSON object containing the articles array. This correctly captures that a single chunk can produce multiple raw articles.

Part 2: 🧠 The "Analyst" AI ("Kritis") - The Batch Processor

Objective: To refactor the Analyst AI to process multiple articles in a single, efficient API call, while respecting token limits.

Action: The logic for the "Analyst AI" (Stage 3) is now a dynamic, batch-processing workflow.

New "Analyst" Workflow Logic:

    Fetch & Consolidate: The function receives a source_id. It fetches all pending_extractions for that source and concatenates all the articles arrays into a single, master list of all articles in the document.

    Smart Batching (The Token Manager):

        Purpose: To group multiple small articles together to make efficient use of the Gemini API's context window.

        Logic:

            Initialize an empty batch array and an empty batches array.

            Initialize currentTokenCount = 0.

            Loop through the master list of articles:

                Calculate the token count of the current article's text.

                If currentTokenCount + articleTokenCount is less than a safe limit (e.g., 6000 tokens, leaving room for the prompt), add the article to the current batch and update currentTokenCount.

                Else, the current batch is full. Push the batch to the batches array, and start a new batch with the current article.

        Result: You now have an array of arrays, where each inner array is a group of articles that can be safely processed in a single API call.

    Parallel Batch Analysis:

        The function now iterates through the batches array.

        For each batch, it constructs a new, more powerful prompt.

New "Kritis" Master Prompt (The "Map" Prompt, now for Batches):

    You are "Kritis," an expert legal analyst. Your task is to deconstruct a list of legal articles into a structured JSON array.

    CONTEXT:

        Master Category List: [...list of categories...]

        This Law's Title: [...parent law title...]

    ARTICLES TO ANALYZE:
    You will be given an array of JSON objects, where each object contains an article_number and its official_text.

    [Insert the JSON string of the current batch of articles here]

    YOUR TASK:
    For each article in the input array, perform a detailed analysis. Return a single, valid JSON object containing one key, analyses. This key must be an array where each object corresponds to an input article and has the following structure:
    code JSON

        
    {
      "analyses": [
        {
          "article_number": "Artigo 1.º", // Must match the input article number
          "suggested_category_id": "The single best category ID for this article.",
          "analysis": {
            "pt": {
              "informal_summary_title": "A concise Portuguese title.",
              "informal_summary": "A brief, action-oriented Portuguese summary.",
              "key_references": [ "List of key dates, entities, and cross-references." ]
            },
            "en": {
              // English translations of the above fields
            }
          }
        },
        {
          "article_number": "Artigo 2.º",
          // ... analysis for the second article in the batch
        }
      ]
    }

      

Implementation (pending_ingestions):

    After all batches have been processed, the system will now have a list of analyses for every article in the document.

    This complete list of analyses is what gets saved into the ingestion_data column of the agora.pending_ingestions table, ready for human validation.

Part 3: 🛠️ The Ingestion & Linking Logic (Update)

Objective: To update the final ingestion script to correctly handle the multi-article data.

Action: The ingest-law server action or Python script is now more straightforward.

New Ingestion Workflow:

    Create the Parent Law: Creates the main record in agora.laws.

    Loop and Create: It now loops through the analyses array in the ingestion_data. For each item in the array:

        It INSERTs a record into agora.law_articles using the article_number.

        It INSERTs a record into agora.law_article_versions, using the official_text (which it can now get by matching the article_number back to the original pending_extractions data) and the analysis object for the translations column.

        It performs the automated tagging and relational linking logic for that specific article before moving to the next one.

This new, more sophisticated pipeline directly solves the "many articles in one chunk" problem. It makes the Extractor AI a simple but powerful parser, and it equips the Analyst AI with a smart batching system to efficiently process documents of any size while still providing a granular, article-by-article analysis.