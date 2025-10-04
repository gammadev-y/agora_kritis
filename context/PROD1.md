The "Agora Analyst" Python Project Setup

Objective: To set up a new, dedicated GitHub repository for the AI analysis service.

2.1. Create a New Repository

    Name: agora-analyst-python

    Structure:
    code Code

        
    /agora-analyst-python/
    ├── analysis/
    │   ├── __init__.py
    │   └── document_analyzer.py  # Core logic for the Map-Reduce process
    ├── lib/
    │   ├── __init__.py
    │   └── supabase_client.py
    ├── main.py                 # The CLI entry point
    ├── .env.example
    ├── Dockerfile
    └── requirements.txt

      

2.2. Define Dependencies
File: requirements.txt
code Code

    
supabase
python-dotenv
google-generativeai  # The official Python client for the Gemini API
numpy               # A dependency for vector operations
pgvector            # For handling vector types before sending to Supabase

  

2.3. Configure the Dockerfile
File: Dockerfile
code Dockerfile

    
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "main.py"]

  

Part 3: 🧠 The AI Implementation Plan (The "Map-Reduce" Workflow)

Objective: To build the core logic of the analysis pipeline.

3.1. The CLI Entry Point
File: main.py

    Action: Create an argparse CLI with a single command: analyze-source.

    Arguments: It must accept --source-id <uuid>.

3.2. The Main Analyzer Logic
File: /analysis/document_analyzer.py

    Function 1: build_context_package(source_id)

        Purpose: The RAG "Context Prompt" builder.

        Logic:

            Fetches all document_chunks for the given source_id.

            Scans the content of the chunks for explicit references to other laws.

            Queries the agora.laws table to fetch the summaries of these referenced laws.

            Performs a vector search on agora.search_index to find the top 3 semantically similar promises/actions.

            Assembles all this information into a single, structured "context string."

    Function 2: run_map_phase(chunks, context_package) (The "Mapper")

        Purpose: To analyze each chunk individually.

        Logic:

            Iterates through each document_chunk.

            For each chunk, it constructs the "Map Prompt" (as defined in our brainstorm), including the context_package and the chunk's text.

            It calls the Gemini API with this prompt. To handle rate limits, it should include a small delay (e.g., time.sleep(1)) between API calls.

            It collects the JSON responses (containing summary_pt, key_takeaway_pt, suggested_tags) into a list.

            This can be parallelized using Python's asyncio and asyncio.gather for significantly faster processing.

    Function 3: run_reduce_phase(map_results) (The "Reducer")

        Purpose: To create the final, high-level summary.

        Logic:

            Extracts all the summary_pt strings from the map_results.

            Concatenates them into a single block of text.

            Constructs the "Reduce Prompt" (as defined in our brainstorm) and sends it to the Gemini API to get the final informal_summary_pt.

            Makes a final Gemini API call to translate the key titles and the final summary into English.

    Function 4: save_analysis_to_db(source_id, map_results, reduce_results)

        Purpose: To persist the final results.

        Logic:

            UPDATE agora.sources and agora.laws with the final, translated summaries.

            Loop through the map_results and UPDATE the translations and tags for each corresponding agora.law_article_versions record.

3.3. The Orchestrator
File: /main.py (when the analyze-source command is called)

    Logic:

        Calls build_context_package.

        Calls run_map_phase.

        Calls run_reduce_phase.

        Calls save_analysis_to_db.

        Logs the entire process.