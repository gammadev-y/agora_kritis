"""
Kritis 3.0 - Multi-Article Legal Document Analysis System
Implementing PROD4.md specifications for sophisticated article parsing and batch analysis.
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

class KritisAnalyzerV3:
    """
    Kritis AI Analyzer V3.0 - Multi-Article Legal Document Analysis System
    
    Features:
    - Smart article parsing within document chunks
    - Batch processing with token management
    - Multi-article knowledge graph creation
    - Enhanced accuracy for complex legal documents
    """
    
    def __init__(self, model_version: str = "gemini-3.0-flash"):
        """Initialize Kritis 3.0 with Supabase clients and Gemini AI."""
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = model_version  # This will be "gemini-3.0-flash" for unique versioning
        self._categories_cache = None
        self._tags_cache = None
        
        # Token management for batch processing
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Approximation for Gemini
        self.max_tokens_per_batch = 6000  # Safe limit leaving room for prompt
        
    def run_enhanced_extractor_phase(self, source_id: str) -> Dict:
        """
        Stage 1: Enhanced Extractor - Smart Article Parser
        Identifies and separates distinct articles within document chunks.
        """
        logger.info(f"🔬 Kritis 3.0 Stage 1: Enhanced Extractor Phase for source {source_id}")
        
        # Get all chunks for the source
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        chunks = chunks_response.data or []
        
        if not chunks:
            raise ValueError(f"No chunks found for source {source_id}")
        
        all_articles = []
        metadata = None
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk['id']}")
            
            if i == 0:
                # First chunk: Extract metadata AND parse articles
                metadata = self._extract_metadata_from_first_chunk(chunk['content'])
                articles = self._parse_articles_from_chunk(chunk['content'])
            else:
                # Other chunks: Only parse articles
                articles = self._parse_articles_from_chunk(chunk['content'])
            
            # Add chunk reference to each article
            for article in articles:
                article['chunk_id'] = chunk['id']
                article['chunk_index'] = chunk['chunk_index']
            
            all_articles.extend(articles)
        
        # Save metadata (first chunk only)
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
        
        # Save parsed articles structure
        articles_analysis = {
            'parsed_articles': all_articles,
            'total_articles_found': len(all_articles),
            'parsing_timestamp': datetime.now().isoformat()
        }
        
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': f"{self.model_version}-parser",
            'analysis_data': articles_analysis
        }).execute()
        
        logger.info(f"🎯 Enhanced Extractor Phase completed: {len(all_articles)} articles found")
        return {
            'metadata': metadata,
            'articles': all_articles,
            'total_articles': len(all_articles)
        }
    
    def _extract_metadata_from_first_chunk(self, content: str) -> Dict:
        """Extract document metadata from first chunk (Kritis 2.0 logic)."""
        
        extractor_prompt = f"""You are a meticulous legal document parser. Analyze the following text, which is the beginning of an official government publication. Your task is to extract the core metadata. Return a single, valid JSON object with the following structure. Do not include any other text in your response.

{{
  "official_number": "The official number of this law (e.g., 'Decreto-Lei n.º 30/2017').",
  "official_title_pt": "The full, official title in Portuguese.",
  "law_type_id": "The ID of the law type based on the title (e.g., 'DECRETO_LEI').",
  "enactment_date": "The primary date of the law in YYYY-MM-DD format.",
  "summary_pt": "The text from the 'SUMÁRIO' section."
}}

TEXT TO ANALYZE:
{content[:8000]}"""  # Limit to avoid token issues

        response = self._call_gemini(extractor_prompt)
        
        try:
            # Clean and parse JSON
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from metadata extractor: {e}")
            return {
                "official_number": f"AUTO-{int(time.time())}",
                "official_title_pt": "Documento Legal",
                "law_type_id": "DECRETO_LAW",  # Use valid fallback
                "enactment_date": datetime.now().date().isoformat(),
                "summary_pt": "Análise não disponível"
            }
    
    def _parse_articles_from_chunk(self, content: str) -> List[Dict]:
        """
        Parse distinct articles from a document chunk using the Enhanced Extractor AI.
        Implements PROD4.md Part 1 specifications.
        """
        
        parser_prompt = f"""You are a meticulous legal document parser. Your sole purpose is to identify and separate distinct articles within a given block of text from an official government publication.

