"""
Kritis AI Analyzer Version 4.0 - Enhanced Legal Document Analysis
Implementing PROD5.md specifications for preamble handling, enriched analysis, 
and intelligent entity-driven tagging system.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tiktoken

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_admin_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class KritisAnalyzerV4:
    """
    Kritis AI Analyzer V4.0 - Enhanced Legal Document Analysis System
    
    Features:
    - Preamble extraction and handling (article 0)
    - Enriched entity extraction (people, organizations, concepts)
    - Intelligent entity-driven tagging system
    - Enhanced cross-reference analysis
    - Law-level summary generation
    """
    
    def __init__(self, model_version: str = "gemini-4.0-flash"):
        """Initialize Kritis 4.0 with enhanced capabilities."""
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = model_version  # This will be "gemini-4.0-flash" for unique versioning
        self._categories_cache = None
        self._tags_cache = None
        
        # Token management for batch processing (reduced for safety)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_tokens_per_batch = 4000  # Reduced from 6000 for better reliability
        
    def run_enhanced_extractor_with_preamble(self, source_id: str) -> Dict:
        """
        Stage 1: Enhanced Extractor with Preamble Handling
        Separates preamble (article 0) from numbered articles.
        Implements PROD5.md Part 2 specifications.
        """
        logger.info(f"🏛️ Kritis 4.0 Stage 1: Enhanced Extractor with Preamble for source {source_id}")
        
        # Get source record with translations (header data from crawler)
        source_response = self.supabase_admin.table('sources').select('id, slug, type_id, translations').eq('id', source_id).execute()
        if not source_response.data:
            raise ValueError(f"Source {source_id} not found")
        
        source_record = source_response.data[0]
        source_translations = source_record.get('translations', {})
        source_type_id = source_record.get('type_id')
        
        logger.info(f"📋 Source translations found: {bool(source_translations)}")
        if source_translations:
            pt_title = source_translations.get('pt', {}).get('title', '')
            logger.info(f"📄 Source title (PT): {pt_title[:100]}")
        
        # Get all chunks for the source
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        chunks = chunks_response.data or []
        
        if not chunks:
            raise ValueError(f"No chunks found for source {source_id}")
        
        # Store source_id for chunk-based parsing fallback
        self._current_source_id = source_id
        
        all_content = ""
        for chunk in chunks:
            all_content += chunk['content'] + "\n\n"
        
        # Extract metadata from first chunk, enhanced with source translations
        metadata = self._extract_metadata_from_content(chunks[0]['content'], source_translations, source_type_id)
        
        # Parse preamble and articles from complete content
        preamble_data = self._parse_preamble_and_articles(all_content)
        
        # Save metadata
        if metadata:
            metadata_analysis = {
                'extracted_metadata': metadata,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            self.supabase_admin.table('source_ai_analysis').insert({
                'source_id': source_id,
                'model_version': f"{self.model_version}-extractor",
                'analysis_data': metadata_analysis
            }).execute()
        
        # Save preamble and articles structure
        preamble_analysis = {
            'preamble_text': preamble_data['preamble_text'],
            'articles': preamble_data['articles'],
            'total_articles_found': len(preamble_data['articles']),
            'has_preamble': bool(preamble_data['preamble_text'].strip()),
            'parsing_timestamp': datetime.now().isoformat()
        }
        
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': f"{self.model_version}-preamble-parser",
            'analysis_data': preamble_analysis
        }).execute()
        
        total_articles = len(preamble_data['articles'])
        has_preamble = bool(preamble_data['preamble_text'].strip())
        
        logger.info(f"🎯 Enhanced Extractor with Preamble completed: {total_articles} articles + preamble")
        return {
            'metadata': metadata,
            'preamble_text': preamble_data['preamble_text'],
            'articles': preamble_data['articles'],
            'total_articles': total_articles,
            'has_preamble': has_preamble
        }
    
    def _extract_metadata_from_content(self, content: str, source_translations: Optional[Dict] = None, source_type_id: Optional[str] = None) -> Dict:
        """Extract document metadata from content, enhanced with source translations."""
        
        # Prepare context hints from source translations
        context_hints = ""
        official_title_hint = ""
        
        if source_translations:
            pt_data = source_translations.get('pt', {})
            official_title_hint = pt_data.get('title', '')
            
            if official_title_hint:
                context_hints = f"""

IMPORTANT CONTEXT FROM SOURCE METADATA:
- The official title from the document header is: "{official_title_hint}"
- This title should be used as the primary reference for official_title_pt
- Use this to determine the correct official_number and law_type_id"""
        
        # Add constitutional document detection
        type_hint = ""
        if source_type_id == "OFFICIAL_PUBLICATION" and official_title_hint:
            if any(keyword in official_title_hint.lower() for keyword in ['constituição', 'constitution', 'crp']):
                type_hint = "\n- DETECTED: This is a CONSTITUTIONAL document. Set law_type_id to 'CONSTITUTION'"
        
        extractor_prompt = f"""You are a meticulous legal document parser. Analyze the following text, which is the beginning of an official government publication. Your task is to extract the core metadata. Return a single, valid JSON object with the following structure. Do not include any other text in your response.

{{
  "official_number": "The official number of this law (e.g., 'Decreto-Lei n.º 30/2017', or 'CRP' for Constitution).",
  "official_title_pt": "The full, official title in Portuguese.",
  "law_type_id": "The ID of the law type based on the title (e.g., 'DECRETO_LEI', 'CONSTITUTION').",
  "enactment_date": "The primary date of the law in YYYY-MM-DD format. Look carefully in the document for publication dates, enactment dates, or dates mentioned in the context.",
  "summary_pt": "The text from the 'SUMÁRIO' section."
}}{context_hints}{type_hint}

IMPORTANT: Pay special attention to finding the correct enactment/publication date. Look for patterns like:
- "de 27 de Maio de 1969"
- "publicado em..."
- "datado de..."
- Any date references in the beginning or end of the document

