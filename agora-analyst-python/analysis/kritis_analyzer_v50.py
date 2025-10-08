"""
Kritis V5.0 - Enhanced Relationship Processing with Knowledge Graph Builder
Implementation of LawArticleRelationships.md specifications.

This analyzer implements relationship consistency improvements:
- Extracts URLs and article numbers from cross-references
- Builds comprehensive knowledge graph with law-to-law and article-to-article links
- Handles internal references (article numbers only) vs external references (with URLs)
- Validates temporal consistency (laws can only amend/revoke earlier laws)
- Updates article status when superseded or revoked
"""

import json
import logging
import os
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)

class KritisAnalyzerV50:
    """Kritis V5.0 - Enhanced Relationship Processing implementing LawArticleRelationships.md."""

    def __init__(self):
        """Initialize Kritis V5.0 with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = 'gemini-2.0-flash'
        
        # Category master list for final categorization
        self.category_master_list = [
            'CONSTITUTIONAL', 'FISCAL', 'LABOR', 'HEALTH', 'ENVIRONMENTAL', 
            'JUDICIAL', 'ADMINISTRATIVE', 'CIVIL', 'CRIMINAL', 'SOCIAL_SECURITY'
        ]
    
    # ========================================
    # STAGE 1: ENHANCED EXTRACTOR
    # ========================================
    
    def run_enhanced_extractor_phase(self, source_id: str) -> Dict[str, Any]:
        """Stage 1: Extract preamble and articles."""
        logger.info(f"🔄 Kritis V5.0 Stage 1: Enhanced Extractor for source {source_id}")
        
        # Get document chunks
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        if not chunks_response.data:
            raise ValueError(f"No document chunks found for source {source_id}")
        
        chunks = chunks_response.data
        
        # Combine all chunk content
        full_text = "".join(chunk['content'] + "\n\n" for chunk in chunks)
        
        # Extract metadata from first chunk
        first_chunk_text = chunks[0]['content']
        metadata = self._extract_metadata(first_chunk_text)
        
        # Extract preamble and articles
        extraction_result = self._extract_preamble_and_articles(full_text)
        
        # Store extraction results
        extracted_data = {
            "preamble_text": extraction_result["preamble_text"],
            "articles": extraction_result["articles"],
            "metadata": metadata,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "total_articles": len(extraction_result["articles"]),
            "has_preamble": bool(extraction_result["preamble_text"].strip())
        }
        
        # Store in pending_extractions table (delete existing first to handle re-runs)
        self.supabase_admin.table('pending_extractions').delete().eq('source_id', source_id).execute()
        self.supabase_admin.table('pending_extractions').insert({
            'source_id': source_id,
            'status': 'COMPLETED',
            'extracted_data': extracted_data
        }).execute()
        
        logger.info(f"✅ Extraction completed: {len(extraction_result['articles'])} articles")
        
        return {
            'total_articles': len(extraction_result['articles']),
            'has_preamble': bool(extraction_result['preamble_text'].strip()),
            'metadata': metadata
        }
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract law metadata from text."""
        metadata = {}
        
        # Extract law type and number with expanded pattern to catch more document types
        # Pattern matches common Portuguese legal document formats
        type_pattern = r'((?:Decreto-Lei|Lei Constitucional|Lei Orgânica|Lei|Decreto Legislativo Regional|Decreto Regional|Decreto Regulamentar Regional|Decreto Regulamentar|Decreto do Governo|Decreto do Presidente da República|Decreto|Portaria|Resolução da Assembleia da República|Resolução do Conselho de Ministros|Resolução|Despacho Conjunto|Despacho Normativo|Despacho|Aviso do Banco de Portugal|Aviso|Acórdão do Tribunal Constitucional|Acórdão do Supremo Tribunal de Justiça|Acórdão do Supremo Tribunal Administrativo|Acórdão do Tribunal de Contas|Acórdão doutrinário|Acórdão|Regulamento|Regimento|Convenção|Tratado|Acordo|Protocolo))\s+n\.?º?\s*(\d+[-/]\d+(?:-[A-Z])?)'
        type_match = re.search(type_pattern, text, re.IGNORECASE)
        if type_match:
            metadata['type'] = type_match.group(1).strip()
            metadata['official_number'] = type_match.group(2).strip()
        
        # Extract date
        date_pattern = r'de\s+(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})'
        date_match = re.search(date_pattern, text, re.IGNORECASE)
        if date_match:
            months = {
                'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
            }
            day = int(date_match.group(1))
            month = months.get(date_match.group(2).lower(), 1)
            year = int(date_match.group(3))
            metadata['enactment_date'] = f"{year:04d}-{month:02d}-{day:02d}"
        
        # Extract title
        title_pattern = r'^(.+?)(?=\n|$)'
        title_match = re.search(title_pattern, text.strip())
        if title_match:
            metadata['official_title'] = title_match.group(1).strip()
        
        return metadata
    
    def _extract_preamble_and_articles(self, full_text: str) -> Dict[str, Any]:
        """Extract preamble and articles using AI."""
        extraction_prompt = f"""
Extract the preamble and articles from this legal document. Return ONLY valid JSON.

{{
  "preamble_text": "The full preamble text (everything before Article 1)",
  "articles": [
    {{"article_number": "Artigo 1.º", "official_text": "Full text including <a> tags"}},
    {{"article_number": "Artigo 2.º", "official_text": "Full text including <a> tags"}}
  ]
}}

DOCUMENT:
{full_text[:8000]}
"""
        
        try:
            response = self.model.generate_content(extraction_prompt)
            extraction_text = response.text.strip()
            
            # Clean response
            if extraction_text.startswith('```json'):
                extraction_text = extraction_text[7:]
            if extraction_text.endswith('```'):
                extraction_text = extraction_text[:-3]
            
            result = json.loads(extraction_text)
            
            # Validate structure
            if 'preamble_text' not in result:
                result['preamble_text'] = ""
            if 'articles' not in result:
                result['articles'] = []
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return {"preamble_text": "", "articles": []}
    
    # ========================================
    # STAGE 2: KRITIS V5.0 ANALYST WITH ENHANCED CROSS-REFERENCES
    # ========================================
    
    def run_kritis_v50_analyst_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 2: Analyze each article with Kritis V5.0 Master Prompt.
        
        Extracts highly structured cross-reference information including:
        - relationship type (cites, amends, revokes, references_internal)
        - type, number, article_number
        - url (href from <a> tags or null for internal refs)
        """
        logger.info(f"🧠 Kritis V5.0 Stage 2: Enhanced Analyst for source {source_id}")
        
        # Get extraction data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        if not extraction_response.data:
            raise ValueError(f"No extraction data found for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        
        analysis_results = []
        total_items = 0
        successful_analyses = 0
        
        # Analyze preamble if exists
        if extraction_data.get('preamble_text', '').strip():
            logger.info("🔍 Analyzing preamble...")
            try:
                preamble_analysis = self._analyze_content_v50(
                    content=extraction_data['preamble_text'],
                    content_type="preamble"
                )
                analysis_results.append({
                    'content_type': 'preamble',
                    'article_order': 0,
                    'analysis': preamble_analysis
                })
                successful_analyses += 1
            except Exception as e:
                logger.error(f"❌ Preamble analysis failed: {e}")
            total_items += 1
        
        # Analyze each article
        articles = extraction_data.get('articles', [])
        for i, article in enumerate(articles):
            logger.info(f"🔍 Analyzing {article.get('article_number', f'Article {i+1}')}...")
            try:
                article_analysis = self._analyze_content_v50(
                    content=article['official_text'],
                    content_type="article",
                    article_number=article.get('article_number', f"Artigo {i+1}.º")
                )
                analysis_results.append({
                    'content_type': 'article',
                    'article_order': i + 1,
                    'article_number': article.get('article_number'),
                    'analysis': article_analysis
                })
                successful_analyses += 1
            except Exception as e:
                logger.error(f"❌ Article {i+1} analysis failed: {e}")
            total_items += 1
        
        # Store analysis results
        analysis_data = {
            'source_id': source_id,
            'analysis_results': analysis_results,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'completion_rate': (successful_analyses / total_items * 100) if total_items > 0 else 0
        }
        
        # Delete existing and insert (to handle re-runs)
        self.supabase_admin.table('source_ai_analysis').delete().eq('source_id', source_id).eq('model_version', 'kritis_v50_enhanced_relationships').execute()
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': 'kritis_v50_enhanced_relationships',
            'analysis_data': analysis_data
        }).execute()
        
        logger.info(f"✅ Analysis completed: {successful_analyses}/{total_items} items")
        
        return {
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'completion_rate': (successful_analyses / total_items * 100) if total_items > 0 else 0
        }
    
    def _analyze_content_v50(self, content: str, content_type: str, article_number: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content using Kritis V5.0 Master Prompt with enhanced cross-references."""
        
        # The Kritis V5.0 Master Prompt from LawArticleRelationships.md
        analysis_prompt = f"""
You are "Kritis," an expert legal analyst. Deconstruct the provided legal article into a single, valid JSON object (no other text). Follow the CRITICAL INSTRUCTIONS strictly.

CRITICAL INSTRUCTIONS:
- Meticulously identify all references to other legal articles or laws. References may appear as hyperlinks (<a> tags) or as phrases like "n.º X do artigo Y" or "Decreto-Lei n.º Z".
- For each reference, extract:
    - relationship (e.g., "cites", "amends", "revokes", "references_internal")
    - type (e.g., "Decreto", "Lei", "Decreto-Lei")
    - number
    - article_number (if present)
    - url (must be the href if present; for internal references with only article numbers, set url to null)
- If a reference is internal (e.g., "nos termos do n.º 2"), mark url: null.

ARTICLE TEXT TO ANALYZE:
{content}

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
            "type": "Decreto",
            "number": "19478",
            "article_number": "14.º",
            "url": "https://diariodarepublica.pt/dr/detalhe/decreto/19478-1931-211983"
        }},
        {{
            "relationship": "references_internal",
            "article_number": "2",
            "url": null
        }}
    ]
}}
"""
        
        try:
            response = self.model.generate_content(analysis_prompt)
            analysis_text = response.text.strip()
            
            # Clean response
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text[7:]
            if analysis_text.endswith('```'):
                analysis_text = analysis_text[:-3]
            
            analysis = json.loads(analysis_text)
            
            # Validate and normalize structure
            if 'tags' not in analysis:
                analysis['tags'] = {"person": [], "organization": [], "concept": []}
            if 'cross_references' not in analysis:
                analysis['cross_references'] = []
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ V5.0 analysis failed: {e}")
            return {
                "tags": {"person": [], "organization": [], "concept": []},
                "analysis": {"pt": {"informal_summary_title": "", "informal_summary": ""}, "en": {"informal_summary_title": "", "informal_summary": ""}},
                "cross_references": []
            }
    
    # ========================================
    # STAGE 3: KNOWLEDGE GRAPH BUILDER
    # ========================================
    
    def run_knowledge_graph_builder_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 3: Build knowledge graph with enhanced relationship processing.
        
        Transaction flow:
        1. Check if source already has a law (delete if exists)
        2. Create parent law record
        3. For each article:
           - Insert into law_articles with cross_references JSONB
           - Call process_and_link_references() immediately
        4. Aggregate tags
        5. Commit transaction
        """
        logger.info(f"🔗 Kritis V5.0 Stage 3: Knowledge Graph Builder for source {source_id}")
        
        # STEP 0: Check if law already exists for this source_id and delete if so
        existing_law_response = self.supabase_admin.table('laws').select('id').eq('source_id', source_id).execute()
        if existing_law_response.data:
            existing_law_id = existing_law_response.data[0]['id']
            logger.warning(f"⚠️ Law already exists for source {source_id}. Deleting via delete_law_and_children()...")
            try:
                self.supabase_admin.rpc('delete_law_and_children', {'p_law_id': existing_law_id}).execute()
                logger.info(f"🗑️ Deleted existing law {existing_law_id}")
            except Exception as e:
                logger.error(f"❌ Failed to delete existing law: {e}")
                raise
        
        # Get extraction and analysis data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        
        if not extraction_response.data or not analysis_response.data:
            raise ValueError(f"Missing extraction or analysis data for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        analysis_data = analysis_response.data[0]['analysis_data']
        
        # Step 1: Create parent law record
        law_id = self._create_parent_law_v50(source_id, extraction_data)
        law_enactment_date = extraction_data.get('metadata', {}).get('enactment_date')
        
        # Step 2-3: Process articles and aggregate tags with retry logic
        max_retries = 1
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Step 2: Process articles with immediate relationship linking
                relationships_created = self._process_articles_with_relationships_v50(
                    law_id, 
                    law_enactment_date,
                    extraction_data, 
                    analysis_data
                )
                
                # Step 3: Aggregate tags
                self._aggregate_tags_v50(law_id)
                
                # Success - break out of retry loop
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Error processing articles for law {law_id} (attempt {retry_count}/{max_retries + 1}): {e}")
                
                if retry_count <= max_retries:
                    logger.info(f"🔄 Deleting law {law_id} and retrying...")
                    try:
                        self.supabase_admin.rpc('delete_law_and_children', {'p_law_id': law_id}).execute()
                        logger.info(f"🗑️ Deleted law {law_id} for retry")
                        
                        # Recreate the law record
                        law_id = self._create_parent_law_v50(source_id, extraction_data)
                        logger.info(f"📜 Recreated law record: {law_id}")
                        
                    except Exception as delete_error:
                        logger.error(f"❌ Failed to delete law for retry: {delete_error}")
                        raise e  # Re-raise original error
                else:
                    logger.error(f"❌ All retry attempts failed for law {law_id}")
                    raise e  # Re-raise the last error
        
        logger.info(f"✅ Knowledge graph built: {relationships_created['law_relationships']} law relationships, {relationships_created['article_references']} article references")
        
        return {
            'law_id': law_id,
            'relationships_created': relationships_created
        }
    
    def _create_parent_law_v50(self, source_id: str, extraction_data: Dict[str, Any]) -> str:
        """Create parent law record and return law_id."""
        metadata = extraction_data.get('metadata', {})
        
        # Get source translations
        source_response = self.supabase_admin.table('sources').select('translations').eq('id', source_id).execute()
        source_translations = {}
        if source_response.data:
            source_translations = source_response.data[0].get('translations', {})
        
        # Hardcode Portugal government entity ID for analysis
        government_entity_id = '3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f'
        
        # Extract official_title from sources.translations.pt, clean special characters
        official_title = 'Untitled Law'
        if 'pt' in source_translations:
            pt_title = source_translations['pt']
            # Remove # and other unwanted characters
            official_title = re.sub(r'[#$@&*]', '', pt_title).strip()
            logger.info(f"📋 Using official_title from sources.translations.pt: {official_title}")
        
        # Extract official_number with new logic
        official_number = self._extract_official_number_v50(source_id, metadata, source_translations)
        
        law_data = {
            'id': str(uuid.uuid4()),
            'source_id': source_id,
            'government_entity_id': government_entity_id,
            'official_number': official_number,
            'slug': self._generate_slug(official_number),
            'type_id': self._map_law_type(metadata.get('type', 'Lei')),
            'category_id': 'ADMINISTRATIVE',  # Will be updated by synthesis
            'enactment_date': metadata.get('enactment_date'),
            'official_title': official_title,
            'translations': {},
            'tags': {}
        }
        
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        law_id = response.data[0]['id']
        
        logger.info(f"📜 Created law record: {law_id} with official_number: {official_number}")
        
        return law_id
    
    def _extract_official_number_v50(self, source_id: str, metadata: Dict[str, Any], source_translations: Dict[str, Any]) -> str:
        """Extract official_number with new logic prioritizing last document chunk."""
        
        # First priority: isolated number from last document chunk
        try:
            chunks_response = self.supabase_admin.table('document_chunks').select('content').eq('source_id', source_id).order('chunk_index', desc=True).limit(1).execute()
            if chunks_response.data:
                last_chunk = chunks_response.data[0]['content']
                # Look for isolated numbers (like "119617986") - prefer longer sequences
                isolated_numbers = re.findall(r'\b(\d{6,})\b', last_chunk)
                if isolated_numbers:
                    # Take the longest isolated number
                    official_number = max(isolated_numbers, key=len)
                    logger.info(f"📋 Extracted official_number from last chunk isolated number: {official_number}")
                    return official_number
        except Exception as e:
            logger.warning(f"⚠️ Could not extract from last chunk: {e}")
        
        # Second priority: law type (pt translation) + nº + numbers from sources.translations pt title
        if 'pt' in source_translations:
            pt_title = source_translations['pt']
            # Extract law type from metadata
            law_type = metadata.get('type', 'Lei')
            # Map to Portuguese translation
            law_type_pt = self._get_law_type_pt_translation(law_type)
            
            # Extract numbers from pt title
            numbers_in_title = re.findall(r'\d+[-/]\d{4}(?:-[A-Z])?|\d{4,}', pt_title)
            if numbers_in_title:
                # Take the first number found
                number_part = numbers_in_title[0]
                official_number = f"{law_type_pt} nº {number_part}"
                logger.info(f"📋 Constructed official_number from pt title: {official_number}")
                return official_number
        
        # Third priority: original metadata extraction
        official_number = metadata.get('official_number', '')
        if official_number:
            logger.info(f"📋 Using official_number from metadata: {official_number}")
            return official_number
        
        # Fourth priority: extract from first chunk
        try:
            chunks_response = self.supabase_admin.table('document_chunks').select('content').eq('source_id', source_id).order('chunk_index').limit(1).execute()
            if chunks_response.data:
                first_chunk = chunks_response.data[0]['content']
                match = re.search(r'(?:Decreto-Lei|Lei Constitucional|Lei Orgânica|Lei|Decreto Legislativo Regional|Decreto Regional|Decreto Regulamentar|Decreto|Portaria|Resolução|Despacho|Aviso|Acórdão|Regulamento|Tratado|Acordo)[^\d]*n\.?º?\s*(\d+[-/]\d{4}(?:-[A-Z])?)', first_chunk, re.IGNORECASE)
                if match:
                    official_number = match.group(1)
                    logger.info(f"📋 Extracted official_number from first chunk: {official_number}")
                    return official_number
        except Exception as e:
            logger.warning(f"⚠️ Could not extract from first chunk: {e}")
        
        # Final fallback
        official_number = source_id[:8]
        logger.warning(f"⚠️ Using fallback official_number: {official_number}")
        return official_number
    
    def _get_law_type_pt_translation(self, law_type: str) -> str:
        """Get Portuguese translation of law type for official_number construction."""
        # Map database IDs back to Portuguese names
        type_mapping_pt = {
            'DECRETO_LEI': 'Decreto-Lei',
            'LEI': 'Lei',
            'LEI_CONSTITUCIONAL': 'Lei Constitucional',
            'LEI_ORGANICA': 'Lei Orgânica',
            'DECRETO': 'Decreto',
            'DECRETO_LEGISLATIVO_REGIONAL': 'Decreto Legislativo Regional',
            'DECRETO_REGIONAL': 'Decreto Regional',
            'DECRETO_REGULAMENTAR': 'Decreto Regulamentar',
            'DECRETO_REGULAMENTAR_REGIONAL': 'Decreto Regulamentar Regional',
            'DECRETO_GOVERNO': 'Decreto do Governo',
            'DECRETO_PR': 'Decreto do Presidente da República',
            'DECRETO_APROVACAO_CONSTITUICAO': 'Decreto de Aprovação da Constituição',
            'PORTARIA': 'Portaria',
            'DESPACHO': 'Despacho',
            'DESPACHO_CONJUNTO': 'Despacho Conjunto',
            'DESPACHO_NORMATIVO': 'Despacho Normativo',
            'AVISO': 'Aviso',
            'AVISO_BP': 'Aviso do Banco de Portugal',
            'RESOLUCAO': 'Resolução',
            'RESOLUCAO_AR': 'Resolução da Assembleia da República',
            'RESOLUCAO_CM': 'Resolução do Conselho de Ministros',
            'ACORDAO': 'Acórdão',
            'REGULAMENTO': 'Regulamento',
            'TRATADO': 'Tratado',
            'ACORDO': 'Acordo'
        }
        
        # If law_type is already a Portuguese name, return it
        if law_type in type_mapping_pt.values():
            return law_type
        
        # Otherwise map from database ID
        return type_mapping_pt.get(law_type, 'Lei')
    
    def _generate_slug(self, official_number: str) -> str:
        """Generate URL-safe slug from official number."""
        slug = re.sub(r'[^\w\s-]', '', official_number.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return f"{slug}-{uuid.uuid4().hex[:8]}"
    
    def _map_law_type(self, type_str: str) -> str:
        """
        Map law type string to type_id using static lookup.
        This avoids database calls since law_types is static reference data.
        
        If type is not found in mapping, returns 'OTHER' as fallback.
        The Kritis prompt should already try to identify the law_type,
        so this mapping handles edge cases and variations.
        """
        # Normalize input - remove extra whitespace and convert to title case
        type_str_normalized = ' '.join(type_str.split()).strip()
        
        # Comprehensive mapping of Portuguese law types to database IDs
        # Based on complete law_types table reference data
        type_mapping = {
            # Primary law types
            'Decreto-Lei': 'DECRETO_LEI',
            'Lei': 'LEI',
            'Lei Constitucional': 'LEI_CONSTITUCIONAL',
            'Lei Orgânica': 'LEI_ORGANICA',
            
            # Decrees
            'Decreto': 'DECRETO',
            'Decreto Legislativo Regional': 'DECRETO_LEGISLATIVO_REGIONAL',
            'Decreto Regional': 'DECRETO_REGIONAL',
            'Decreto Regulamentar': 'DECRETO_REGULAMENTAR',
            'Decreto Regulamentar Regional': 'DECRETO_REGULAMENTAR_REGIONAL',
            'Decreto do Governo': 'DECRETO_GOVERNO',
            'Decreto do Presidente da República': 'DECRETO_PR',
            'Decreto de Aprovação da Constituição': 'DECRETO_APROVACAO_CONSTITUICAO',
            
            # Administrative acts
            'Portaria': 'PORTARIA',
            'Despacho': 'DESPACHO',
            'Despacho Conjunto': 'DESPACHO_CONJUNTO',
            'Despacho Normativo': 'DESPACHO_NORMATIVO',
            'Aviso': 'AVISO',
            'Aviso do Banco de Portugal': 'AVISO_BP',
            'Edital': 'EDITAL',
            'Alvará': 'ALVARA',
            
            # Resolutions
            'Resolução': 'RESOLUCAO',
            'Resolução da Assembleia da República': 'RESOLUCAO_AR',
            'Resolução do Conselho de Ministros': 'RESOLUCAO_CM',
            
            # Jurisprudence
            'Acórdão': 'ACORDAO',
            'Acórdão do Tribunal Constitucional': 'ACORDAO_TC',
            'Acórdão do Supremo Tribunal de Justiça': 'ACORDAO_STJ',
            'Acórdão do Supremo Tribunal Administrativo': 'ACORDAO_STA',
            'Acórdão do Tribunal de Contas': 'ACORDAO_T_CONTAS',
            'Acórdão doutrinário': 'ACORDAO_DOUTRINARIO',
            'Assento': 'ASSENTO',
            
            # Constitutional documents
            'Constituição': 'CONSTITUTION',
            'Carta Constitucional': 'CARTA_CONSTITUCIONAL',
            'Revisão Constitucional': 'CONSTITUTIONAL_REVISION',
            
            # International
            'Tratado': 'TRATADO',
            'Convenção': 'CONVENCAO',
            'Acordo': 'ACORDO',
            'Protocolo': 'PROTOCOLO',
            'Protocolo de acordo': 'PROTOCOLO',
            
            # Regulatory and organizational
            'Regulamento': 'REGULAMENTO',
            'Regimento': 'REGIMENTO',
            'Instrução': 'INSTRUCAO',
            'Circular': 'CIRCULAR',
            
            # Other administrative
            'Deliberação': 'DELIBERACAO',
            'Decisão': 'DECISAO',
            'Declaração': 'DECLARACAO',
            'Declaração de Retificação': 'DECLARACAO_RETIFICACAO',
            'Errata': 'ERRATA',
            'Comunicação': 'COMUNICACAO',
            'Anúncio': 'ANUNCIO',
            
            # Parliamentary and governmental
            'Moção': 'MOCAO',
            'Moção de Confiança': 'MOCAO_CONFIANCA',
            'Moção de Censura': 'MOCAO_CENSURA',
            'Parecer': 'PARECER',
            'Programa': 'PROGRAMA',
            
            # Accession and ratification
            'Carta de Adesão': 'CARTA_ADESAO',
            'Carta de Ratificação': 'CARTA_RATIFICACAO',
            'Contrato': 'CONTRATO',
            'Aditamento': 'ADITAMENTO',
            'Alteração': 'ALTERACAO',
            
            # Reference materials
            'Lista': 'LISTA',
            'Mapa': 'MAPA',
            'Mapa Oficial': 'MAPA_OFICIAL',
            
            # Case insensitive English equivalents (for compatibility)
            'Constitution': 'CONSTITUTION',
            'Decree-Law': 'DECRETO_LEI',
            'Law': 'LEI',
            'Ordinance': 'PORTARIA',
            'Resolution': 'RESOLUCAO',
            'Regulation': 'REGULAMENTO',
            'Treaty': 'TRATADO',
            'Agreement': 'ACORDO',
        }
        
        # Try exact match first
        if type_str_normalized in type_mapping:
            return type_mapping[type_str_normalized]
        
        # Try case-insensitive match
        type_str_lower = type_str_normalized.lower()
        for key, value in type_mapping.items():
            if key.lower() == type_str_lower:
                return value
        
        # Fallback to OTHER if no match found
        logger.warning(f"⚠️ Unknown law type '{type_str}', defaulting to OTHER")
        return 'OTHER'
    
    def _process_articles_with_relationships_v50(
        self, 
        law_id: str, 
        law_enactment_date: Optional[str],
        extraction_data: Dict[str, Any], 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Process articles and create relationships immediately (V5.0 logic)."""
        
        law_relationships_count = 0
        article_references_count = 0
        
        articles = extraction_data.get('articles', [])
        analysis_results = analysis_data.get('analysis_results', [])
        
        for analysis_item in analysis_results:
            content_type = analysis_item['content_type']
            article_order = analysis_item['article_order']
            analysis = analysis_item['analysis']
            
            # Skip preamble for article creation, but we'll process its cross-references later
            if content_type != 'article':
                continue
            
            # Get official text
            if article_order - 1 < len(articles):
                official_text = articles[article_order - 1]['official_text']
            else:
                official_text = f"Article {article_order} text not found"
            
            # Create law_article record with cross_references
            # Use law's enactment_date as valid_from (articles are valid from the law's enactment date)
            article_id = str(uuid.uuid4())
            article_data = {
                'id': article_id,
                'law_id': law_id,
                'article_order': article_order,
                'mandate_id': "50259b5a-054e-4bbf-a39d-637e7d1c1f9f",
                'status_id': "ACTIVE",
                'valid_from': law_enactment_date,  # Always use law's enactment date, not today
                'valid_to': None,
                'official_text': official_text,
                'tags': analysis.get('tags', {}),
                'translations': analysis.get('analysis', {}),
                'cross_references': analysis.get('cross_references', [])
            }
            
            self.supabase_admin.table('law_articles').insert(article_data).execute()
            
            # Immediately process and link references
            stats = self._process_and_link_references(
                article_id, 
                law_id, 
                law_enactment_date,
                analysis.get('cross_references', [])
            )
            
            law_relationships_count += stats['law_relationships']
            article_references_count += stats['article_references']
        
        # Process preamble cross-references (for law-to-law relationships only)
        for analysis_item in analysis_results:
            if analysis_item['content_type'] == 'preamble':
                analysis = analysis_item['analysis']
                cross_refs = analysis.get('cross_references', [])
                if cross_refs:
                    logger.info(f"🔗 Processing {len(cross_refs)} preamble cross-references...")
                    stats = self._process_preamble_references(
                        law_id, 
                        law_enactment_date,
                        cross_refs
                    )
                    law_relationships_count += stats['law_relationships']
        
        return {
            'law_relationships': law_relationships_count,
            'article_references': article_references_count
        }
    
    def _process_preamble_references(
        self,
        source_law_id: str,
        source_enactment_date: Optional[str],
        cross_references: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Process cross-references from preamble (law-to-law relationships only)."""
        
        law_relationships = 0
        
        for ref in cross_references:
            try:
                # Skip internal references (no law-to-law relationship)
                if not ref.get('url') and not ref.get('number'):
                    continue
                
                # Find target law
                target_law = self._find_target_law_v50(ref.get('url'), ref.get('number'))
                
                if not target_law:
                    continue
                
                target_law_id = target_law['id']
                target_enactment_date = target_law.get('enactment_date')
                relationship = ref.get('relationship', 'cites')
                
                # Sanity check: temporal consistency
                if relationship in ['amends', 'revokes'] and source_enactment_date and target_enactment_date:
                    if source_enactment_date < target_enactment_date:
                        logger.warning(f"⚠️ Temporal inconsistency: law {source_law_id} ({source_enactment_date}) {relationship} law {target_law_id} ({target_enactment_date})")
                
                # Create law-to-law relationship
                try:
                    self.supabase_admin.table('law_relationships').insert({
                        'source_law_id': source_law_id,
                        'target_law_id': target_law_id,
                        'relationship_type': relationship.upper()
                    }).execute()
                    
                    law_relationships += 1
                    logger.info(f"✅ Preamble law relationship: {source_law_id} -> {target_law_id} ({relationship})")
                    
                except Exception as e:
                    # Relationship might already exist
                    logger.debug(f"Law relationship exists or failed: {e}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to process preamble reference {ref}: {e}")
                continue
        
        return {'law_relationships': law_relationships}
    
    def _process_and_link_references(
        self, 
        source_article_id: str, 
        source_law_id: str, 
        source_enactment_date: Optional[str],
        cross_references: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        The Knowledge Graph Linker Function.
        
        For each reference:
        1. Find target law (priority: URL, then number)
        2. Create law-to-law relationship
        3. Create article-to-article relationship (if article_number present)
        4. Update target article status (if amends/revokes)
        """
        law_relationships = 0
        article_references = 0
        
        for ref in cross_references:
            try:
                relationship = ref.get('relationship', 'cites')
                ref_url = ref.get('url')
                ref_number = ref.get('number')
                ref_article_number = ref.get('article_number')
                
                # Skip internal-only references (they point to same law)
                if not ref_url and not ref_number:
                    continue
                
                # Find target law
                target_law = self._find_target_law_v50(ref_url, ref_number)
                
                if not target_law:
                    logger.debug(f"Target law not found for ref: {ref}")
                    continue
                
                target_law_id = target_law['id']
                target_enactment_date = target_law.get('enactment_date')
                
                # A) Insert law-to-law relationship
                try:
                    # Sanity check: temporal consistency
                    if relationship in ['amends', 'revokes'] and source_enactment_date and target_enactment_date:
                        if source_enactment_date < target_enactment_date:
                            logger.warning(f"⚠️ Temporal inconsistency: law {source_law_id} ({source_enactment_date}) {relationship} law {target_law_id} ({target_enactment_date})")
                    
                    self.supabase_admin.table('law_relationships').insert({
                        'source_law_id': source_law_id,
                        'target_law_id': target_law_id,
                        'relationship_type': relationship.upper()
                    }).execute()
                    
                    law_relationships += 1
                    logger.debug(f"✅ Law relationship: {source_law_id} -> {target_law_id} ({relationship})")
                    
                except Exception as e:
                    # Relationship might already exist
                    logger.debug(f"Law relationship exists or failed: {e}")
                
                # B) Insert article-to-article relationship (if article_number present)
                if ref_article_number:
                    target_article_id = self._find_target_article_v50(
                        target_law_id, 
                        ref_article_number
                    )
                    
                    if target_article_id:
                        try:
                            self.supabase_admin.table('law_article_references').insert({
                                'source_article_id': source_article_id,
                                'target_article_id': target_article_id,
                                'reference_type': relationship.upper()
                            }).execute()
                            
                            article_references += 1
                            logger.debug(f"✅ Article reference: {source_article_id} -> {target_article_id}")
                            
                            # C) Update target article status (if amends/revokes)
                            if relationship in ['amends', 'revokes'] and source_enactment_date:
                                self._update_target_article_status_v50(
                                    target_article_id,
                                    relationship,
                                    source_enactment_date
                                )
                            
                        except Exception as e:
                            logger.debug(f"Article reference exists or failed: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process reference {ref}: {e}")
                continue
        
        return {
            'law_relationships': law_relationships,
            'article_references': article_references
        }
    
    def _find_target_law_v50(self, url: Optional[str], number: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Find target law with priority logic:
        1. URL-based matching (parse slug from URL)
        2. Number-based matching (official_number)
        """
        try:
            # Priority 1: URL-based matching
            if url:
                # Parse slug from URL (e.g., /dr/detalhe/decreto/19478-1931-211983)
                slug_match = re.search(r'/([^/]+)$', url)
                if slug_match:
                    slug = slug_match.group(1)
                    response = self.supabase_admin.table('laws').select('id, enactment_date').eq('slug', slug).execute()
                    if response.data:
                        return response.data[0]
            
            # Priority 2: Number-based matching
            if number:
                response = self.supabase_admin.table('laws').select('id, enactment_date').eq('official_number', number).execute()
                if response.data:
                    return response.data[0]
                
                # Try partial match
                response = self.supabase_admin.table('laws').select('id, enactment_date').ilike('official_number', f'%{number}%').execute()
                if response.data:
                    return response.data[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding target law: {e}")
            return None
    
    def _find_target_article_v50(self, target_law_id: str, article_number: str) -> Optional[str]:
        """Find target article by law_id and article_number."""
        try:
            # Parse article order from number (e.g., "14.º" -> 14, "Artigo 2.º" -> 2)
            order_match = re.search(r'(\d+)', article_number)
            if not order_match:
                return None
            
            article_order = int(order_match.group(1))
            
            # Find active article with this order
            response = self.supabase_admin.table('law_articles').select('id').eq('law_id', target_law_id).eq('article_order', article_order).eq('status_id', 'ACTIVE').execute()
            
            if response.data:
                return response.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding target article: {e}")
            return None
    
    def _update_target_article_status_v50(
        self, 
        target_article_id: str, 
        relationship: str, 
        source_enactment_date: str
    ) -> None:
        """Update target article status when superseded or revoked."""
        try:
            # Determine new status
            if relationship == 'revokes':
                new_status = 'REVOKED'
            elif relationship == 'amends':
                new_status = 'SUPERSEDED'
            else:
                return
            
            # Calculate valid_to (day before source enactment)
            enactment = datetime.fromisoformat(source_enactment_date).date()
            valid_to = (enactment - timedelta(days=1)).isoformat()
            
            # Update article
            self.supabase_admin.table('law_articles').update({
                'status_id': new_status,
                'valid_to': valid_to
            }).eq('id', target_article_id).execute()
            
            logger.info(f"📝 Updated article {target_article_id} to {new_status}, valid_to: {valid_to}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to update article status: {e}")
    
    def _aggregate_tags_v50(self, law_id: str) -> None:
        """Aggregate tags from all articles to parent law."""
        # Get all tags from articles
        articles_response = self.supabase_admin.table('law_articles').select('tags').eq('law_id', law_id).execute()
        
        aggregated_tags = {
            'person': [],
            'organization': [],
            'concept': []
        }
        
        unique_tags = {
            'person': set(),
            'organization': set(),
            'concept': set()
        }
        
        for article in articles_response.data:
            if article.get('tags'):
                tags = article['tags']
                if isinstance(tags, dict):
                    for category in ['person', 'organization', 'concept']:
                        if category in tags and isinstance(tags[category], list):
                            for tag in tags[category]:
                                if tag and tag not in unique_tags[category]:
                                    unique_tags[category].add(tag)
                                    aggregated_tags[category].append(tag)
        
        # Update parent law
        self.supabase_admin.table('laws').update({
            'tags': aggregated_tags
        }).eq('id', law_id).execute()
        
        logger.info(f"📊 Aggregated tags: {len(aggregated_tags['person'])} persons, {len(aggregated_tags['organization'])} orgs, {len(aggregated_tags['concept'])} concepts")