CRITICAL INSTRUCTIONS:
- Scan the text for article delimiters, which can be lines that start with ANY of these patterns:
  * "Artigo X.º" or "ARTIGO X.º"
  * "Art. X.º" or "ART. X.º" 
  * "Artigo X" or "Art. X"
  * Any similar numbering pattern for legal articles
- For each distinct article you find, extract its article_number and its complete, verbatim official_text.
- Include ALL text that belongs to each article until the next article starts.
- Return a single, valid JSON object. Do not include any other text or explanations. The JSON object must contain a single key, "articles", which is an array of objects.

TEXT CHUNK TO PARSE:
{content}

YOUR TASK:
Return a JSON object with the following structure:
{{
  "articles": [
    {{
      "article_number": "Art. 1.º",
      "official_text": "The full, verbatim text of the first article found in the chunk..."
    }},
    {{
      "article_number": "Art. 2.º", 
      "official_text": "The full, verbatim text of the second article found in the chunk..."
    }}
  ]
}}"""

        response = self._call_gemini(parser_prompt)
        
        try:
            # Clean and parse JSON
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            parsed_data = json.loads(json_text)
            articles = parsed_data.get('articles', [])
            
            # Validate and clean articles
            valid_articles = []
            for i, article in enumerate(articles):
                if 'article_number' in article and 'official_text' in article:
                    # Ensure we have content
                    if article['official_text'].strip():
                        valid_articles.append(article)
                    else:
                        logger.warning(f"Empty article text for {article.get('article_number', f'Article {i+1}')}")
                else:
                    logger.warning(f"Invalid article structure at index {i}")
            
            return valid_articles
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from article parser: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Fallback: treat entire chunk as single article
            return [{
                "article_number": "Artigo 1.º",
                "official_text": content
            }]
    
    def run_batch_analyst_phase(self, source_id: str) -> Dict:
        """
        Stage 2: Batch Analyst - Multi-Article Processor
        Processes multiple articles in efficient batches with token management.
        Implements PROD4.md Part 2 specifications.
        """
        logger.info(f"🧠 Kritis 3.0 Stage 2: Batch Analyst Phase for source {source_id}")
        
        # Get parsed articles
        parser_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-parser").execute()
        
        if not parser_response.data:
            raise ValueError(f"No parsed articles found for source {source_id}. Run enhanced extractor first.")
        
        all_articles = parser_response.data[0]['analysis_data']['parsed_articles']
        
        if not all_articles:
            raise ValueError(f"No articles found in parsed data for source {source_id}")
        
        # Get metadata for context
        metadata_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-extractor").execute()
        
        document_title = "Unknown Document"
        if metadata_response.data:
            metadata = metadata_response.data[0]['analysis_data']['extracted_metadata']
            document_title = metadata.get('official_title_pt', 'Unknown Document')
        
        # Smart batching with token management
        batches = self._create_smart_batches(all_articles)
        logger.info(f"Created {len(batches)} batches for {len(all_articles)} articles")
        
        # Process each batch
        all_analyses = []
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} articles")
            
            batch_analyses = self._analyze_article_batch(batch, document_title)
            all_analyses.extend(batch_analyses)
        
        # Save complete analysis results
        complete_analysis = {
            'analyses': all_analyses,
            'total_articles_analyzed': len(all_analyses),
            'batches_processed': len(batches),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': f"{self.model_version}-batch-analyst",
            'analysis_data': complete_analysis
        }).execute()
        
        logger.info(f"🎯 Batch Analyst Phase completed: {len(all_analyses)} articles analyzed")
        return complete_analysis
    
    def _create_smart_batches(self, articles: List[Dict]) -> List[List[Dict]]:
        """
        Create smart batches of articles respecting token limits.
        Implements PROD4.md token management logic.
        """
        batches = []
        current_batch = []
        current_token_count = 0
        
        for article in articles:
            # Calculate tokens for this article
            article_text = article.get('official_text', '')
            article_tokens = len(self.tokenizer.encode(article_text))
            
            # Check if adding this article would exceed limit
            if current_token_count + article_tokens > self.max_tokens_per_batch and current_batch:
                # Current batch is full, start new one
                batches.append(current_batch)
                current_batch = [article]
                current_token_count = article_tokens
            else:
                # Add to current batch
                current_batch.append(article)
                current_token_count += article_tokens
        
        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _analyze_article_batch(self, batch: List[Dict], document_title: str) -> List[Dict]:
        """
        Analyze a batch of articles with the enhanced Kritis prompt.
        Implements PROD4.md Part 2 batch analysis.
        """
        
        # Get categories for context
        if self._categories_cache is None:
            categories_response = self.supabase_admin.table('law_categories').select('id').execute()
            self._categories_cache = [cat['id'] for cat in categories_response.data or []]
        
        categories_list = ', '.join(self._categories_cache)
        
        # Prepare batch data for prompt
        batch_json = json.dumps(batch, ensure_ascii=False, indent=2)
        
        kritis_prompt = f"""You are "Kritis," an expert legal analyst. Your task is to deconstruct a list of legal articles into a structured JSON array.