For constitutional documents:
- Use "CRP" or similar abbreviation as official_number
- Set law_type_id to "CONSTITUTION"
- Look for dates like "2 de abril de 1976" (original constitution) or revision dates
- If no date is found in the text, use "1976-04-02" (original Portuguese Constitution date) as a reasonable default

TEXT TO ANALYZE:
{content[:8000]}"""

        response = self._call_gemini(extractor_prompt)
        
        try:
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            metadata = json.loads(json_text)
            
            # Override with source translations if official_title_pt is missing or generic
            if source_translations:
                pt_data = source_translations.get('pt', {})
                source_title = pt_data.get('title', '')
                
                # Use source title if it's more complete than AI-extracted title
                if source_title and (not metadata.get('official_title_pt') or 
                                    len(source_title) > len(metadata.get('official_title_pt', ''))):
                    logger.info(f"✨ Using source translation title: {source_title[:80]}")
                    metadata['official_title_pt'] = source_title
                    
                    # Re-detect official_number and law_type from enhanced title
                    if 'constituição' in source_title.lower() or 'crp' in source_title.lower():
                        if not metadata.get('official_number') or metadata['official_number'].startswith('AUTO-'):
                            metadata['official_number'] = 'CRP'
                        metadata['law_type_id'] = 'CONSTITUTION'
                        
                        # Set default constitution date if not found
                        if not metadata.get('enactment_date') or metadata['enactment_date'] == datetime.now().date().isoformat():
                            metadata['enactment_date'] = '1976-04-02'  # Portuguese Constitution original date
                            logger.info("📅 Using default Portuguese Constitution date: 1976-04-02")
                        
                        logger.info("🏛️ Detected CONSTITUTION from source title")
            
            # Fix law type mapping to valid database values
            law_type_mapping = {
                "DECRETO_PRESIDENTE_REPUBLICA": "DECRETO_PR",
                "DECRETO_LEI": "DECRETO_LEI",
                "LEI": "LEI",
                "RESOLUCAO": "RESOLUCAO",
                "PORTARIA": "PORTARIA",
                "DESPACHO": "DESPACHO",
                "CONSTITUTION": "CONSTITUTION"
            }
            
            if 'law_type_id' in metadata and metadata['law_type_id'] in law_type_mapping:
                metadata['law_type_id'] = law_type_mapping[metadata['law_type_id']]
            elif 'law_type_id' not in metadata or metadata['law_type_id'] not in ['CONSTITUTION', 'CONSTITUTIONAL_REVISION', 'PARLIAMENTARY_LAW', 'DECREE_LAW', 'REGULATION', 'RESOLUTION', 'INTERNATIONAL_TREATY', 'ACORDAO', 'ACORDAO_STA', 'ACORDAO_STJ', 'ACORDAO_TC', 'ACORDAO_T_CONTAS', 'ACORDAO_DOUTRINARIO', 'ACORDO', 'ADITAMENTO', 'ALTERACAO', 'ALVARA', 'ANUNCIO', 'ASSENTO', 'AVISO', 'AVISO_BP', 'CARTA_CONSTITUCIONAL', 'CARTA_ADESAO', 'CARTA_RATIFICACAO', 'CIRCULAR', 'COMUNICACAO', 'CONTRATO', 'CONVENCAO', 'DECISAO', 'DECLARACAO', 'DECLARACAO_RETIFICACAO', 'DECRETO', 'DECRETO_APROVACAO_CONSTITUICAO', 'DECRETO_GOVERNO', 'DECRETO_PR', 'DECRETO_LEGISLATIVO_REGIONAL', 'DECRETO_REGIONAL', 'DECRETO_REGULAMENTAR', 'DECRETO_REGULAMENTAR_REGIONAL', 'DECRETO_LEI', 'DELIBERACAO', 'DESPACHO', 'DESPACHO_CONJUNTO', 'DESPACHO_NORMATIVO', 'EDITAL', 'ERRATA', 'INSTRUCAO', 'JURISPRUDENCIA', 'LEI', 'LEI_CONSTITUCIONAL', 'LEI_ORGANICA', 'LISTA', 'MAPA', 'MAPA_OFICIAL', 'MOCAO', 'MOCAO_CENSURA', 'MOCAO_CONFIANCA', 'PARECER', 'PORTARIA', 'PROGRAMA', 'PROTOCOLO', 'REGIMENTO', 'REGULAMENTO', 'RESOLUCAO', 'RESOLUCAO_AR', 'RESOLUCAO_CM', 'TRATADO']:
                metadata['law_type_id'] = 'DECRETO_LEI'  # Default fallback
            
            return metadata
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from metadata extractor: {e}")
            
            # Try to use source translations in fallback
            fallback_title = "Documento Legal"
            fallback_type = "DECRETO_LEI"
            
            if source_translations:
                pt_data = source_translations.get('pt', {})
                source_title = pt_data.get('title', '')
                if source_title:
                    fallback_title = source_title
                    if 'constituição' in source_title.lower() or 'crp' in source_title.lower():
                        fallback_type = 'CONSTITUTION'
            
            return {
                "official_number": f"AUTO-{int(time.time())}",
                "official_title_pt": fallback_title,
                "law_type_id": fallback_type,
                "enactment_date": datetime.now().date().isoformat(),
                "summary_pt": "Análise não disponível"
            }
    
    def _parse_preamble_and_articles(self, content: str) -> Dict:
        """
        Parse preamble and articles using Enhanced Extractor AI.
        Implements PROD5.md Part 2 specifications.
        
        For very large documents, we use the chunk-based approach where each chunk
        is likely already a separate article.
        """
        
        # Check if content is too large (> 100k chars) - use chunk-based approach
        if len(content) > 100000:
            logger.info("Large document detected, using chunk-based parsing approach")
            return self._parse_using_chunks()
        
        parser_prompt = f"""You are a meticulous legal document parser. Your task is to identify and separate the introductory "preamble" from the numbered articles in the provided text.

