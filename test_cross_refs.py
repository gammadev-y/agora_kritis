#!/usr/bin/env python3
"""Test cross-reference extraction manually"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

# Test content with a reference
test_content = """
O conselho diretivo da Agência para a Integração, Migrações e Asilo, I. P. (AIMA, I. P.), é composto por um presidente e quatro vogais, nomeados para um mandato de cinco anos, renovável uma vez por igual período, de entre indivíduos com reconhecida idoneidade, competência técnica, aptidão, experiência profissional e formação adequadas ao exercício das respetivas funções, nos termos dos n.os 1 e 5 do artigo 5.º da respetiva orgânica, aprovada em anexo ao [Decreto-Lei n.º 41/2023](https://diariodarepublica.pt/dr/detalhe/decreto-lei/41-2023-213881448 "Decreto-Lei n.º 41/2023"), de 2 de junho, do n.º 1 do artigo 20.º da Lei-Quadro dos Institutos Públicos, aprovada pela [Lei n.º 3/2004](https://diariodarepublica.pt/dr/detalhe/lei/3-2004-603478 "Lei n.º 3/2004"), de 15 de janeiro, na sua redação atual, e do artigo 3.º do anexo I à [Lei n.º 71/2007](https://diariodarepublica.pt/dr/detalhe/decreto-lei/71-2007-518057 "Lei n.º 71/2007"), de 27 de março, na sua redação atual.
"""

analysis_prompt = f"""
You are "Kritis," an expert legal analyst. Deconstruct the provided legal article into a single, valid JSON object (no other text). Follow the CRITICAL INSTRUCTIONS strictly.

CRITICAL INSTRUCTIONS:
- Meticulously identify all references to other legal articles or laws. References may appear as hyperlinks (<a> tags) or as phrases like "n.º X do artigo Y" or "Decreto-Lei n.º Z".
- References are in Markdown format: [Law Name](URL "Title")
- For each reference, extract:
    - relationship (e.g., "cites", "amends", "revokes", "references_internal")
    - type (e.g., "Decreto-Lei", "Lei", "Decreto Legislativo Regional")
    - number (e.g., "41/2023", "3/2004")
    - article_number (if present, e.g., "5.º")
    - url (must be the href if present; for internal references with only article numbers, set url to null)
- If a reference is internal (e.g., "nos termos do n.º 2"), mark url: null.

ARTICLE TEXT TO ANALYZE:
{test_content}

OUTPUT:
Return one valid JSON object only, with this structure:

{{
    "tags": {{
        "person": [],
        "organization": [],
        "concept": []
    }},
    "analysis": {{
        "pt": {{
            "informal_summary_title": "",
            "informal_summary": ""
        }},
        "en": {{
            "informal_summary_title": "",
            "informal_summary": ""
        }}
    }},
    "cross_references": [
        {{
            "relationship": "cites",
            "type": "Decreto-Lei",
            "number": "41/2023",
            "article_number": "5.º",
            "url": "https://diariodarepublica.pt/dr/detalhe/decreto-lei/41-2023-213881448"
        }}
    ]
}}
"""

print("=== Sending prompt to AI ===\n")
response = model.generate_content(analysis_prompt)
print("=== AI Response ===\n")
print(response.text)

# Try to parse
try:
    text = response.text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.endswith('```'):
        text = text[:-3]
    
    result = json.loads(text)
    print("\n=== Parsed JSON ===\n")
    print(json.dumps(result, indent=2))
    
    print(f"\n=== Cross-references found: {len(result.get('cross_references', []))} ===")
    for ref in result.get('cross_references', []):
        print(json.dumps(ref, indent=2))
        
except Exception as e:
    print(f"\n❌ Error parsing: {e}")