CONTEXT:
- Master Category List: {categories_list}
- This Law's Title: {document_title}

ARTICLES TO ANALYZE:
You will be given an array of JSON objects, where each object contains an article_number and its official_text.

{batch_json}

YOUR TASK:
For each article in the input array, perform a detailed analysis. Return a single, valid JSON object containing one key, "analyses". This key must be an array where each object corresponds to an input article and has the following structure:

{{
  "analyses": [
    {{
      "article_number": "Artigo 1.º",
      "suggested_category_id": "The single best category ID for this article.",
      "analysis": {{
        "pt": {{
          "informal_summary_title": "A concise Portuguese title.",
          "informal_summary": "A brief, action-oriented Portuguese summary.",
          "key_dates": {{
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          }},
          "key_entities": [
            {{"type": "person", "name": "Name of person"}},
            {{"type": "organization", "name": "Name of organization"}}
          ],
          "cross_references": [
            {{"type": "Decreto-Lei", "number": "30/2017", "article": "140"}}
          ]
        }},
        "en": {{
          "informal_summary_title": "A concise English title.",
          "informal_summary": "A brief, action-oriented English summary.",
          "key_dates": {{
            "Enactment Date": "YYYY-MM-DD",
            "Effective Date": "YYYY-MM-DD"
          }},
          "key_entities": [
            {{"type": "person", "name": "Name of person"}},
            {{"type": "organization", "name": "Name of organization"}}
          ],
          "cross_references": [
            {{"type": "Decree-Law", "number": "30/2017", "article": "140"}}
          ]
        }}
      }}
    }}
  ]
}}"""

        response = self._call_gemini(kritis_prompt)
        
        try:
            # Clean and parse JSON
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
                            "informal_summary_title": "Erro na análise",
                            "informal_summary": "Não foi possível analisar este artigo.",
                            "key_dates": {},
                            "key_entities": [],
                            "cross_references": []
                        },
                        "en": {
                            "informal_summary_title": "Analysis Error",
                            "informal_summary": "Could not analyze this article.",
                            "key_dates": {},
                            "key_entities": [],
                            "cross_references": []
                        }
                    }
                })
            return fallback_analyses
    
    def run_multi_article_knowledge_graph_builder(self, source_id: str) -> str:
        """
        Stage 3: Multi-Article Knowledge Graph Builder
        Creates law and multiple articles with enhanced relationships.
        Implements PROD4.md Part 3 specifications.
        """
        logger.info(f"📚 Kritis 3.0 Stage 3: Multi-Article Knowledge Graph Builder for source {source_id}")
        
        # Step 1: Create the parent law
        law_id = self._create_law_from_metadata(source_id)
        logger.info(f"✅ Created law record: {law_id}")
        
        # Step 2: Create articles and versions from analyses
        article_versions = self._create_multi_articles_from_analyses(source_id, law_id)
        logger.info(f"✅ Created {len(article_versions)} article versions")
        
        # Step 3: Perform automated tagging
        self._perform_automated_tagging(article_versions)
        logger.info(f"✅ Automated tagging completed")
        
        # Step 4: Perform relational linking
        self._perform_relational_linking(article_versions)
        logger.info(f"✅ Relational linking completed")
        
        # Step 5: Update historical status
        self._update_historical_status(article_versions)
        logger.info(f"✅ Historical status updates completed")
        
        logger.info(f"🎯 Multi-Article Knowledge Graph Builder completed: {law_id}")
        return law_id
    
    def _create_multi_articles_from_analyses(self, source_id: str, law_id: str) -> List[Dict]:
        """
        Create multiple law articles and versions from batch analyses.
        Each analysis becomes a separate article with its own version.
        """
        
        # Get batch analyses
        analyses_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-batch-analyst").execute()
        
        if not analyses_response.data:
            raise ValueError(f"No batch analyses found for source {source_id}")
        
        all_analyses = analyses_response.data[0]['analysis_data']['analyses']
        
        # Get parsed articles for original text matching
        parser_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-parser").execute()
        parsed_articles = parser_response.data[0]['analysis_data']['parsed_articles']
        
        # Create mapping from article_number to original text
        article_text_map = {
            article['article_number']: article['official_text'] 
            for article in parsed_articles
        }
        
        # Get mandate
        mandate_response = self.supabase_admin.table('mandates').select('id').limit(1).execute()
        if not mandate_response.data:
            raise Exception("No mandate found")
        mandate_id = mandate_response.data[0]['id']
        
        article_versions = []
        
        for analysis in all_analyses:
            try:
                article_number = analysis.get('article_number', 'Unknown')
                
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
                original_text = article_text_map.get(article_number, 'Text not found')
                
                # Create version with complete analysis data
                effective_date = datetime.now().date().isoformat()  # Default
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
                            
                            # Extract effective date
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
                
                logger.info(f"✅ Created article {article_number} with version")
                
            except Exception as e:
                logger.error(f"❌ Error creating article {analysis.get('article_number', 'Unknown')}: {e}")
                continue
        
        return article_versions
    
    # Reuse methods from V2 with minor adaptations
    def _create_law_from_metadata(self, source_id: str) -> str:
        """Create law record using extracted metadata (from V2)."""
        
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
        
        # Generate document-level summary from first analysis
        document_summary = self._generate_document_summary_v3(source_id)
        
        # Generate slug from title
        title = metadata.get('official_title_pt', 'Unknown Law')
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', title.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        slug = f"{slug}-{int(time.time())}"
        
        # Prepare law data
        law_data = {
            'government_entity_id': government_entity_id,
            'official_number': metadata.get('official_number', f"AUTO-{int(time.time())}"),
            'slug': slug,
            'type_id': metadata.get('law_type_id', 'DECREE_LAW'),
            'enactment_date': metadata.get('enactment_date', datetime.now().date().isoformat()),
            'official_title': title,
            'translations': document_summary
        }
        
        # Insert law record
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        if not response.data:
            raise Exception("Failed to create law record")
        
        return response.data[0]['id']
    
    def _generate_document_summary_v3(self, source_id: str) -> Dict:
        """Generate document-level summary from batch analyses."""
        
        # Get batch analyses
        analyses_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-batch-analyst").execute()
        
        if not analyses_response.data:
            return {
                'pt': {'informal_summary_title': 'Documento Legal', 'informal_summary': 'Análise não disponível'},
                'en': {'informal_summary_title': 'Legal Document', 'informal_summary': 'Analysis not available'}
            }
        
        all_analyses = analyses_response.data[0]['analysis_data']['analyses']
        
        # Use first article's title as document title, combine summaries
        pt_title = 'Documento Legal'
        en_title = 'Legal Document'
        pt_summaries = []
        en_summaries = []
        
        for i, analysis in enumerate(all_analyses):
            if 'analysis' in analysis:
                pt_analysis = analysis['analysis'].get('pt', {})
                en_analysis = analysis['analysis'].get('en', {})
                
                if i == 0:  # Use first article's title
                    pt_title = pt_analysis.get('informal_summary_title', 'Documento Legal')
                    en_title = en_analysis.get('informal_summary_title', 'Legal Document')
                
                if 'informal_summary' in pt_analysis:
                    pt_summaries.append(pt_analysis['informal_summary'])
                if 'informal_summary' in en_analysis:
                    en_summaries.append(en_analysis['informal_summary'])
        
        combined_pt = ' '.join(pt_summaries)
        combined_en = ' '.join(en_summaries)
        
        return {
            'pt': {
                'informal_summary_title': pt_title,
                'informal_summary': combined_pt[:500] + '...' if len(combined_pt) > 500 else combined_pt
            },
            'en': {
                'informal_summary_title': en_title,
                'informal_summary': combined_en[:500] + '...' if len(combined_en) > 500 else combined_en
            }
        }
    
    def _perform_automated_tagging(self, article_versions: List[Dict]):
        """Perform automated tagging (from V2)."""
        if self._tags_cache is None:
            try:
                tags_response = self.supabase_admin.table('tags').select('id, name').execute()
                self._tags_cache = tags_response.data or []
            except Exception as e:
                logger.error(f"Could not fetch tags: {e}")
                self._tags_cache = []
        
        tags = self._tags_cache
        logger.info(f"Checking {len(tags)} tags against {len(article_versions)} article versions")
        
        for article_version in article_versions:
            version_id = article_version['version_id']
            official_text = article_version['official_text'].lower()
            
            matched_tags = []
            for tag in tags:
                tag_name = tag['name'].lower()
                if tag_name in official_text:
                    matched_tags.append(tag['id'])
            
            # Create tag links
            for tag_id in matched_tags:
                try:
                    self.supabase_admin.table('law_article_version_tags').insert({
                        'version_id': version_id,
                        'tag_id': tag_id
                    }).execute()
                except Exception as e:
                    logger.warning(f"Tag link creation failed: {e}")
    
    def _perform_relational_linking(self, article_versions: List[Dict]):
        """Perform relational linking (from V2)."""
        for article_version in article_versions:
            try:
                analysis_data = article_version.get('analysis_data', {})
                if 'analysis' not in analysis_data:
                    continue
                
                pt_analysis = analysis_data['analysis'].get('pt', {})
                cross_references = pt_analysis.get('cross_references', [])
                
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
                        target_laws = self.supabase_admin.table('laws').select('id, enactment_date').ilike('official_number', f'%{ref_number}%').execute()
                        
                        for target_law in target_laws.data or []:
                            target_enactment = target_law['enactment_date']
                            
                            if source_enactment > target_enactment:
                                try:
                                    self.supabase_admin.table('law_relationships').insert({
                                        'source_law_id': source_law_id,
                                        'target_law_id': target_law['id'],
                                        'relationship_type': 'AMENDS'
                                    }).execute()
                                except Exception as e:
                                    logger.warning(f"Relationship creation failed: {e}")
                            
            except Exception as e:
                logger.warning(f"Relational linking error for article {article_version.get('article_number', 'Unknown')}: {e}")
    
    def _update_historical_status(self, article_versions: List[Dict]):
        """Update historical status (simplified from V2)."""
        logger.info("Historical status update completed (simplified implementation)")
    
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