CRITICAL INSTRUCTIONS:
- The preamble is all the text that comes before the first line that starts with any article pattern (Artigo 1.º, Art. 1.º, etc.)
- Identify every distinct article with patterns like:
  * "Artigo X.º" or "ARTIGO X.º"
  * "Art. X.º" or "ART. X.º" 
  * "Artigo X" or "Art. X"
- Include ALL text that belongs to each article until the next article starts
- Return a single, valid JSON object with two keys: preamble_text and articles

TEXT CHUNK TO PARSE:
{content}

YOUR TASK:
Return a JSON object with the following structure:
{{
  "preamble_text": "All the text from the beginning of the document up to the first article...",
  "articles": [
    {{ "article_number": "Art. 1.º", "official_text": "The full, verbatim text of the first article..." }},
    {{ "article_number": "Art. 2.º", "official_text": "The full, verbatim text of the second article..." }}
  ]
}}"""

        response = self._call_gemini(parser_prompt)
        
        try:
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            parsed_data = json.loads(json_text)
            
            # Validate structure
            if 'preamble_text' not in parsed_data:
                parsed_data['preamble_text'] = ''
            if 'articles' not in parsed_data:
                parsed_data['articles'] = []
            
            # Validate articles
            valid_articles = []
            for article in parsed_data.get('articles', []):
                if 'article_number' in article and 'official_text' in article:
                    if article['official_text'].strip():
                        valid_articles.append(article)
            
            parsed_data['articles'] = valid_articles
            return parsed_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from preamble parser: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Fallback to chunk-based approach
            logger.info("Falling back to chunk-based parsing approach")
            return self._parse_using_chunks()
    
    def _parse_using_chunks(self) -> Dict:
        """
        Alternative parsing approach that treats each chunk as a potential article.
        Used for very large documents or when AI parsing fails.
        """
        # Get chunks from the current source_id (we need to store this)
        if not hasattr(self, '_current_source_id'):
            logger.error("Source ID not available for chunk-based parsing")
            return {"preamble_text": "", "articles": []}
        
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', self._current_source_id).order('chunk_index').execute()
        chunks = chunks_response.data or []
        
        if not chunks:
            return {"preamble_text": "", "articles": []}
        
        # First chunk is likely preamble if it doesn't start with an article pattern
        first_chunk = chunks[0]['content']
        preamble_text = ""
        articles = []
        
        # Check if first chunk looks like a preamble (doesn't start with article pattern)
        if not re.match(r'^\s*(artigo|art\.)\s+\d+', first_chunk.lower().strip()):
            preamble_text = first_chunk
            article_chunks = chunks[1:]
        else:
            article_chunks = chunks
        
        # Process remaining chunks as articles
        for chunk in article_chunks:
            content = chunk['content'].strip()
            if not content:
                continue
                
            # Extract article number from content
            article_match = re.search(r'(artigo|art\.)\s+(\d+)', content.lower())
            if article_match:
                article_num = article_match.group(2)
                article_number = f"Artigo {article_num}.º"
            else:
                # Use chunk index as fallback
                article_number = f"Artigo {chunk['chunk_index']}.º"
            
            articles.append({
                "article_number": article_number,
                "official_text": content
            })
        
        logger.info(f"Chunk-based parsing found: {len(articles)} articles, preamble: {'Yes' if preamble_text else 'No'}")
        return {
            "preamble_text": preamble_text,
            "articles": articles
        }
    
    def run_enhanced_analyst_with_context(self, source_id: str) -> Dict:
        """
        Stage 2: Enhanced Analyst with Preamble Context
        Processes articles and preamble with enriched entity extraction.
        Implements PROD5.md Part 3 specifications.
        """
        logger.info(f"🧠 Kritis 4.0 Stage 2: Enhanced Analyst with Context for source {source_id}")
        
        # Get preamble and articles data
        preamble_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-preamble-parser").execute()
        
        if not preamble_response.data:
            raise ValueError(f"No preamble parsing data found for source {source_id}. Run enhanced extractor first.")
        
        preamble_data = preamble_response.data[0]['analysis_data']
        preamble_text = preamble_data['preamble_text']
        articles = preamble_data['articles']
        
        # Get metadata for date context
        metadata_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-extractor").execute()
        
        document_title = "Unknown Document"
        default_enactment_date = datetime.now().date().isoformat()  # Fallback
        if metadata_response.data:
            metadata = metadata_response.data[0]['analysis_data']['extracted_metadata']
            document_title = metadata.get('official_title_pt', 'Unknown Document')
            if metadata.get('enactment_date'):
                default_enactment_date = metadata['enactment_date']
        
        # Analyze preamble first (article 0)
        all_analyses = []
        if preamble_text.strip():
            logger.info("Analyzing preamble as article 0")
            preamble_analysis = self._analyze_content_with_context(
                content=preamble_text,
                article_number="0",
                document_title=document_title,
                preamble_context=preamble_text,
                is_preamble=True
            )
            all_analyses.append(preamble_analysis)
        
        # Smart batching for articles with robust error handling
        if articles:
            batches = self._create_smart_batches_v4(articles)
            logger.info(f"Created {len(batches)} batches for {len(articles)} articles")
            
            for i, batch in enumerate(batches):
                logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} articles")
                
                batch_analyses = self._analyze_article_batch_with_robust_retry(
                    batch=batch,
                    document_title=document_title,
                    preamble_context=preamble_text
                )
                all_analyses.extend(batch_analyses)
        
        # Save complete analysis results with completion tracking
        successful_analyses = 0
        failed_analyses = 0
        
        for analysis in all_analyses:
            if 'analysis' in analysis and 'pt' in analysis['analysis']:
                pt_title = analysis['analysis']['pt'].get('informal_summary_title', '')
                if 'não processado' in pt_title.lower() or 'not processed' in pt_title.lower() or 'análise não disponível' in pt_title.lower():
                    failed_analyses += 1
                else:
                    successful_analyses += 1
            else:
                failed_analyses += 1
        
        complete_analysis = {
            'analyses': all_analyses,
            'total_items_analyzed': len(all_analyses),
            'successful_analyses': successful_analyses,
            'failed_analyses': failed_analyses,
            'completion_rate': round((successful_analyses / len(all_analyses)) * 100, 2) if all_analyses else 0,
            'has_preamble_analysis': bool(preamble_text.strip()),
            'batches_processed': len(batches) if articles else 0,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': f"{self.model_version}-enhanced-analyst",
            'analysis_data': complete_analysis
        }).execute()
        
        logger.info(f"🎯 Enhanced Analyst completed: {len(all_analyses)} items analyzed")
        return complete_analysis
    
    def _create_smart_batches_v4(self, articles: List[Dict]) -> List[List[Dict]]:
        """Create smart batches for articles (from V3 with minor updates)."""
        batches = []
        current_batch = []
        current_token_count = 0
        
        for article in articles:
            article_text = article.get('official_text', '')
            article_tokens = len(self.tokenizer.encode(article_text))
            
            if current_token_count + article_tokens > self.max_tokens_per_batch and current_batch:
                batches.append(current_batch)
                current_batch = [article]
                current_token_count = article_tokens
            else:
                current_batch.append(article)
                current_token_count += article_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _analyze_content_with_context(self, content: str, article_number: str, document_title: str, preamble_context: str, is_preamble: bool = False) -> Dict:
        """
        Analyze single content item with enhanced context.
        Implements PROD5.md Part 3 enhanced prompt.
        """
        
        # Get categories for context
        if self._categories_cache is None:
            categories_response = self.supabase_admin.table('law_categories').select('id').execute()
            self._categories_cache = [cat['id'] for cat in categories_response.data or []]
        
        categories_list = ', '.join(self._categories_cache)
        
        content_type = "preamble" if is_preamble else "article"
        
        kritis_prompt = f"""You are "Kritis," an expert analyst and communicator for the Agora platform. Your mission is to translate complex legal articles into clear, simple, and understandable explanations for the public.

