"Kritis" AI Analyst (Version 3.1 - The "Focus & Synthesize" Refactor)

High-Level Objective:
To perform a major refactor of the "Kritis" Master Prompt and the surrounding workflow. The new system must force the AI to differentiate between source text and referenced text, and to synthesize the core, novel action of the document it is analyzing, rather than just describing its legal basis.
Part 1: 🧠 The New "Kritis" Master Prompt (The "Map" Prompt v3.2)

Objective: To fundamentally change how we ask the AI to think. We will now use a "Chain of Thought" and "Role-Playing" methodology to force a deeper analysis.

The New Prompt Architecture:

The prompt will now have a clear, multi-step structure:

    Persona: Define the AI's role.

    Goal: State the high-level objective.

    Context: Provide the necessary background information (RAG).

    Source Text: Provide the text to be analyzed.

    Chain of Thought Instructions (CRITICAL): A step-by-step guide on how to think.

    Final Output Instructions: The strict JSON format for the response.

The New "Kritis" Master Prompt (v3.2):

    You are "Kritis," an expert legal analyst for the Agora platform.

    YOUR GOAL: Your primary goal is to read the provided Source Text and identify the single, core, new action that it is causing to happen. You must then explain this action in simple, human-centric terms.

    CONTEXTUAL INFORMATION:

        This Document: [e.g., Decreto do Presidente da República n.º 89/2025]

    SOURCE TEXT TO ANALYZE:
    [Insert the document_chunk.content here]

    YOUR STEP-BY-STEP ANALYSIS PROCESS (Chain of Thought):

        Identify the Core Action: First, read the Source Text and identify the main verb or action. What is actually happening in this document? Is someone being promoted? Is a new tax being created? Is a rule being changed?

        Identify the Actors: Who is performing the action (e.g., "O Presidente da República")? Who is being affected by the action (e.g., "Coronel Paulo Daniel Duarte Machado")?

        Identify the Justification: Find the legal basis or references (e.g., "...nos termos da alínea a) do n.º 1 do artigo 140.º do Decreto-Lei n.º 30/2017..."). Treat these as justifications, not the main topic.

        Synthesize the Summary: Combine your findings from steps 1-3 into a clear, action-oriented summary.

    FINAL OUTPUT:
    Based on your analysis, return a single, valid JSON object with the following structure. Do not include any other text.
    code JSON

        
    {
      "suggested_category_id": "...",
      "tags": [
        {"type": "person", "name": "..."},
        {"type": "organization", "name": "..."},
        {"type": "concept", "name": "..."}
      ],
      "analysis": {
        "pt": {
          "informal_summary_title": "A 5-10 word Portuguese title describing the CORE ACTION.",
          "informal_summary": "A human-centric Portuguese summary focusing on 'who did what' and the outcome. If there are conditions, use a bulleted list.",
          "cross_references": [
            {"type": "Decreto-Lei", "number": "30/2017", "article": "140", "description": "Legal basis for the decree."}
          ]
        },
        "en": { /* English translations */ }
      }
    }

      

Why This Prompt is Superior:

    The "Chain of Thought" section is the magic. It forces the AI to follow a logical process before generating its final output. It explicitly tells the AI to separate the action from the justification, which is the exact error it was making.

    A Clear Goal: The prompt starts with a high-level goal ("identify the single, core, new action"), focusing the AI on the most important task.

    Structured cross_references: We have added a description field to the cross_references. This prompts the AI to not just identify the reference, but to explain why it's relevant (e.g., "Legal basis for the decree"), providing richer data for our knowledge graph.

Part 2: 🛠️ The Implementation & Validation Plan

Objective: To integrate this new prompt and add the necessary validation steps to the pipeline.

2.1. Update the "Analyst" AI Function
Action: The Python function run_map_phase in document_analyzer.py must be updated.

    Logic: The only change is to replace the old prompt with the New "Kritis" Master Prompt (v3.2). The surrounding logic of batching and making API calls remains the same.

2.2. Update the Ingestion Logic (ingest-law)

    Action: The ingest-law function needs a small but important update.

    Logic: When it parses the AI's response to create the law_article_references records, it should now also populate the description field in that junction table (Note: you may need to add this column if it doesn't exist).

2.3. Implement a "Sanity Check" Validation Step

    Requirement: To catch these kinds of logical errors automatically before they even reach the human validator.

    Action: After the "Analyst AI" (Kritis) returns its JSON, but before it's saved to pending_ingestions, your Python script should run a quick automated check.

    Logic:

        Keyword Check: Does the informal_summary contain generic, non-specific phrases like "This decree states," "The President decrees," or "Based on the law"?

        Entity Check: Does the informal_summary mention at least one of the key_entities that the AI also identified in the tags section? (e.g., the summary should probably mention "Paulo Daniel Duarte Machado").

        Flagging: If a summary fails these checks, it can be automatically flagged for priority human review with a note like "AI summary may be too generic."

This refined plan directly addresses the AI's failure mode. By forcing the AI to follow a structured thought process and separating the core action from its legal justification, you will get consistently high-quality, human-centric, and truly "informal" summaries that fulfill the mission of the Agora platform.