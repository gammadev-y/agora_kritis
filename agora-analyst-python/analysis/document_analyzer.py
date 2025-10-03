"""
Document Analyzer - Core logic for the Map-Reduce analysis pipeline.
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """AI-powered document analyzer using Map-Reduce workflow."""

    def __init__(self):
        """Initialize the analyzer with Supabase client and Gemini API."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()  # For operations needing admin access
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_source(self, source_id: str):
        """
        Main orchestrator for analyzing a source document.

        Args:
            source_id: UUID of the source to analyze
        """
        logger.info(f"Starting analysis for source {source_id}")

        # Validate source_id
        try:
            uuid.UUID(source_id)
        except ValueError:
            raise ValueError(f"Invalid source UUID: {source_id}")

        # Build context package
        context_package = self.build_context_package(source_id)
        logger.info("Context package built")

        # Get document chunks
        chunks = self._get_document_chunks(source_id)
        if not chunks:
            logger.warning(f"No document chunks found for source {source_id}")
            return

        logger.info(f"Found {len(chunks)} chunks to analyze")

        # Run map phase
        map_results = asyncio.run(self.run_map_phase(chunks, context_package))
        logger.info(f"Map phase completed for {len(map_results)} chunks")

        # Run reduce phase
        reduce_results = self.run_reduce_phase(map_results)
        logger.info("Reduce phase completed")

        # Save to database
        self.save_analysis_to_db(source_id, map_results, reduce_results)
        logger.info("Analysis saved to database")

    def build_context_package(self, source_id: str) -> str:
        """
        Build the RAG context package for the source.

        Args:
            source_id: UUID of the source

        Returns:
            str: Formatted context string
        """
        context_parts = []

        # Get source info
        try:
            source_response = self.supabase.table('sources').select('*').eq('id', source_id).execute()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise ValueError(f"Unable to access database tables. Please ensure the 'agora' schema tables are properly set up in Supabase. Error: {e}")
        
        if not source_response.data:
            raise ValueError(f"Source {source_id} not found in database")
        
        source = source_response.data[0]

        context_parts.append(f"Source Title: {source.get('title', 'Unknown')}")
        context_parts.append(f"Source Type: {source.get('type_id', 'Unknown')}")

        # Get document chunks content to scan for references
        chunks = self._get_document_chunks(source_id)
        full_content = ' '.join([chunk['content'] for chunk in chunks])

        # Scan for law references (simple pattern: "Lei" followed by number or name)
        law_references = self._extract_law_references(full_content)

        if law_references:
            # Fetch summaries of referenced laws
            referenced_laws = self._get_law_summaries(law_references)
            if referenced_laws:
                context_parts.append("Referenced Laws:")
                for law in referenced_laws:
                    context_parts.append(f"- {law['title']}: {law.get('summary', 'No summary available')}")

        # Vector search for similar promises/actions
        similar_items = self._find_similar_promises_actions(full_content)
        if similar_items:
            context_parts.append("Similar Promises/Actions:")
            for item in similar_items:
                item_type = "Promise" if 'promise_text' in item or 'translations' in item else "Action"
                # Extract text from translations
                translations = item.get('translations', {})
                text = ""
                if isinstance(translations, dict):
                    # Try Portuguese first, then English
                    text = translations.get('pt', {}).get('description', '') or \
                           translations.get('en', {}).get('description', '') or \
                           str(translations)
                else:
                    text = item.get('promise_text', item.get('description', ''))
                context_parts.append(f"- {item_type}: {text[:200]}...")

        return '\n\n'.join(context_parts)

    def _get_document_chunks(self, source_id: str) -> List[Dict]:
        """Get all document chunks for a source."""
        logger.info(f"Querying chunks for source {source_id}")
        try:
            response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).execute()
            logger.info(f"Chunk query response: {len(response.data) if response.data else 0} chunks found")
            if response.data:
                for i, chunk in enumerate(response.data):
                    logger.info(f"Chunk {i}: ID={chunk['id']}, length={len(chunk.get('content', ''))}")
            return response.data or []
        except Exception as e:
            logger.error(f"Could not fetch document chunks: {e}")
            return []

    def _extract_law_references(self, content: str) -> List[str]:
        """Extract potential law references from content."""
        # Simple regex patterns for Portuguese law references
        patterns = [
            r'Lei\s+(?:n[º°]?\s*)?(\d+(?:/\d{4})?)',  # Lei 123/2023
            r'Lei\s+([A-Z][a-z]+)',  # Lei Penal
            r'Código\s+([A-Z][a-z]+)',  # Código Civil
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))  # Remove duplicates

    def _get_law_summaries(self, law_references: List[str]) -> List[Dict]:
        """Get summaries of referenced laws."""
        summaries = []
        for ref in law_references[:5]:  # Limit to 5 references
            # Try to match by number or title
            if re.match(r'\d+', ref):
                # Numeric law
                response = self.supabase.table('laws').select('title,summary').ilike('title', f'%{ref}%').limit(1).execute()
            else:
                # Title-based
                response = self.supabase.table('laws').select('title,summary').ilike('title', f'%{ref}%').limit(1).execute()

            if response.data:
                summaries.extend(response.data)

        return summaries

    def _find_similar_promises_actions(self, content: str) -> List[Dict]:
        """Find top 3 semantically similar promises/actions using vector search."""
        # This assumes a search_index table with vectors
        # For simplicity, we'll do a basic text search instead
        # In production, this would use pgvector similarity search

        # Search promises
        promises = self.supabase.table('promises').select('translations').limit(3).execute()

        # Search government actions
        actions = self.supabase.table('government_actions').select('translations').limit(3).execute()

        return (promises.data or []) + (actions.data or [])

    async def run_map_phase(self, chunks: List[Dict], context_package: str) -> List[Dict]:
        """
        Run the map phase: analyze each chunk individually.

        Args:
            chunks: List of document chunks
            context_package: Context string

        Returns:
            List of analysis results
        """
        async def analyze_chunk(chunk: Dict) -> Dict:
            """Analyze a single chunk."""
            map_prompt = f"""
Você é um analista jurídico especializado em legislação brasileira.

CONTEXTO GERAL:
{context_package}

TEXTO PARA ANÁLISE:
{chunk['content']}

INSTRUÇÕES:
Analise o texto acima e forneça:
1. Um resumo conciso em português (máximo 200 palavras)
2. O ponto-chave mais importante em português
3. Tags sugeridas (separadas por vírgula)

Responda APENAS com um objeto JSON válido:
{{
    "summary_pt": "resumo aqui",
    "key_takeaway_pt": "ponto chave aqui",
    "suggested_tags": "tag1, tag2, tag3"
}}
"""

            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self._call_gemini, map_prompt
                )

                # Extract JSON from response (might be wrapped in markdown)
                json_text = response.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:]
                if json_text.endswith('```'):
                    json_text = json_text[:-3]
                json_text = json_text.strip()

                result = json.loads(json_text)
                result['chunk_id'] = chunk['id']
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for chunk {chunk['id']}: {e}, response: {response[:500]}")
                return {
                    'chunk_id': chunk['id'],
                    'summary_pt': 'Erro na análise - resposta inválida',
                    'key_takeaway_pt': 'Erro na análise - resposta inválida',
                    'suggested_tags': ''
                }
            except Exception as e:
                logger.error(f"Error analyzing chunk {chunk['id']}: {e}")
                return {
                    'chunk_id': chunk['id'],
                    'summary_pt': 'Erro na análise',
                    'key_takeaway_pt': 'Erro na análise',
                    'suggested_tags': ''
                }

        # Process chunks with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Limit concurrent API calls

        async def limited_analyze(chunk):
            async with semaphore:
                await asyncio.sleep(1)  # Rate limiting
                return await analyze_chunk(chunk)

        tasks = [limited_analyze(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        return results

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with prompt."""
        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            else:
                logger.error(f"Empty response from Gemini API")
                return "{}"
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "{}"

    def run_reduce_phase(self, map_results: List[Dict]) -> Dict:
        """
        Run the reduce phase: combine results into final summary.

        Args:
            map_results: Results from map phase

        Returns:
            Dict with final summary and translation
        """
        # Concatenate all summaries
        all_summaries = '\n\n'.join([r['summary_pt'] for r in map_results])

        reduce_prompt = f"""
Você é um analista jurídico. Combine os seguintes resumos parciais em um único resumo informal e abrangente em português:

RESUMOS PARCIAIS:
{all_summaries}

INSTRUÇÕES:
- Crie um resumo narrativo e informal
- Mantenha o foco nos aspectos mais importantes
- Máximo 500 palavras
- Use linguagem acessível

Responda APENAS com o resumo em português.
"""

        informal_summary_pt = self._call_gemini(reduce_prompt)

        # Translate to English
        translate_prompt = f"""
Traduza o seguinte texto do português para o inglês, mantendo o tom informal:

{informal_summary_pt}

Responda APENAS com a tradução em inglês.
"""

        informal_summary_en = self._call_gemini(translate_prompt)

        return {
            'informal_summary_pt': informal_summary_pt,
            'informal_summary_en': informal_summary_en
        }

    def save_analysis_to_db(self, source_id: str, map_results: List[Dict], reduce_results: Dict):
        """
        Save analysis results to the database.

        Args:
            source_id: Source UUID
            map_results: Map phase results
            reduce_results: Reduce phase results
        """
        # Update source with final summary in translations field
        translations = {
            'pt': {
                'informal_summary': reduce_results['informal_summary_pt']
            },
            'en': {
                'informal_summary': reduce_results['informal_summary_en']
            }
        }

        self.supabase_admin.table('sources').update({
            'translations': translations
        }).eq('id', source_id).execute()

        # Update law_article_versions with translations and tags
        for result in map_results:
            # Assuming chunks link to law_article_versions
            # This might need adjustment based on actual schema
            chunk = self.supabase_admin.table('document_chunks').select('id').eq('id', result['chunk_id']).execute()
            if chunk.data:
                # Find corresponding law_article_version
                # This is a simplification - actual mapping might be different
                version_response = self.supabase_admin.table('law_article_versions').select('id').limit(1).execute()
                if version_response.data:
                    version_id = version_response.data[0]['id']

                    # Translate key takeaway
                    translate_takeaway = f"Translate to English: {result['key_takeaway_pt']}"
                    key_takeaway_en = self._call_gemini(translate_takeaway)

                    self.supabase_admin.table('law_article_versions').update({
                        'summary_pt': result['summary_pt'],
                        'summary_en': self._call_gemini(f"Translate to English: {result['summary_pt']}"),
                        'key_takeaway_pt': result['key_takeaway_pt'],
                        'key_takeaway_en': key_takeaway_en
                    }).eq('id', version_id).execute()

                    # Add tags (this might need a separate tags relationship)
                    if result['suggested_tags']:
                        tags = [tag.strip() for tag in result['suggested_tags'].split(',')]
                        for tag in tags:
                            # Insert or get tag
                            tag_response = self.supabase_admin.table('tags').select('id').eq('name', tag).execute()
                            if not tag_response.data:
                                tag_response = self.supabase_admin.table('tags').insert({'name': tag}).select('id').execute()

                            if tag_response.data:
                                # Link tag to version (assuming law_article_version_tags table)
                                self.supabase_admin.table('law_article_version_tags').insert({
                                    'version_id': version_id,
                                    'tag_id': tag_response.data['id']
                                }).execute()