YOUR STYLE GUIDE:
- Plain Language: Use simple, everyday words. Avoid legal jargon.
- Concise Structure: Use bullet points or numbered lists to break down conditions or rules.
- Human-Centric Tone: Speak directly to the reader. Make it feel conversational and easy to understand.
- No Intros: NEVER start your response with phrases like "This article is about" or "In summary." Go directly to the explanation.

EXAMPLE of a PERFECT RESPONSE:

Original Text: "Artigo 1.º - 1. O limite para o provimento em cargos públicos, fixado no artigo 4.º do Decreto n.º 16563... não é aplicável aos que antes de excederem a idade... se mantenham ao serviço sem interrupção..."

Your Output for informal_summary_pt:
```
O limite de idade para cargos públicos é ignorado se:
- Tiver tido serviço prévio contínuo ao estado; ou
- Tiver tido interrupções de menos de 60 dias que não foram por sua culpa.

Isto inclui todo o serviço prestado ao estado, como em agências autónomas ou autarquias locais.
```

CONTEXT:
- Master Category List: {categories_list}
- This {content_type.capitalize()} Belongs To: {document_title}
- Law Preamble: {preamble_context[:1000]}...

{content_type.upper()} TEXT TO ANALYZE:
{content}

YOUR TASK:
Analyze the following {content_type} text and return a single, valid JSON object. Follow the style guide and example above precisely.

RETURN JSON OBJECT:
Return a single, valid JSON object with the following structure. Do not include any other text in your response.

