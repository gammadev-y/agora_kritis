"""
Kritis - The Agora AI Analyst
Advanced legal document analysis using Map-Reduce pattern with structured ingestion.
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class KritisAnalyzer:
    """Kritis - Expert legal analyst for the Agora platform."""

    def __init__(self):
        """Initialize Kritis with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = 'gemini-2.0-flash'
        
        # Token limits for managing large documents
        self.max_tokens_per_batch = 100000  # Conservative limit for Gemini
        
    # ========================================
    # STAGE 1: MAP PHASE - Per-Chunk Analysis
    # ========================================
    
    def run_map_phase(self, source_id: str) -> bool:
        """
        Stage 1: Analyze each document chunk individually.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            bool: Success status
        """
        logger.info(f"🧠 Kritis Stage 1: Starting Map Phase for source {source_id}")
        
        try:
            # Validate source_id
            uuid.UUID(source_id)
        except ValueError:
            raise ValueError(f"Invalid source UUID: {source_id}")
        
        # Get source metadata
        source_response = self.supabase_admin.table('sources').select('*').eq('id', source_id).execute()
        if not source_response.data:
            raise ValueError(f"Source {source_id} not found")
        
        source = source_response.data[0]
        logger.info(f"Processing source: {source.get('translations', {}).get('pt', {}).get('title', 'Unknown')}")
        
        # Build context package
        context_package = self.build_context_package(source_id, source)
        logger.info("Context package built successfully")
        
        # Get document chunks
        chunks = self._get_document_chunks(source_id)
        if not chunks:
            logger.warning(f"No document chunks found for source {source_id}")
            return False
            
        logger.info(f"Found {len(chunks)} chunks to analyze")
        
        # Process each chunk
        success_count = 0
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(chunks)}: {chunk['id']}")
            
            try:
                # Generate analysis
                analysis_data = self._analyze_chunk_with_kritis(chunk, context_package, source)
                
                # Add metadata to analysis_data
                analysis_data['chunk_id'] = chunk['id']
                analysis_data['chunk_index'] = chunk.get('chunk_index', i)
                
                # Store in source_ai_analysis table
                self.supabase_admin.table('source_ai_analysis').insert({
                    'source_id': source_id,
                    'model_version': self.model_version,
                    'analysis_data': analysis_data
                }).execute()
                
                success_count += 1
                logger.info(f"✅ Chunk {chunk['id']} analyzed and saved")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing chunk {chunk['id']}: {e}")
                continue
        
        logger.info(f"🎯 Map Phase completed: {success_count}/{len(chunks)} chunks analyzed successfully")
        return success_count > 0
    
    def _analyze_chunk_with_kritis(self, chunk: Dict, context_package: str, source: Dict) -> Dict:
        """Analyze a single chunk using the Kritis Master Prompt."""
        
        # Extract source metadata
        source_type = source.get('type_id', 'Unknown')
        source_translations = source.get('translations', {})
        source_title = source_translations.get('pt', {}).get('title', 'Unknown Document')
        
        # Construct the Kritis Master Prompt
        kritis_prompt = f"""You are "Kritis," an expert legal analyst for the Agora platform. Your task is to deconstruct a legal text into a clear, structured JSON object. Your tone must be neutral, factual, and action-oriented.

CRITICAL INSTRUCTIONS:
- DO NOT start any summary with phrases like "In summary" or "This text is about."
- BE CONCISE. The informal_summary_title must be a short, impactful headline.
- SEPARATE the narrative summary from the hard references.

CONTEXTUAL INFORMATION:
Document Type: {source_type}
Document Title: {source_title}
Related Database Items: {context_package}

ARTICLE TEXT TO ANALYZE:
{chunk['content']}

YOUR TASK:
Return a single, valid JSON object with the following structure. Do not include any other text in your response.

{{
  "pt": {{
    "informal_summary_title": "A very concise, 5-10 word title in Portuguese summarizing the core action of this article.",
    "informal_summary": "A brief, action-oriented summary in Portuguese explaining what this article does.",
    "key_references": [
      "A list item for each important date, legal article, or entity reference found in the text."
    ]
  }},
  "en": {{
    "informal_summary_title": "An English translation of the concise title.",
    "informal_summary": "An English translation of the action-oriented summary.",
    "key_references": [
      "An English translation of the key references."
    ]
  }}
}}"""

        # Call Gemini API
        response = self._call_gemini(kritis_prompt)
        
        # Parse and validate JSON response
        try:
            # Extract JSON from response (might be wrapped in markdown)
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            analysis_data = json.loads(json_text)
            
            # Validate required structure
            required_keys = ['pt', 'en']
            for lang in required_keys:
                if lang not in analysis_data:
                    raise ValueError(f"Missing language key: {lang}")
                
                lang_data = analysis_data[lang]
                required_subkeys = ['informal_summary_title', 'informal_summary', 'key_references']
                for key in required_subkeys:
                    if key not in lang_data:
                        raise ValueError(f"Missing key {key} in {lang}")
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from Kritis: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback structure
            return {
                "pt": {
                    "informal_summary_title": "Erro na análise",
                    "informal_summary": "Não foi possível analisar este artigo devido a erro técnico.",
                    "key_references": []
                },
                "en": {
                    "informal_summary_title": "Analysis Error",
                    "informal_summary": "Could not analyze this article due to technical error.",
                    "key_references": []
                }
            }
    
    # ==========================================
    # STAGE 2: REDUCE PHASE - Document Synthesis
    # ==========================================
    
    def run_reduce_phase(self, source_id: str) -> Dict:
        """
        Stage 2: Synthesize all chunk analyses into document-level summary.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict: Final document summary in both languages
        """
        logger.info(f"🔄 Kritis Stage 2: Starting Reduce Phase for source {source_id}")
        
        # Fetch all analysis records for this source
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).order('created_at').execute()
        
        if not analysis_response.data:
            raise ValueError(f"No analysis data found for source {source_id}")
        
        analyses = analysis_response.data
        logger.info(f"Found {len(analyses)} chunk analyses to synthesize")
        
        # Extract summaries for token management
        pt_summaries = []
        en_summaries = []
        
        for analysis in analyses:
            data = analysis['analysis_data']
            if 'pt' in data and 'informal_summary' in data['pt']:
                pt_summaries.append(data['pt']['informal_summary'])
            if 'en' in data and 'informal_summary' in data['en']:
                en_summaries.append(data['en']['informal_summary'])
        
        # Check if we need nested map-reduce for token management
        combined_pt = '\n\n'.join(pt_summaries)
        combined_en = '\n\n'.join(en_summaries)
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(combined_pt) / 4
        
        if estimated_tokens > self.max_tokens_per_batch:
            logger.info(f"Large document detected ({estimated_tokens:.0f} tokens). Using nested map-reduce.")
            combined_pt = self._nested_map_reduce(pt_summaries, 'pt')
            combined_en = self._nested_map_reduce(en_summaries, 'en')
        
        # Generate final document-level summary
        reduce_result = self._synthesize_document_summary(combined_pt, combined_en)
        
        logger.info("🎯 Reduce Phase completed successfully")
        return reduce_result
    
    def _nested_map_reduce(self, summaries: List[str], language: str) -> str:
        """Handle large documents with nested map-reduce."""
        
        # Calculate batch size to stay under token limit
        avg_summary_length = sum(len(s) for s in summaries) / len(summaries)
        summaries_per_batch = max(1, int(self.max_tokens_per_batch * 4 / avg_summary_length))
        
        # Group summaries into batches
        batches = [summaries[i:i + summaries_per_batch] for i in range(0, len(summaries), summaries_per_batch)]
        
        logger.info(f"Processing {len(batches)} batches for {language}")
        
        # Pre-reduce each batch
        batch_summaries = []
        for i, batch in enumerate(batches):
            batch_text = '\n\n'.join(batch)
            
            pre_reduce_prompt = f"""You are "Kritis," an expert legal editor. Your task is to summarize these legal article summaries into a single, coherent summary.

ARTICLE SUMMARIES TO COMBINE:
{batch_text}

YOUR TASK:
Create a single, comprehensive summary that captures the key points from all the articles above. Be concise but complete. Write in {'Portuguese' if language == 'pt' else 'English'}.

Respond with ONLY the summary text, no additional formatting."""

            batch_summary = self._call_gemini(pre_reduce_prompt)
            batch_summaries.append(batch_summary.strip())
            
            logger.info(f"Pre-reduced batch {i+1}/{len(batches)}")
            time.sleep(1)  # Rate limiting
        
        # Combine batch summaries
        return '\n\n'.join(batch_summaries)
    
    def _synthesize_document_summary(self, pt_summaries: str, en_summaries: str) -> Dict:
        """Generate final document-level summary."""
        
        # Generate Portuguese summary
        pt_reduce_prompt = f"""Você é "Kritis," um editor jurídico especialista. Aqui estão os resumos de todos os artigos de uma lei. Sua tarefa é sintetizá-los em um único título informal e resumo de alto nível para toda a lei. Capture seu propósito geral e impactos mais significativos.

RESUMOS DOS ARTIGOS:
{pt_summaries}

SUA TAREFA:
Retorne um objeto JSON válido com esta estrutura:

{{
  "informal_summary_title": "Um título conciso de 5-10 palavras capturando o propósito principal da lei",
  "informal_summary": "Um resumo abrangente explicando o que esta lei faz e seus principais impactos"
}}

Responda APENAS com o JSON, sem texto adicional."""

        pt_response = self._call_gemini(pt_reduce_prompt)
        pt_data = self._parse_json_response(pt_response, "pt")
        
        # Generate English summary
        en_reduce_prompt = f"""You are "Kritis," an expert legal editor. Here are the summaries for every article in a law. Your task is to synthesize them into a single, high-level informal_summary_title and informal_summary for the entire law. Capture its overall purpose and most significant impacts.

ARTICLE SUMMARIES:
{en_summaries}

YOUR TASK:
Return a valid JSON object with this structure:

{{
  "informal_summary_title": "A concise 5-10 word title capturing the main purpose of the law",
  "informal_summary": "A comprehensive summary explaining what this law does and its key impacts"
}}

Respond with ONLY the JSON, no additional text."""

        en_response = self._call_gemini(en_reduce_prompt)
        en_data = self._parse_json_response(en_response, "en")
        
        return {
            'pt': pt_data,
            'en': en_data
        }
    
    # ==========================================
    # STAGE 3: LAW INGESTION
    # ==========================================
    
    def ingest_law_from_analysis(self, source_id: str) -> str:
        """
        Stage 3: Create structured law records from analysis data.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            str: UUID of the created law
        """
        logger.info(f"📚 Kritis Stage 3: Starting Law Ingestion for source {source_id}")
        
        # Get the final document summary
        document_summary = self.run_reduce_phase(source_id)
        
        # Get source metadata
        source_response = self.supabase_admin.table('sources').select('*').eq('id', source_id).execute()
        if not source_response.data:
            raise ValueError(f"Source {source_id} not found")
        
        source = source_response.data[0]
        
        # Get all chunk analyses
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).order('created_at').execute()
        if not analysis_response.data:
            raise ValueError(f"No analysis data found for source {source_id}")
        
        analyses = analysis_response.data
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        chunks = chunks_response.data or []
        
        # Start transaction
        try:
            law_id = self._create_law_record(source, document_summary)
            logger.info(f"✅ Created law record: {law_id}")
            
            # Create articles and versions
            article_count = 0
            for i, (analysis, chunk) in enumerate(zip(analyses, chunks)):
                try:
                    article_id = self._create_law_article(law_id, i + 1)
                    self._create_law_article_version(article_id, chunk, analysis['analysis_data'])
                    article_count += 1
                    logger.info(f"✅ Created article {i+1} with version")
                except Exception as e:
                    logger.error(f"❌ Error creating article {i+1}: {e}")
                    continue
            
            logger.info(f"🎯 Law Ingestion completed: {law_id} with {article_count} articles")
            return law_id
            
        except Exception as e:
            logger.error(f"❌ Law ingestion failed: {e}")
            raise
    
    def _create_law_record(self, source: Dict, document_summary: Dict) -> str:
        """Create the main law record."""
        
        # Extract metadata from source
        source_translations = source.get('translations', {})
        official_title = source_translations.get('pt', {}).get('title', 'Unknown Law')
        
        # Get Portugal entity (default)
        portugal_entity = self.supabase_admin.table('government_entities').select('id').eq('name', 'Portugal').limit(1).execute()
        if not portugal_entity.data:
            raise Exception("Portugal government entity not found")
        government_entity_id = portugal_entity.data[0]['id']
        
        # Generate slug from title
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', official_title.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        slug = f"{slug}-{int(time.time())}"  # Add timestamp for uniqueness
        
        # Map source type to law type
        source_type = source.get('type_id', 'OFFICIAL_PUBLICATION')
        law_type_mapping = {
            'OFFICIAL_PUBLICATION': 'DECREE_LAW',
            'DECREE': 'DECREE_LAW', 
            'LAW': 'PARLIAMENTARY_LAW',
            'REGULATION': 'REGULATION',
            'RESOLUTION': 'RESOLUTION'
        }
        law_type = law_type_mapping.get(source_type, 'DECREE_LAW')  # Default to DECREE_LAW
        
        # Prepare law data
        law_data = {
            'government_entity_id': government_entity_id,
            'official_number': source.get('official_number', f"AUTO-{int(time.time())}"),
            'slug': slug,
            'type_id': law_type,
            'enactment_date': source.get('published_at', datetime.now().date().isoformat()),
            'official_title': official_title,
            'translations': document_summary
        }
        
        # Insert law record
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        if not response.data:
            raise Exception("Failed to create law record")
        
        return response.data[0]['id']
    
    def _create_law_article_version(self, article_id: str, chunk: Dict, analysis_data: Dict):
        """Create a law article version record."""
        
        # Get any available mandate (since we don't have created_at)
        mandate_response = self.supabase_admin.table('mandates').select('id').limit(1).execute()
        if not mandate_response.data:
            raise Exception("No mandate found")
        mandate_id = mandate_response.data[0]['id']
        
        version_data = {
            'article_id': article_id,
            'mandate_id': mandate_id,
            'status_id': 'ACTIVE',  # Use actual status from database
            'valid_from': datetime.now().date().isoformat(),
            'official_text': chunk['content'],
            'translations': analysis_data
        }
        
        response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
        if not response.data:
            raise Exception(f"Failed to create article version for {article_id}")
        
        return response.data[0]['id']
    
    def _create_law_article(self, law_id: str, article_number: int) -> str:
        """Create a law article record."""
        
        article_data = {
            'law_id': law_id,
            'article_number': str(article_number)
        }
        
        response = self.supabase_admin.table('law_articles').insert(article_data).execute()
        if not response.data:
            raise Exception(f"Failed to create article {article_number}")
        
        return response.data[0]['id']
    
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def build_context_package(self, source_id: str, source: Dict) -> str:
        """Build contextual information for analysis."""
        
        context_parts = ["CONTEXTUAL DATABASE INFORMATION:"]
        
        # Get sample promises
        try:
            promises_response = self.supabase_admin.table('promises').select('translations').limit(3).execute()
            if promises_response.data:
                context_parts.append("Related Promises:")
                for promise in promises_response.data:
                    translations = promise.get('translations', {})
                    if isinstance(translations, dict):
                        text = translations.get('pt', {}).get('description', '') or \
                               translations.get('en', {}).get('description', '') or \
                               str(translations)
                        context_parts.append(f"- {text[:150]}...")
        except Exception as e:
            logger.warning(f"Could not fetch promises for context: {e}")
        
        # Get sample government actions  
        try:
            actions_response = self.supabase_admin.table('government_actions').select('translations').limit(3).execute()
            if actions_response.data:
                context_parts.append("Related Government Actions:")
                for action in actions_response.data:
                    translations = action.get('translations', {})
                    if isinstance(translations, dict):
                        text = translations.get('pt', {}).get('description', '') or \
                               translations.get('en', {}).get('description', '') or \
                               str(translations)
                        context_parts.append(f"- {text[:150]}...")
        except Exception as e:
            logger.warning(f"Could not fetch actions for context: {e}")
        
        return '\n'.join(context_parts)
    
    def _get_document_chunks(self, source_id: str) -> List[Dict]:
        """Get all document chunks for a source."""
        logger.info(f"Fetching chunks for source {source_id}")
        try:
            response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
            logger.info(f"Found {len(response.data) if response.data else 0} chunks")
            return response.data or []
        except Exception as e:
            logger.error(f"Could not fetch document chunks: {e}")
            return []
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with error handling."""
        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            else:
                logger.error("Empty response from Gemini API")
                return "{}"
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "{}"
    
    def _parse_json_response(self, response: str, context: str = "") -> Dict:
        """Parse JSON response with fallback handling."""
        try:
            # Extract JSON from response
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error ({context}): {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback
            return {
                "informal_summary_title": "Erro na análise",
                "informal_summary": "Não foi possível processar a resposta da IA."
            }