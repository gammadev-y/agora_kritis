"""
Kritis V6.0 - Production Analyst with Local Translation & Token-Aware Reduce

Key improvements in V6.0:
- AI only analyzes in Portuguese (source language)
- Local translation (argos-translate + googletrans fallback) reduces API costs
- Token-aware Reduce phase for law summaries
- Enhanced AI persona with style guide and few-shot examples
- Multilingual tag aggregation with proper noun preservation
"""

import json
import logging
import os
import re
import uuid
import unicodedata
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client
from lib.translator import translate_text, translate_analysis_object, translate_tags

load_dotenv()
logger = logging.getLogger(__name__)

class KritisAnalyzerV6:
    """Kritis V6.0 - Production Analyst with efficiency and cost optimizations."""

    def __init__(self):
        """Initialize Kritis V6.0 with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.model_version = 'gemini-2.0-flash-exp'
        
        # Token limit for model (use safe limit)
        self.model_token_limit = 1_000_000
        self.safe_token_limit = 800_000  # Leave margin for response
        
        # Category master list for final categorization
        self.category_master_list = [
            'CONSTITUTIONAL', 'FISCAL', 'LABOR', 'HEALTH', 'ENVIRONMENTAL', 
            'JUDICIAL', 'ADMINISTRATIVE', 'CIVIL', 'CRIMINAL', 'SOCIAL_SECURITY'
        ]
    
    # ========================================
    # STAGE 1: ENHANCED EXTRACTOR (unchanged from v5.0)
    # ========================================
    
    def run_enhanced_extractor_phase(self, source_id: str) -> Dict[str, Any]:
        """Stage 1: Extract preamble and articles."""
        logger.info(f"🔄 Kritis V6.0 Stage 1: Enhanced Extractor for source {source_id}")
        
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
        
        # Store in pending_extractions table
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
        
        # Extract law type and number
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
    # STAGE 2: KRITIS V6.0 MAP PHASE (Portuguese-only analysis)
    # ========================================
    
    def run_kritis_v6_map_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 2: Map Phase - Analyze each article in Portuguese only.
        Translation happens locally in Stage 3.
        """
        logger.info(f"🧠 Kritis V6.0 Stage 2: Map Phase (PT-only analysis) for source {source_id}")
        
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
            logger.info("🔍 Analyzing preamble (PT-only)...")
            try:
                preamble_analysis = self._analyze_content_v6_map_with_retry(
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
            logger.info(f"🔍 Analyzing {article.get('article_number', f'Article {i+1}')} (PT-only)...")
            try:
                article_analysis = self._analyze_content_v6_map_with_retry(
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
        
        # Delete existing and insert
        self.supabase_admin.table('source_ai_analysis').delete().eq('source_id', source_id).eq('model_version', 'kritis_v6_map').execute()
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': 'kritis_v6_map',
            'analysis_data': analysis_data
        }).execute()
        
        logger.info(f"✅ Map Phase completed: {successful_analyses}/{total_items} items")
        
        return {
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'completion_rate': (successful_analyses / total_items * 100) if total_items > 0 else 0
        }
    
    def _analyze_content_v6_map_with_retry(self, content: str, content_type: str, article_number: Optional[str] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Wrapper for _analyze_content_v6_map with exponential backoff for rate limit errors.
        """
        import time
        
        for attempt in range(max_retries):
            try:
                return self._analyze_content_v6_map(content, content_type, article_number)
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a 429 rate limit error
                if '429' in error_str and attempt < max_retries - 1:
                    # Extract retry delay from error if available
                    retry_delay = 10  # Default 10 seconds
                    if 'retry_delay' in error_str or 'seconds:' in error_str:
                        delay_match = re.search(r'seconds:\s*(\d+)', error_str)
                        if delay_match:
                            retry_delay = int(delay_match.group(1))
                    
                    logger.warning(f"⚠️ Rate limit hit (429), retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                
                # For other errors or final attempt, re-raise
                raise
        
        # Should not reach here, but just in case
        raise Exception("Max retries exceeded")
    
    def _analyze_content_v6_map(self, content: str, content_type: str, article_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Kritis V6.0 Map Phase Prompt - Portuguese-only analysis.
        
        Returns structure:
        {
            "tags": {"person": [...], "organization": [...], "concept": [...]},
            "informal_summary_title": "Título em Português",
            "informal_summary": "Resumo em Português",
            "cross_references": [...]
        }
        """
        
        analysis_prompt = f"""
És "Kritis", um analista jurídico especializado. Analisa o seguinte artigo legal português.

REQUISITOS DE IDIOMA:
- Toda a análise DEVE ser em Português de Portugal (pt-pt)

GUIA DE ESTILO (CRÍTICO):
- **Linguagem Simples**: Usa palavras do dia-a-dia. Evita jargão jurídico completamente.
- **Estrutura Concisa**: Usa pontos de marcação (-) para desdobrar condições, regras ou listas.
- **Tom Útil e Humano**: Explica conceitos claramente, como a um amigo que não percebe jargão.
- **Sem Introduções**: NUNCA começas um resumo com frases como "Este artigo trata de" ou "Em resumo". Vai direto à ação e objetivo central.
- **Orientado para a Ação**: Foca no que acontece, quem é afetado, e as consequências práticas.

EXEMPLO DE RESUMO PERFEITO:
"O limite de idade para cargos públicos é ignorado se:
- Tiver tido serviço prévio contínuo ao estado;
- As interrupções de serviço não tiverem sido por sua culpa e duraram menos de 60 dias."

REFERÊNCIAS CRUZADAS:
- Identifica meticulosamente todas as referências a outros artigos ou leis
- Para cada referência, extrai:
    - relationship (e.g., "cites", "amends", "revokes", "references_internal")
    - type (tipo de documento)
    - number (número oficial)
    - article_number (se presente)
    - url (href do tag <a> se presente; null para referências internas)

TAGS:
- Identifica pessoas, organizações e conceitos únicos mencionados
- Tudo em português

TEXTO DO ARTIGO:
{content}

SAÍDA:
Retorna um único objeto JSON válido com esta estrutura EXATA:

{{
    "tags": {{
        "person": ["nome da pessoa"],
        "organization": ["nome da organização"],
        "concept": ["conceito chave"]
    }},
    "informal_summary_title": "Título conciso orientado para a ação em português",
    "informal_summary": "Resumo breve e centrado no ser humano que segue o guia de estilo em português",
    "cross_references": [
        {{
            "relationship": "cites",
            "type": "Decreto",
            "number": "19478",
            "article_number": "14.º",
            "url": "https://diariodarepublica.pt/dr/detalhe/decreto/19478-1931-211983"
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
            
            # Validate structure
            if 'tags' not in analysis:
                analysis['tags'] = {"person": [], "organization": [], "concept": []}
            if 'cross_references' not in analysis:
                analysis['cross_references'] = []
            if 'informal_summary_title' not in analysis:
                analysis['informal_summary_title'] = ""
            if 'informal_summary' not in analysis:
                analysis['informal_summary'] = ""
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ V6 Map analysis failed: {e}")
            return {
                "tags": {"person": [], "organization": [], "concept": []},
                "informal_summary_title": "",
                "informal_summary": "",
                "cross_references": []
            }
    
    # ========================================
    # STAGE 3: KNOWLEDGE GRAPH BUILDER WITH LOCAL TRANSLATION
    # ========================================
    
    def run_knowledge_graph_builder_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 3: Build knowledge graph with local translation.
        
        Workflow:
        1. Create parent law record
        2. For each article:
           - Translate PT analysis to bilingual format (local)
           - Insert into law_articles
           - Process cross-references
        3. Aggregate and translate tags (local)
        4. Generate final law summary with token-aware Reduce
        """
        logger.info(f"🔗 Kritis V6.0 Stage 3: Knowledge Graph Builder for source {source_id}")
        
        # Check if law already exists and delete
        existing_law_response = self.supabase_admin.table('laws').select('id').eq('source_id', source_id).execute()
        if existing_law_response.data:
            existing_law_id = existing_law_response.data[0]['id']
            logger.warning(f"⚠️ Law already exists, deleting {existing_law_id}...")
            try:
                self.supabase_admin.rpc('delete_law_by_law_id', {'p_law_id': existing_law_id}).execute()
                logger.info(f"🗑️ Deleted existing law")
            except Exception as e:
                logger.error(f"❌ Failed to delete existing law: {e}")
                raise
        
        # Get extraction and analysis data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', 'kritis_v6_map').order('created_at', desc=True).limit(1).execute()
        
        if not extraction_response.data or not analysis_response.data:
            raise ValueError(f"Missing extraction or analysis data for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        analysis_data = analysis_response.data[0]['analysis_data']
        
        # Step 1: Create parent law record
        law_id = self._create_parent_law_v6(source_id, extraction_data)
        
        # Get law enactment date
        law_response = self.supabase_admin.table('laws').select('enactment_date').eq('id', law_id).execute()
        law_enactment_date = law_response.data[0]['enactment_date'] if law_response.data else None
        
        # Step 2: Process articles with local translation
        try:
            relationships_created = self._process_articles_with_translation_v6(
                law_id, 
                law_enactment_date,
                extraction_data, 
                analysis_data
            )
            
            # Step 3: Aggregate tags and translate locally
            self._aggregate_and_translate_tags_v6(law_id, analysis_data)
            
            # Step 4: Generate final law summary with token-aware Reduce
            self._generate_final_law_summary_v6(law_id, analysis_data)
            
        except Exception as e:
            logger.error(f"❌ Error processing law {law_id}: {e}")
            raise
        
        logger.info(f"✅ Knowledge graph built: {relationships_created['law_relationships']} law relationships, {relationships_created['article_references']} article references")
        
        return {
            'law_id': law_id,
            'relationships_created': relationships_created
        }
    
    def _create_parent_law_v6(self, source_id: str, extraction_data: Dict[str, Any]) -> str:
        """Create parent law record (reuses v5.0 logic)."""
        metadata = extraction_data.get('metadata', {})
        
        # Get source data
        source_response = self.supabase_admin.table('sources').select('translations, published_at, main_url').eq('id', source_id).execute()
        source_translations = {}
        source_published_at = None
        source_main_url = None
        if source_response.data:
            source_translations = source_response.data[0].get('translations', {})
            source_published_at = source_response.data[0].get('published_at')
            source_main_url = source_response.data[0].get('main_url')
        
        government_entity_id = '3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f'
        
        # Extract official_title
        official_title = 'Untitled Law'
        if 'pt' in source_translations:
            pt_data = source_translations['pt']
            if isinstance(pt_data, dict):
                pt_title = pt_data.get('title', '')
            else:
                pt_title = str(pt_data)
            
            if pt_title:
                official_title = re.sub(r'[#$@&*]', '', pt_title).strip()
                logger.info(f"📋 Using official_title: {official_title}")
        
        # Extract official_number
        official_number = self._extract_official_number_v6(source_id, metadata, source_translations)
        
        # Extract enactment_date with fallback
        enactment_date = metadata.get('enactment_date')
        if not enactment_date and source_published_at:
            if isinstance(source_published_at, str):
                enactment_date = source_published_at.split('T')[0]
            logger.info(f"📅 Using published_at as enactment_date: {enactment_date}")
        
        # Determine law type
        if official_number == 'CRP':
            type_id = 'CONSTITUTION'
            logger.info(f"📜 Detected CRP, setting type_id to CONSTITUTION")
        else:
            type_id = self._map_law_type(metadata.get('type', 'Lei'))
        
        law_data = {
            'id': str(uuid.uuid4()),
            'source_id': source_id,
            'government_entity_id': government_entity_id,
            'official_number': official_number,
            'slug': self._generate_slug(official_title),
            'type_id': type_id,
            'category_id': 'ADMINISTRATIVE',  # Updated by Reduce phase
            'enactment_date': enactment_date,
            'official_title': official_title,
            'translations': {},
            'tags': {}
        }
        
        if source_main_url:
            law_data['url'] = source_main_url
        
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        law_id = response.data[0]['id']
        
        logger.info(f"📜 Created law: {law_id}, number: {official_number}")
        
        return law_id
    
    def _extract_official_number_v6(self, source_id: str, metadata: Dict[str, Any], source_translations: Dict[str, Any]) -> str:
        """Extract official_number (reuses v5.0 logic)."""
        # Special case: CRP
        if 'pt' in source_translations:
            pt_data = source_translations['pt']
            pt_title = pt_data.get('title', '') if isinstance(pt_data, dict) else str(pt_data)
            
            if 'Constituição da República Portuguesa' in pt_title or 'CRP' in pt_title:
                return 'CRP'
        
        # Priority 1: isolated number from last chunk
        try:
            chunks_response = self.supabase_admin.table('document_chunks').select('content').eq('source_id', source_id).order('chunk_index', desc=True).limit(1).execute()
            if chunks_response.data:
                last_chunk = chunks_response.data[0]['content']
                isolated_numbers = re.findall(r'\b(\d{6,})\b', last_chunk)
                if isolated_numbers:
                    return max(isolated_numbers, key=len)
        except Exception as e:
            logger.warning(f"⚠️ Could not extract from last chunk: {e}")
        
        # Priority 2: law type + nº + numbers from pt title
        if 'pt' in source_translations:
            pt_data = source_translations['pt']
            pt_title = pt_data.get('title', '') if isinstance(pt_data, dict) else str(pt_data)
            
            if pt_title:
                law_type = metadata.get('type', 'Lei')
                law_type_pt = self._get_law_type_pt_translation(law_type)
                numbers_in_title = re.findall(r'\d+[-/]\d{4}(?:-[A-Z])?|\d{4,}', pt_title)
                if numbers_in_title:
                    return f"{law_type_pt} nº {numbers_in_title[0]}"
        
        # Priority 3: metadata
        official_number = metadata.get('official_number', '')
        if official_number:
            return official_number
        
        # Fallback
        return source_id[:8]
    
    def _get_law_type_pt_translation(self, law_type: str) -> str:
        """Get Portuguese translation of law type."""
        type_mapping_pt = {
            'DECRETO_LEI': 'Decreto-Lei',
            'LEI': 'Lei',
            'LEI_CONSTITUCIONAL': 'Lei Constitucional',
            'LEI_ORGANICA': 'Lei Orgânica',
            'DECRETO': 'Decreto',
            'PORTARIA': 'Portaria',
            'RESOLUCAO': 'Resolução',
        }
        
        if law_type in type_mapping_pt.values():
            return law_type
        
        return type_mapping_pt.get(law_type, 'Lei')
    
    def _generate_slug(self, official_title: str) -> str:
        """Generate URL-safe slug."""
        normalized = unicodedata.normalize('NFKD', official_title)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[^\w\s-]', '', ascii_text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:150].rstrip('-')
    
    def _map_law_type(self, type_str: str) -> str:
        """Map law type string to type_id."""
        type_mapping = {
            'Decreto-Lei': 'DECRETO_LEI',
            'Lei': 'LEI',
            'Lei Constitucional': 'LEI_CONSTITUCIONAL',
            'Lei Orgânica': 'LEI_ORGANICA',
            'Decreto': 'DECRETO',
            'Portaria': 'PORTARIA',
            'Resolução': 'RESOLUCAO',
        }
        return type_mapping.get(type_str, 'OTHER')
    
    def _process_articles_with_translation_v6(
        self,
        law_id: str,
        law_enactment_date: Optional[str],
        extraction_data: Dict[str, Any],
        analysis_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Process articles with local translation and relationship linking."""
        articles = extraction_data.get('articles', [])
        analysis_results = analysis_data.get('analysis_results', [])
        
        law_relationships_count = 0
        article_references_count = 0
        
        # Process each article
        for analysis_item in analysis_results:
            if analysis_item['content_type'] != 'article':
                continue
            
            article_order = analysis_item['article_order']
            article_number = analysis_item.get('article_number', f"Artigo {article_order}.º")
            analysis = analysis_item['analysis']
            
            # Skip articles with empty/failed analysis (e.g., from rate limit errors)
            pt_title = analysis.get('informal_summary_title', '').strip()
            pt_summary = analysis.get('informal_summary', '').strip()
            
            if not pt_title and not pt_summary:
                logger.warning(f"⚠️ Skipping article {article_order} - empty analysis (likely rate limit error)")
                continue
            
            # Find corresponding article text
            article_idx = article_order - 1
            official_text = ""
            if 0 <= article_idx < len(articles):
                official_text = articles[article_idx].get('official_text', '')
            
            # Translate analysis locally
            logger.info(f"🌍 Translating article {article_order} locally...")
            pt_analysis = {
                'informal_summary_title': pt_title,
                'informal_summary': pt_summary
            }
            translations = translate_analysis_object(pt_analysis)
            
            # Create article record
            article_id = str(uuid.uuid4())
            article_data = {
                'id': article_id,
                'law_id': law_id,
                'article_order': article_order,
                'mandate_id': "50259b5a-054e-4bbf-a39d-637e7d1c1f9f",
                'status_id': "ACTIVE",
                'valid_from': law_enactment_date,
                'valid_to': None,
                'official_text': official_text,
                'tags': analysis.get('tags', {}),
                'translations': translations,
                'cross_references': analysis.get('cross_references', [])
            }
            
            self.supabase_admin.table('law_articles').insert(article_data).execute()
            
            # Process cross-references
            stats = self._process_and_link_references(
                article_id,
                law_id,
                law_enactment_date,
                analysis.get('cross_references', [])
            )
            
            law_relationships_count += stats['law_relationships']
            article_references_count += stats['article_references']
        
        # Process preamble references
        for analysis_item in analysis_results:
            if analysis_item['content_type'] == 'preamble':
                analysis = analysis_item['analysis']
                cross_refs = analysis.get('cross_references', [])
                if cross_refs:
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
        """Process preamble references (law-to-law only)."""
        law_relationships = 0
        
        for ref in cross_references:
            try:
                if not ref.get('url') and not ref.get('number'):
                    continue
                
                target_law = self._find_target_law(ref.get('url'), ref.get('number'))
                if not target_law:
                    continue
                
                relationship = ref.get('relationship', 'cites')
                
                try:
                    self.supabase_admin.table('law_relationships').insert({
                        'source_law_id': source_law_id,
                        'target_law_id': target_law['id'],
                        'relationship_type': relationship.upper()
                    }).execute()
                    law_relationships += 1
                except Exception as e:
                    logger.debug(f"Law relationship exists or failed: {e}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to process preamble reference: {e}")
        
        return {'law_relationships': law_relationships}
    
    def _process_and_link_references(
        self,
        source_article_id: str,
        source_law_id: str,
        source_enactment_date: Optional[str],
        cross_references: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Process and link cross-references."""
        law_relationships = 0
        article_references = 0
        
        for ref in cross_references:
            try:
                relationship = ref.get('relationship', 'cites')
                ref_url = ref.get('url')
                ref_number = ref.get('number')
                ref_article_number = ref.get('article_number')
                
                if not ref_url and not ref_number:
                    continue
                
                target_law = self._find_target_law(ref_url, ref_number)
                if not target_law:
                    continue
                
                target_law_id = target_law['id']
                
                # Create law-to-law relationship
                try:
                    self.supabase_admin.table('law_relationships').insert({
                        'source_law_id': source_law_id,
                        'target_law_id': target_law_id,
                        'relationship_type': relationship.upper()
                    }).execute()
                    law_relationships += 1
                except Exception as e:
                    logger.debug(f"Law relationship exists: {e}")
                
                # Create article-to-article relationship
                if ref_article_number:
                    target_article_id = self._find_target_article(target_law_id, ref_article_number)
                    if target_article_id:
                        try:
                            self.supabase_admin.table('law_article_references').insert({
                                'source_article_id': source_article_id,
                                'target_article_id': target_article_id,
                                'reference_type': relationship.upper()
                            }).execute()
                            article_references += 1
                            
                            if relationship in ['amends', 'revokes'] and source_enactment_date:
                                self._update_target_article_status(
                                    target_article_id,
                                    relationship,
                                    source_enactment_date
                                )
                        except Exception as e:
                            logger.debug(f"Article reference exists: {e}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to process reference: {e}")
        
        return {
            'law_relationships': law_relationships,
            'article_references': article_references
        }
    
    def _find_target_law(self, url: Optional[str], number: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find target law by URL or number."""
        try:
            if url:
                slug_match = re.search(r'/([^/]+)$', url)
                if slug_match:
                    slug = slug_match.group(1)
                    response = self.supabase_admin.table('laws').select('id, enactment_date').eq('slug', slug).execute()
                    if response.data:
                        return response.data[0]
            
            if number:
                response = self.supabase_admin.table('laws').select('id, enactment_date').eq('official_number', number).execute()
                if response.data:
                    return response.data[0]
            
            return None
        except Exception as e:
            logger.debug(f"Error finding target law: {e}")
            return None
    
    def _find_target_article(self, target_law_id: str, article_number: str) -> Optional[str]:
        """Find target article by law_id and article_number."""
        try:
            order_match = re.search(r'(\d+)', article_number)
            if not order_match:
                return None
            
            article_order = int(order_match.group(1))
            response = self.supabase_admin.table('law_articles').select('id').eq('law_id', target_law_id).eq('article_order', article_order).eq('status_id', 'ACTIVE').execute()
            
            if response.data:
                return response.data[0]['id']
            
            return None
        except Exception as e:
            logger.debug(f"Error finding target article: {e}")
            return None
    
    def _update_target_article_status(
        self,
        target_article_id: str,
        relationship: str,
        source_enactment_date: str
    ) -> None:
        """Update target article status when superseded or revoked."""
        try:
            if relationship == 'revokes':
                new_status = 'REVOKED'
            elif relationship == 'amends':
                new_status = 'SUPERSEDED'
            else:
                return
            
            enactment = datetime.fromisoformat(source_enactment_date).date()
            valid_to = (enactment - timedelta(days=1)).isoformat()
            
            self.supabase_admin.table('law_articles').update({
                'status_id': new_status,
                'valid_to': valid_to
            }).eq('id', target_article_id).execute()
            
            logger.info(f"📝 Updated article {target_article_id} to {new_status}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update article status: {e}")
    
    def _aggregate_and_translate_tags_v6(self, law_id: str, analysis_data: Dict[str, Any]) -> None:
        """Aggregate tags from articles and translate locally."""
        articles_response = self.supabase_admin.table('law_articles').select('tags').eq('law_id', law_id).execute()
        
        # Aggregate Portuguese tags
        aggregated_tags_pt = {
            'person': [],
            'organization': [],
            'concept': []
        }
        
        unique_tags_pt = {
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
                                if tag and tag not in unique_tags_pt[category]:
                                    unique_tags_pt[category].add(tag)
                                    aggregated_tags_pt[category].append(tag)
        
        # Translate tags locally
        logger.info(f"🌍 Translating tags locally...")
        multilingual_tags = translate_tags(aggregated_tags_pt)
        
        # Update law with multilingual tags
        self.supabase_admin.table('laws').update({
            'tags': multilingual_tags
        }).eq('id', law_id).execute()
        
        logger.info(f"📊 Aggregated and translated tags: {len(aggregated_tags_pt['person'])} persons, {len(aggregated_tags_pt['organization'])} orgs, {len(aggregated_tags_pt['concept'])} concepts")
    
    # ========================================
    # STAGE 4: TOKEN-AWARE REDUCE PHASE
    # ========================================
    
    def _generate_final_law_summary_v6(self, law_id: str, analysis_data: Dict[str, Any]) -> None:
        """
        Generate final law summary with token-aware Reduce phase.
        
        Steps:
        1. Gather all article summaries (Portuguese)
        2. Count tokens
        3. If under limit: single Reduce call
        4. If over limit: batch pre-summarization, then final Reduce
        5. Translate final summary locally
        6. Update law with translations and category_id
        """
        logger.info(f"📚 Kritis V6.0: Token-aware Reduce Phase for law {law_id}")
        
        # Gather Portuguese article summaries
        articles_response = self.supabase_admin.table('law_articles').select('translations, article_order').eq('law_id', law_id).order('article_order').execute()
        
        article_summaries_pt = []
        for article in articles_response.data:
            if article.get('translations'):
                translations = article['translations']
                if isinstance(translations, dict):
                    pt_data = translations.get('pt', {})
                    if isinstance(pt_data, dict):
                        pt_summary = pt_data.get('informal_summary', '').strip()
                        if pt_summary:
                            # Sanitize for JSON: remove control characters
                            pt_summary_clean = pt_summary.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                            # Collapse multiple spaces
                            pt_summary_clean = re.sub(r'\s+', ' ', pt_summary_clean).strip()
                            article_summaries_pt.append(f"Artigo {article.get('article_order', '?')}: {pt_summary_clean}")
        
        if not article_summaries_pt:
            logger.warning("⚠️ No article summaries found for Reduce phase")
            return
        
        # Combine summaries
        combined_summaries = "\n\n".join(article_summaries_pt)
        
        # Count tokens (rough estimate: 1 token ≈ 4 chars for Portuguese)
        estimated_tokens = len(combined_summaries) // 4
        logger.info(f"📊 Estimated tokens: {estimated_tokens:,}")
        
        # Token-aware processing
        if estimated_tokens < self.safe_token_limit:
            # Single Reduce call
            logger.info("✅ Under token limit, single Reduce call")
            final_summary_pt = self._run_reduce_prompt_v6(combined_summaries)
        else:
            # Batch pre-summarization
            logger.info(f"⚠️ Over token limit, using batch pre-summarization")
            final_summary_pt = self._run_batched_reduce_v6(article_summaries_pt)
        
        if not final_summary_pt:
            logger.warning("⚠️ Reduce phase failed")
            return
        
        # Translate final summary locally
        logger.info("🌍 Translating final summary locally...")
        final_translations = translate_analysis_object(final_summary_pt)
        
        # Extract category suggestion
        suggested_category = final_summary_pt.get('suggested_category_id', 'ADMINISTRATIVE')
        
        # Update law
        self.supabase_admin.table('laws').update({
            'translations': final_translations,
            'category_id': suggested_category
        }).eq('id', law_id).execute()
        
        logger.info(f"✅ Final law summary generated and translated, category: {suggested_category}")
    
    def _run_reduce_prompt_v6(self, combined_summaries: str) -> Optional[Dict[str, Any]]:
        """Run single Reduce prompt for law summary."""
        reduce_prompt = f"""
És "Kritis", um editor jurídico especializado. Dadas as análises de artigos individuais, sintetiza um único resumo de alto nível.

GUIA DE ESTILO:
- Linguagem simples e clara
- Pontos de marcação para estrutura
- Tom útil e humano
- Sem introduções - direto ao conteúdo
- Foca no propósito geral e impactos principais da lei

RESUMOS DOS ARTIGOS (Português):
{combined_summaries}

CATEGORIAS DISPONÍVEIS:
{', '.join(self.category_master_list)}

Retorna um único objeto JSON válido:

{{
    "suggested_category_id": "A melhor categoria desta lista",
    "informal_summary_title": "Título conciso para toda a lei",
    "informal_summary": "Resumo de alto nível sobre o propósito e os principais impactos da lei (3-5 parágrafos)"
}}
"""
        
        try:
            response = self.model.generate_content(reduce_prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Remove literal control characters that break JSON parsing
            # These can appear in AI-generated summaries
            import re
            response_text = re.sub(r'[\x00-\x1f\x7f]', ' ', response_text)
            
            result = json.loads(response_text)
            
            # Extract final_analysis if nested
            if 'final_analysis' in result:
                analysis = result['final_analysis']
                analysis['suggested_category_id'] = result.get('suggested_category_id', 'ADMINISTRATIVE')
                return analysis
            
            return result
        except Exception as e:
            logger.error(f"❌ Reduce prompt failed: {e}")
            return None
    
    def _run_batched_reduce_v6(self, article_summaries: List[str]) -> Optional[Dict[str, Any]]:
        """Run batched Reduce for large laws."""
        # Split into batches that fit token limit
        batch_size = 50  # Approximately safe batch size
        batches = [article_summaries[i:i + batch_size] for i in range(0, len(article_summaries), batch_size)]
        
        logger.info(f"📦 Split into {len(batches)} batches")
        
        # Pre-summarize each batch
        pre_summaries = []
        for i, batch in enumerate(batches):
            logger.info(f"🔄 Pre-summarizing batch {i+1}/{len(batches)}...")
            batch_text = "\n\n".join(batch)
            
            pre_prompt = f"""
Sintetiza estes artigos de lei num resumo conciso (1-2 parágrafos):

{batch_text}

Retorna apenas o texto do resumo, sem JSON.
"""
            try:
                response = self.model.generate_content(pre_prompt)
                pre_summary = response.text.strip()
                pre_summaries.append(f"Lote {i+1}: {pre_summary}")
            except Exception as e:
                logger.error(f"❌ Batch {i+1} pre-summarization failed: {e}")
        
        # Final Reduce on pre-summaries
        if pre_summaries:
            logger.info("🔄 Running final Reduce on pre-summaries...")
            combined_pre_summaries = "\n\n".join(pre_summaries)
            return self._run_reduce_prompt_v6(combined_pre_summaries)
        
        return None