{{
  "article_number": "{article_number}",
  "suggested_category_id": "From the master list, choose the single best category ID for this {content_type}'s content.",
  "analysis": {{
    "pt": {{
      "informal_summary_title": "A very concise, 5-10 word action-oriented title in Portuguese.",
      "informal_summary": "A brief, human-centric summary in Portuguese that follows the style guide. Use lists and simple language.",
      "key_dates": {{
        "Enactment Date": "YYYY-MM-DD",
        "Effective Date": "YYYY-MM-DD"
      }},
      "key_entities": [
        {{"type": "person", "name": "Marcelo Rebelo de Sousa"}},
        {{"type": "organization", "name": "Secretariado da Reforma Administrativa"}},
        {{"type": "concept", "name": "assistance in sickness"}},
        {{"type": "concept", "name": "pension"}}
      ],
      "cross_references": [
        {{"type": "Decreto-Lei", "number": "26334"}},
        {{"type": "Decreto", "number": "16563"}}
      ]
    }},
    "en": {{
      "informal_summary_title": "An English translation of the concise title.",
      "informal_summary": "An English translation of the summary, maintaining the same clear, human-centric style.",
      "key_dates": {{
        "Enactment Date": "YYYY-MM-DD",
        "Effective Date": "YYYY-MM-DD"
      }},
      "key_entities": [
        {{"type": "person", "name": "Marcelo Rebelo de Sousa"}},
        {{"type": "organization", "name": "Administrative Reform Secretariat"}},
        {{"type": "concept", "name": "assistance in sickness"}},
        {{"type": "concept", "name": "pension"}}
      ],
      "cross_references": [
        {{"type": "Decree-Law", "number": "26334"}},
        {{"type": "Decree", "number": "16563"}}
      ]
    }}
  }}
}}"""

        response = self._call_gemini(kritis_prompt)
        
        try:
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            analysis_data = json.loads(json_text)
            
            # Ensure article_number is set correctly
            analysis_data['article_number'] = article_number
            
            # Validate structure
            if 'suggested_category_id' not in analysis_data:
                analysis_data['suggested_category_id'] = 'ADMINISTRATIVE'
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from enhanced analyst: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback structure
            return {
                "article_number": article_number,
                "suggested_category_id": "ADMINISTRATIVE",
                "analysis": {
                    "pt": {
                        "informal_summary_title": "Conteúdo não processado",
                        "informal_summary": "Este conteúdo não pôde ser analisado automaticamente. Consulte o texto original para mais detalhes.",
                        "key_dates": {},
                        "key_entities": [],
                        "cross_references": []
                    },
                    "en": {
                        "informal_summary_title": "Content not processed",
                        "informal_summary": "This content could not be analyzed automatically. Please refer to the original text for details.",
                        "key_dates": {},
                        "key_entities": [],
                        "cross_references": []
                    }
                }
            }
    
    def _analyze_article_batch_with_robust_retry(self, batch: List[Dict], document_title: str, preamble_context: str) -> List[Dict]:
        """
        Analyze batch of articles with robust retry logic and error handling.
        Implements multiple retry strategies to avoid analysis errors.
        """
        
        # First attempt: try the full batch
        logger.info(f"Attempt 1: Analyzing full batch of {len(batch)} articles")
        try:
            analyses = self._analyze_article_batch_with_context(batch, document_title, preamble_context)
            
            # Validate that all analyses are complete
            if self._validate_batch_analyses(analyses, batch):
                logger.info(f"✅ Full batch analysis successful")
                return analyses
            else:
                logger.warning(f"⚠️ Full batch analysis incomplete, trying smaller batches")
                
        except Exception as e:
            logger.warning(f"⚠️ Full batch analysis failed: {e}")
        
        # Second attempt: split into smaller batches (max 5 articles each)
        logger.info(f"Attempt 2: Splitting into smaller batches")
        smaller_batches = self._create_smaller_batches(batch, max_size=5)
        all_analyses = []
        
        for i, small_batch in enumerate(smaller_batches):
            logger.info(f"Processing small batch {i+1}/{len(smaller_batches)} with {len(small_batch)} articles")
            try:
                small_analyses = self._analyze_article_batch_with_context(small_batch, document_title, preamble_context)
                
                if self._validate_batch_analyses(small_analyses, small_batch):
                    all_analyses.extend(small_analyses)
                else:
                    logger.warning(f"Small batch {i+1} incomplete, trying individual articles")
                    # Fall back to individual analysis for this batch
                    individual_analyses = self._analyze_articles_individually(small_batch, document_title, preamble_context)
                    all_analyses.extend(individual_analyses)
                    
            except Exception as e:
                logger.warning(f"Small batch {i+1} failed: {e}, trying individual articles")
                # Fall back to individual analysis
                individual_analyses = self._analyze_articles_individually(small_batch, document_title, preamble_context)
                all_analyses.extend(individual_analyses)
        
        return all_analyses
    
    def _create_smaller_batches(self, articles: List[Dict], max_size: int) -> List[List[Dict]]:
        """Create smaller batches with maximum size."""
        smaller_batches = []
        for i in range(0, len(articles), max_size):
            smaller_batches.append(articles[i:i + max_size])
        return smaller_batches
    
    def _validate_batch_analyses(self, analyses: List[Dict], original_batch: List[Dict]) -> bool:
        """Validate that batch analyses are complete and correct."""
        if len(analyses) != len(original_batch):
            return False
        
        for analysis in analyses:
            # Check for error indicators
            if 'analysis' not in analysis:
                return False
            
            if 'pt' in analysis['analysis']:
                pt_title = analysis['analysis']['pt'].get('informal_summary_title', '')
                if 'não processado' in pt_title.lower() or 'not processed' in pt_title.lower():
                    return False
        
        return True
    
    def _analyze_articles_individually(self, articles: List[Dict], document_title: str, preamble_context: str) -> List[Dict]:
        """Analyze articles one by one as final fallback."""
        logger.info(f"Final attempt: Analyzing {len(articles)} articles individually")
        individual_analyses = []
        
        for article in articles:
            try:
                # Create a single-article batch
                single_batch = [article]
                analysis = self._analyze_article_batch_with_context(single_batch, document_title, preamble_context)
                
                if analysis and len(analysis) > 0:
                    individual_analyses.append(analysis[0])
                else:
                    # Create fallback analysis
                    fallback_analysis = self._create_fallback_analysis(article)
                    individual_analyses.append(fallback_analysis)
                    
            except Exception as e:
                logger.error(f"Individual analysis failed for article {article.get('article_number', 'Unknown')}: {e}")
                # Create fallback analysis
                fallback_analysis = self._create_fallback_analysis(article)
                individual_analyses.append(fallback_analysis)
        
        return individual_analyses
    
    def _create_fallback_analysis(self, article: Dict) -> Dict:
        """Create a fallback analysis structure when AI analysis fails."""
        article_number = article.get('article_number', 'Unknown')
        
        return {
            "article_number": article_number,
            "suggested_category_id": "ADMINISTRATIVE",
            "analysis": {
                "pt": {
                    "informal_summary_title": f"Artigo {article_number} - Análise não disponível",
                    "informal_summary": "A análise automática não conseguiu processar este artigo. O conteúdo original pode ser consultado diretamente.",
                    "key_dates": {},
                    "key_entities": [],
                    "cross_references": []
                },
                "en": {
                    "informal_summary_title": f"Article {article_number} - Analysis unavailable",
                    "informal_summary": "Automatic analysis could not process this article. The original content can be consulted directly.",
                    "key_dates": {},
                    "key_entities": [],
                    "cross_references": []
                }
            }
        }
    
    def _analyze_article_batch_with_context(self, batch: List[Dict], document_title: str, preamble_context: str) -> List[Dict]:
        """
        Analyze batch of articles with preamble context.
        Similar to V3 but with enhanced prompting from PROD5.md.
        """
        
        # Get categories for context
        if self._categories_cache is None:
            categories_response = self.supabase_admin.table('law_categories').select('id').execute()
            self._categories_cache = [cat['id'] for cat in categories_response.data or []]
        
        categories_list = ', '.join(self._categories_cache)
        batch_json = json.dumps(batch, ensure_ascii=False, indent=2)
        
        kritis_prompt = f"""You are "Kritis," an expert analyst and communicator for the Agora platform. Your mission is to translate complex legal articles into clear, simple, and understandable explanations for the public.

YOUR STYLE GUIDE:
- Plain Language: Use simple, everyday words. Avoid legal jargon.
- Concise Structure: Use bullet points or numbered lists to break down conditions or rules.
- Human-Centric Tone: Speak directly to the reader. Make it feel conversational and easy to understand.
- No Intros: NEVER start your response with phrases like "This article is about" or "In summary." Go directly to the explanation.

EXAMPLE of a PERFECT RESPONSE:

Original Text: "Artigo 1.º - 1. O limite para o provimento em cargos públicos, fixado no artigo 4.º do Decreto n.º 16563... não é aplicável aos que antes de excederem a idade... se mantenham ao serviço sem interrupção..."

Your Output for informal_summary_pt:
```
O limite de idade para cargos públicos é ignorado se:
- Tiver tido serviço prévio contínuo ao estado; ou
- Tiver tido interrupções de menos de 60 dias que não foram por sua culpa.

Isto inclui todo o serviço prestado ao estado, como em agências autónomas ou autarquias locais.
```

CONTEXT:
- Master Category List: {categories_list}
- This Law's Title: {document_title}
- Law Preamble: {preamble_context[:1000]}...

ARTICLES TO ANALYZE:
{batch_json}

YOUR TASK:
For each article in the input array, perform a detailed analysis following the style guide above. Return a single, valid JSON object containing one key, "analyses". This key must be an array where each object corresponds to an input article and has the following structure:

{{
  "analyses": [
    {{
      "article_number": "Art. 1.º",
      "suggested_category_id": "The single best category ID for this article.",
      "analysis": {{
        "pt": {{
          "informal_summary_title": "A very concise, 5-10 word action-oriented title in Portuguese.",
          "informal_summary": "A brief, human-centric summary in Portuguese that follows the style guide. Use lists and simple language.",
          "key_dates": {{
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          }},
          "key_entities": [
            {{"type": "person", "name": "Name of person"}},
            {{"type": "organization", "name": "Name of organization"}},
            {{"type": "concept", "name": "Important concept or term"}}
          ],
          "cross_references": [
            {{"type": "Decreto-Lei", "number": "26334"}},
            {{"type": "Decreto", "number": "16563"}}
          ]
        }},
        "en": {{
          "informal_summary_title": "An English translation of the concise title.",
          "informal_summary": "An English translation of the summary, maintaining the same clear, human-centric style.",
          "key_dates": {{
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          }},
          "key_entities": [
            {{"type": "person", "name": "Name of person"}},
            {{"type": "organization", "name": "Name of organization"}},
            {{"type": "concept", "name": "Important concept or term"}}
          ],
          "cross_references": [
            {{"type": "Decree-Law", "number": "26334"}},
            {{"type": "Decree", "number": "16563"}}
          ]
        }}
      }}
    }}
  ]
}}"""

        response = self._call_gemini(kritis_prompt)
        
        try:
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            analysis_data = json.loads(json_text)
            analyses = analysis_data.get('analyses', [])
            
            # Validate analyses match batch articles
            if len(analyses) != len(batch):
                logger.warning(f"Analysis count ({len(analyses)}) doesn't match batch size ({len(batch)})")
            
            return analyses
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from batch analyst: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback analyses
            fallback_analyses = []
            for article in batch:
                fallback_analyses.append({
                    "article_number": article.get('article_number', 'Unknown'),
                    "suggested_category_id": "ADMINISTRATIVE",
                    "analysis": {
                        "pt": {
                            "informal_summary_title": "Artigo não processado",
                            "informal_summary": "Este artigo não pôde ser analisado automaticamente. Consulte o texto original para mais informações.",
                            "key_dates": {},
                            "key_entities": [],
                            "cross_references": []
                        },
                        "en": {
                            "informal_summary_title": "Article not processed",
                            "informal_summary": "This article could not be analyzed automatically. Please refer to the original text for more information.",
                            "key_dates": {},
                            "key_entities": [],
                            "cross_references": []
                        }
                    }
                })
            return fallback_analyses
    
    def run_intelligent_knowledge_graph_builder(self, source_id: str) -> str:
        """
        Stage 3: Intelligent Knowledge Graph Builder with Enhanced Tagging
        Creates law with preamble (article 0) and implements intelligent tagging.
        Implements PROD5.md Part 4 specifications.
        """
        logger.info(f"📚 Kritis 4.0 Stage 3: Intelligent Knowledge Graph Builder for source {source_id}")
        
        # Step 1: Create the parent law
        law_id = self._create_law_from_metadata_v4(source_id)
        logger.info(f"✅ Created law record: {law_id}")
        
        # Step 2: Create articles and versions (including preamble as article 0)
        article_versions = self._create_articles_with_preamble(source_id, law_id)
        logger.info(f"✅ Created {len(article_versions)} article versions (including preamble)")
        
        # Step 3: Perform intelligent entity-driven tagging
        self._perform_intelligent_tagging(article_versions)
        logger.info(f"✅ Intelligent tagging completed")
        
        # Step 4: Perform enhanced relational linking
        self._perform_enhanced_relational_linking(article_versions)
        logger.info(f"✅ Enhanced relational linking completed")
        
        # Step 5: Generate final law-level summary (reduce phase)
        self._generate_law_level_summary(source_id, law_id, article_versions)
        logger.info(f"✅ Law-level summary completed")
        
        logger.info(f"🎯 Intelligent Knowledge Graph Builder completed: {law_id}")
        return law_id
    
    def _create_law_from_metadata_v4(self, source_id: str) -> str:
        """Create law record using extracted metadata (enhanced from V3)."""
        
        # Get extracted metadata
        metadata_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-extractor").execute()
        
        if not metadata_response.data:
            raise ValueError(f"No metadata extraction found for source {source_id}")
        
        metadata = metadata_response.data[0]['analysis_data']['extracted_metadata']
        
        # Get Portugal entity
        portugal_entity = self.supabase_admin.table('government_entities').select('id').eq('name', 'Portugal').limit(1).execute()
        if not portugal_entity.data:
            raise Exception("Portugal government entity not found")
        government_entity_id = portugal_entity.data[0]['id']
        
        # Generate slug from official_number and enactment_date (per PROD5.md)
        official_number = metadata.get('official_number', f"AUTO-{int(time.time())}")
        official_title = metadata.get('official_title_pt', official_number)  # Use official_number as fallback
        enactment_date = metadata.get('enactment_date', None)
        
        # Create slug: dl-49031-19690527 (from official_number)
        slug_base = re.sub(r'[^a-zA-Z0-9]', '-', official_number.lower())
        if enactment_date:
            date_part = enactment_date.replace('-', '')
            slug = f"{slug_base}-{date_part}"
        else:
            slug = slug_base
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Prepare law data with corrected field mapping
        law_data = {
            'government_entity_id': government_entity_id,
            'official_number': official_number,
            'official_title': official_title,  # Use official_title_pt here
            'slug': slug,
            'type_id': metadata.get('law_type_id', 'DECRETO_LEI'),
            'enactment_date': enactment_date,  # Use extracted date
            'translations': None  # Will be populated by reduce phase
        }
        
        # Insert law record
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        if not response.data:
            raise Exception("Failed to create law record")
        
        return response.data[0]['id']
    
    def _create_articles_with_preamble(self, source_id: str, law_id: str) -> List[Dict]:
        """
        Create articles including preamble as article 0.
        Enhanced from V3 to handle preamble properly.
        """
        
        # Get enhanced analyses
        analyses_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-enhanced-analyst").execute()
        
        if not analyses_response.data:
            raise ValueError(f"No enhanced analyses found for source {source_id}")
        
        all_analyses = analyses_response.data[0]['analysis_data']['analyses']
        
        # Get preamble and articles for original text matching
        preamble_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-preamble-parser").execute()
        preamble_data = preamble_response.data[0]['analysis_data']
        
        # Get metadata for date context
        metadata_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-extractor").execute()
        
        default_enactment_date = datetime.now().date().isoformat()  # Fallback
        if metadata_response.data:
            metadata = metadata_response.data[0]['analysis_data']['extracted_metadata']
            if metadata.get('enactment_date'):
                default_enactment_date = metadata['enactment_date']
        
        # Create text mapping
        text_map = {}
        if preamble_data['preamble_text'].strip():
            text_map['0'] = preamble_data['preamble_text']
        
        for article in preamble_data['articles']:
            text_map[article['article_number']] = article['official_text']
        
        # Get mandate
        mandate_response = self.supabase_admin.table('mandates').select('id').limit(1).execute()
        if not mandate_response.data:
            raise Exception("No mandate found")
        mandate_id = mandate_response.data[0]['id']
        
        article_versions = []
        
        for analysis in all_analyses:
            try:
                article_number = analysis.get('article_number', 'Unknown')
                
                # Handle article 0 (preamble) specially
                if article_number == '0':
                    clean_article_number = '0'
                else:
                    # Extract clean article number for database
                    clean_article_number = re.sub(r'[^\d]', '', article_number)
                    if not clean_article_number:
                        clean_article_number = str(len(article_versions) + 1)
                
                # Create article
                article_data = {
                    'law_id': law_id,
                    'article_number': clean_article_number
                }
                
                article_response = self.supabase_admin.table('law_articles').insert(article_data).execute()
                if not article_response.data:
                    raise Exception(f"Failed to create article {article_number}")
                
                article_id = article_response.data[0]['id']
                
                # Get original text
                original_text = text_map.get(article_number, 'Text not found')
                
                # Create version with complete analysis data
                effective_date = default_enactment_date  # Use extracted enactment date as default
                translations = {}
                
                if 'analysis' in analysis:
                    for lang in ['pt', 'en']:
                        if lang in analysis['analysis']:
                            lang_data = analysis['analysis'][lang]
                            translations[lang] = {
                                'informal_summary_title': lang_data.get('informal_summary_title', ''),
                                'informal_summary': lang_data.get('informal_summary', ''),
                                'key_dates': lang_data.get('key_dates', {}),
                                'key_entities': lang_data.get('key_entities', []),
                                'cross_references': lang_data.get('cross_references', [])
                            }
                            
                            # Extract effective date if available, otherwise use enactment date
                            if lang == 'pt' and 'key_dates' in lang_data:
                                dates = lang_data['key_dates']
                                if 'Effective Date' in dates and dates['Effective Date']:
                                    try:
                                        datetime.strptime(dates['Effective Date'], '%Y-%m-%d')
                                        effective_date = dates['Effective Date']
                                    except (ValueError, TypeError):
                                        pass
                
                version_data = {
                    'article_id': article_id,
                    'mandate_id': mandate_id,
                    'status_id': 'ACTIVE',
                    'valid_from': effective_date,
                    'official_text': original_text,
                    'translations': translations
                }
                
                version_response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
                if not version_response.data:
                    raise Exception(f"Failed to create version for article {article_number}")
                
                version_id = version_response.data[0]['id']
                
                # Store for later processing
                article_versions.append({
                    'version_id': version_id,
                    'article_id': article_id,
                    'article_number': article_number,
                    'official_text': original_text,
                    'analysis_data': analysis
                })
                
                if article_number == '0':
                    logger.info(f"✅ Created preamble as article 0")
                else:
                    logger.info(f"✅ Created article {article_number} with version")
                
            except Exception as e:
                logger.error(f"❌ Error creating article {analysis.get('article_number', 'Unknown')}: {e}")
                continue
        
        return article_versions
    
    def _perform_intelligent_tagging(self, article_versions: List[Dict]):
        """
        Perform intelligent entity-driven tagging.
        Implements PROD5.md Part 4 enhanced tagging logic.
        """
        logger.info(f"Performing intelligent tagging on {len(article_versions)} article versions")
        
        for article_version in article_versions:
            try:
                analysis_data = article_version.get('analysis_data', {})
                if 'analysis' not in analysis_data:
                    continue
                
                pt_analysis = analysis_data['analysis'].get('pt', {})
                key_entities = pt_analysis.get('key_entities', [])
                
                version_id = article_version['version_id']
                
                for entity in key_entities:
                    entity_name = entity.get('name', '').strip()
                    entity_type = entity.get('type', 'concept').strip()
                    
                    if not entity_name:
                        continue
                    
                    # UPSERT tag with type
                    try:
                        # Try to find existing tag
                        existing_tag = self.supabase_admin.table('tags').select('*').eq('name', entity_name).execute()
                        
                        if existing_tag.data:
                            # Update existing tag with type
                            tag_id = existing_tag.data[0]['id']
                            self.supabase_admin.table('tags').update({
                                'type': entity_type
                            }).eq('id', tag_id).execute()
                        else:
                            # Create new tag
                            new_tag = self.supabase_admin.table('tags').insert({
                                'name': entity_name,
                                'type': entity_type,
                                'translations': {
                                    'pt': {'name': entity_name},
                                    'en': {'name': entity_name}  # Could be enhanced
                                }
                            }).execute()
                            tag_id = new_tag.data[0]['id']
                        
                        # Create tag link
                        self.supabase_admin.table('law_article_version_tags').insert({
                            'version_id': version_id,
                            'tag_id': tag_id
                        }).execute()
                        
                    except Exception as e:
                        logger.warning(f"Tag creation/linking failed for {entity_name}: {e}")
                
            except Exception as e:
                logger.warning(f"Intelligent tagging error for article {article_version.get('article_number', 'Unknown')}: {e}")
    
    def _perform_enhanced_relational_linking(self, article_versions: List[Dict]):
        """
        Perform enhanced relational linking with status updates.
        Implements PROD5.md Part 4 enhanced relational logic.
        """
        for article_version in article_versions:
            try:
                analysis_data = article_version.get('analysis_data', {})
                if 'analysis' not in analysis_data:
                    continue
                
                pt_analysis = analysis_data['analysis'].get('pt', {})
                cross_references = pt_analysis.get('cross_references', [])
                
                # Get source law info
                source_law_response = self.supabase_admin.table('law_articles').select('law_id').eq('id', article_version['article_id']).execute()
                if not source_law_response.data:
                    continue
                
                source_law_id = source_law_response.data[0]['law_id']
                source_law_details = self.supabase_admin.table('laws').select('id, enactment_date').eq('id', source_law_id).execute()
                if not source_law_details.data:
                    continue
                
                source_enactment = source_law_details.data[0]['enactment_date']
                
                for ref in cross_references:
                    ref_number = ref.get('number', '')
                    if ref_number:
                        # Find target laws
                        target_laws = self.supabase_admin.table('laws').select('id, enactment_date').ilike('official_number', f'%{ref_number}%').execute()
                        
                        for target_law in target_laws.data or []:
                            target_enactment = target_law['enactment_date']
                            
                            # Directional check: source law must be newer
                            if source_enactment and target_enactment and source_enactment > target_enactment:
                                try:
                                    # Check if relationship already exists
                                    existing_rel = self.supabase_admin.table('law_relationships').select('id').eq('source_law_id', source_law_id).eq('target_law_id', target_law['id']).execute()
                                    
                                    if not existing_rel.data:
                                        # Determine relationship type based on text analysis
                                        official_text = article_version['official_text'].lower()
                                        if 'revog' in official_text or 'ab' in official_text:
                                            relationship_type = 'REVOKES'
                                        else:
                                            relationship_type = 'AMENDS'
                                        
                                        # Create relationship
                                        self.supabase_admin.table('law_relationships').insert({
                                            'source_law_id': source_law_id,
                                            'target_law_id': target_law['id'],
                                            'relationship_type': relationship_type
                                        }).execute()
                                        
                                        # TODO: Implement status updates for REVOKED articles
                                        # This would update target article versions to SUPERSEDED status
                                    
                                except Exception as e:
                                    logger.warning(f"Relationship creation failed: {e}")
                            
            except Exception as e:
                logger.warning(f"Enhanced relational linking error for article {article_version.get('article_number', 'Unknown')}: {e}")
    
    def _generate_law_level_summary(self, source_id: str, law_id: str, article_versions: List[Dict]):
        """
        Generate final law-level summary using reduce phase.
        Implements PROD5.md Part 4 final reduce phase.
        """
        logger.info("Generating law-level summary (reduce phase)")
        
        # Collect all English summaries for token efficiency
        english_summaries = []
        for article_version in article_versions:
            analysis_data = article_version.get('analysis_data', {})
            if 'analysis' in analysis_data and 'en' in analysis_data['analysis']:
                en_summary = analysis_data['analysis']['en'].get('informal_summary', '')
                if en_summary and not en_summary.endswith('...'):
                    english_summaries.append(en_summary)
        
        if not english_summaries:
            logger.warning("No English summaries found for law-level summary")
            return
        
        # Create reduce prompt
        combined_summaries = '\n\n'.join(english_summaries)
        
        reduce_prompt = f"""You are a legal expert tasked with creating a comprehensive law-level summary. Based on the individual article summaries below, create a high-level overview of the entire law.

INDIVIDUAL ARTICLE SUMMARIES:
{combined_summaries}

YOUR TASK:
Create a JSON object with both Portuguese and English summaries of the entire law:

{{
  "pt": {{
    "informal_summary_title": "A concise title in Portuguese summarizing the entire law",
    "informal_summary": "A comprehensive summary in Portuguese of what this law accomplishes overall"
  }},
  "en": {{
    "informal_summary_title": "A concise title in English summarizing the entire law", 
    "informal_summary": "A comprehensive summary in English of what this law accomplishes overall"
  }}
}}"""

        response = self._call_gemini(reduce_prompt)
        
        try:
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            law_summary = json.loads(json_text)
            
            # Update the law record with translations
            self.supabase_admin.table('laws').update({
                'translations': law_summary
            }).eq('id', law_id).execute()
            
            logger.info("✅ Law-level summary generated and saved")
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from law summary generator: {e}")
    
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