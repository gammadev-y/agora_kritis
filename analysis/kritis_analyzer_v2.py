"""
Kritis 2.0 - Advanced AI Legal Document Analysis System
Implementing the enhanced 4-stage pipeline with metadata extraction, 
structured analysis, and knowledge graph building.
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

class KritisAnalyzerV2:
    """Kritis 2.0 - Advanced AI legal analyst with metadata extraction and knowledge graph building."""

    def __init__(self):
        """Initialize Kritis 2.0 with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = 'gemini-2.0-flash'
        
        # Token limits for managing large documents
        self.max_tokens_per_batch = 100000  # Conservative limit for Gemini
        
        # Cache for categories and tags
        self._categories_cache = None
        self._tags_cache = None
        
    # ========================================
    # STAGE 1 & 2: THE "EXTRACTOR" AI
    # ========================================
    
    def run_extractor_phase(self, source_id: str) -> Dict:
        """
        Stage 1 & 2: Extract core metadata from the first chunk of the document.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict: Extracted metadata
        """
        logger.info(f"🔍 Kritis 2.0 Stage 1-2: Starting Extractor Phase for source {source_id}")
        
        try:
            # Validate source_id
            uuid.UUID(source_id)
        except ValueError:
            raise ValueError(f"Invalid source UUID: {source_id}")
        
        # Get the first chunk (chunk_index = 0)
        first_chunk_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).eq('chunk_index', 0).execute()
        
        if not first_chunk_response.data:
            raise ValueError(f"No first chunk (index 0) found for source {source_id}")
        
        first_chunk = first_chunk_response.data[0]
        logger.info(f"Processing first chunk: {first_chunk['id']} (length: {len(first_chunk['content'])})")
        
        # Extract metadata using the Extractor AI
        metadata = self._extract_metadata_with_ai(first_chunk['content'])
        
        # Store the extraction result
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': f"{self.model_version}-extractor",
            'analysis_data': {
                'type': 'metadata_extraction',
                'chunk_id': first_chunk['id'],
                'extracted_metadata': metadata
            }
        }).execute()
        
        logger.info("🎯 Extractor Phase completed successfully")
        logger.info(f"📋 Extracted: {metadata.get('official_title_pt', 'Unknown')}")
        
        return metadata
    
    def _extract_metadata_with_ai(self, chunk_content: str) -> Dict:
        """Extract metadata from first chunk using specialized AI prompt."""
        
        extractor_prompt = f"""You are a meticulous legal document parser. Analyze the following text, which is the beginning of an official government publication. Your task is to extract the core metadata. Return a single, valid JSON object with the following structure. Do not include any other text in your response.

{chunk_content}

{{
  "official_number": "The official number of this law (e.g., 'Decreto-Lei n.º 30/2017').",
  "official_title_pt": "The full, official title in Portuguese.",
  "law_type_id": "The ID of the law type based on the title (e.g., 'DECRETO_LEI').",
  "enactment_date": "The primary date of the law in YYYY-MM-DD format.",
  "summary_pt": "The text from the 'SUMÁRIO' section."
}}"""

        # Call Gemini API
        response = self._call_gemini(extractor_prompt)
        
        # Parse and validate JSON response
        try:
            # Extract JSON from response
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            metadata = json.loads(json_text)
            
            # Validate required fields
            required_fields = ['official_number', 'official_title_pt', 'law_type_id', 'enactment_date']
            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    logger.warning(f"Missing or empty field: {field}")
            
            # Map law type to valid database values
            metadata['law_type_id'] = self._map_law_type(metadata.get('law_type_id', ''))
            
            return metadata
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse extractor response: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback metadata
            return {
                "official_number": f"AUTO-{int(time.time())}",
                "official_title_pt": "Documento Legal",
                "law_type_id": "DECREE_LAW",
                "enactment_date": datetime.now().date().isoformat(),
                "summary_pt": "Não foi possível extrair o sumário."
            }
    
    def _map_law_type(self, extracted_type: str) -> str:
        """Map extracted law type to valid database values."""
        type_mapping = {
            'DECRETO_LEI': 'DECREE_LAW',
            'DECRETO-LEI': 'DECREE_LAW',
            'LEI': 'PARLIAMENTARY_LAW',
            'REGULAMENTO': 'REGULATION',
            'RESOLUÇÃO': 'RESOLUTION',
            'CONSTITUIÇÃO': 'CONSTITUTION'
        }
        
        # Clean up the extracted type
        clean_type = extracted_type.upper().replace(' ', '_').replace('-', '_')
        return type_mapping.get(clean_type, 'DECREE_LAW')  # Default fallback
    
    # ========================================
    # STAGE 3: THE "ANALYST" AI ("KRITIS")
    # ========================================
    
    def run_analyst_phase(self, source_id: str) -> bool:
        """
        Stage 3: Enhanced structured analysis of each document chunk.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            bool: Success status
        """
        logger.info(f"🧠 Kritis 2.0 Stage 3: Starting Analyst Phase for source {source_id}")
        
        # Get source metadata (should have been extracted in Stage 1-2)
        source_response = self.supabase_admin.table('sources').select('*').eq('id', source_id).execute()
        if not source_response.data:
            raise ValueError(f"Source {source_id} not found")
        
        source = source_response.data[0]
        
        # Get extracted metadata from Stage 1-2
        metadata_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-extractor").execute()
        
        if metadata_response.data:
            extracted_metadata = metadata_response.data[0]['analysis_data']['extracted_metadata']
            official_title = extracted_metadata.get('official_title_pt', 'Unknown Law')
        else:
            official_title = 'Unknown Law'
            logger.warning("No metadata extraction found, using fallback title")
        
        # Get master category list
        categories = self._get_categories_list()
        
        # Get document chunks
        chunks = self._get_document_chunks(source_id)
        if not chunks:
            logger.warning(f"No document chunks found for source {source_id}")
            return False
            
        logger.info(f"Found {len(chunks)} chunks to analyze")
        
        # Process each chunk with enhanced Kritis analysis
        success_count = 0
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(chunks)}: {chunk['id']}")
            
            try:
                # Generate enhanced analysis
                analysis_data = self._analyze_chunk_with_enhanced_kritis(
                    chunk, categories, official_title
                )
                
                # Add metadata to analysis_data
                analysis_data['chunk_id'] = chunk['id']
                analysis_data['chunk_index'] = chunk.get('chunk_index', i)
                analysis_data['type'] = 'enhanced_analysis'
                
                # Store in source_ai_analysis table
                self.supabase_admin.table('source_ai_analysis').insert({
                    'source_id': source_id,
                    'model_version': f"{self.model_version}-analyst",
                    'analysis_data': analysis_data
                }).execute()
                
                success_count += 1
                logger.info(f"✅ Chunk {chunk['id']} analyzed and saved")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing chunk {chunk['id']}: {e}")
                continue
        
        logger.info(f"🎯 Analyst Phase completed: {success_count}/{len(chunks)} chunks analyzed successfully")
        return success_count > 0
    
    def _analyze_chunk_with_enhanced_kritis(self, chunk: Dict, categories: str, official_title: str) -> Dict:
        """Analyze a single chunk using the enhanced Kritis prompt."""
        
        # Construct the enhanced Kritis prompt
        kritis_prompt = f"""You are "Kritis," an expert legal analyst. Your task is to deconstruct the following legal article text into a structured JSON object.

CONTEXT:
Master Category List: {categories}
This Article Belongs To: {official_title}

ARTICLE TEXT TO ANALYZE:
{chunk['content']}

YOUR TASK: Return a single, valid JSON object with the following structure:

{{
  "suggested_category_id": "From the master list, choose the single best category ID for this article's content (e.g., 'FISCAL').",
  "analysis": {{
    "pt": {{
      "informal_summary_title": "A concise, 5-10 word action-oriented title in Portuguese.",
      "informal_summary": "A brief, action-oriented summary in Portuguese.",
      "key_dates": {{
        "Enactment Date": "YYYY-MM-DD",
        "Effective Date": "YYYY-MM-DD"
      }},
      "key_entities": [
        {{"type": "person", "name": "Marcelo Rebelo de Sousa"}},
        {{"type": "organization", "name": "Conselho Superior da Guarda Nacional Republicana"}}
      ],
      "cross_references": [
        {{"type": "Decreto-Lei", "number": "30/2017", "article": "140"}}
      ]
    }},
    "en": {{
      "informal_summary_title": "English translation of the concise title.",
      "informal_summary": "English translation of the action-oriented summary.",
      "key_dates": {{
        "Enactment Date": "YYYY-MM-DD",
        "Effective Date": "YYYY-MM-DD"
      }},
      "key_entities": [
        {{"type": "person", "name": "Marcelo Rebelo de Sousa"}},
        {{"type": "organization", "name": "Superior Council of the National Republican Guard"}}
      ],
      "cross_references": [
        {{"type": "Decree-Law", "number": "30/2017", "article": "140"}}
      ]
    }}
  }}
}}"""

        # Call Gemini API
        response = self._call_gemini(kritis_prompt)
        
        # Parse and validate JSON response
        try:
            # Extract JSON from response
            json_text = response.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            analysis_data = json.loads(json_text)
            
            # Validate structure
            if 'suggested_category_id' not in analysis_data:
                analysis_data['suggested_category_id'] = 'ADMINISTRATIVE'  # Default
                
            if 'analysis' not in analysis_data:
                raise ValueError("Missing 'analysis' field")
            
            # Ensure both languages exist
            for lang in ['pt', 'en']:
                if lang not in analysis_data['analysis']:
                    analysis_data['analysis'][lang] = {
                        "informal_summary_title": "Erro na análise" if lang == 'pt' else "Analysis Error",
                        "informal_summary": "Não foi possível analisar" if lang == 'pt' else "Could not analyze",
                        "key_dates": {},
                        "key_entities": [],
                        "cross_references": []
                    }
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid JSON response from Enhanced Kritis: {e}")
            logger.error(f"Raw response: {response[:500]}")
            
            # Return fallback structure
            return {
                "suggested_category_id": "ADMINISTRATIVE",
                "analysis": {
                    "pt": {
                        "informal_summary_title": "Erro na análise",
                        "informal_summary": "Não foi possível analisar este artigo devido a erro técnico.",
                        "key_dates": {},
                        "key_entities": [],
                        "cross_references": []
                    },
                    "en": {
                        "informal_summary_title": "Analysis Error",
                        "informal_summary": "Could not analyze this article due to technical error.",
                        "key_dates": {},
                        "key_entities": [],
                        "cross_references": []
                    }
                }
            }
    
    def _get_categories_list(self) -> str:
        """Get comma-separated list of all law categories."""
        if self._categories_cache is None:
            try:
                response = self.supabase_admin.table('law_categories').select('id').execute()
                categories = [cat['id'] for cat in response.data or []]
                self._categories_cache = ', '.join(categories)
            except Exception as e:
                logger.error(f"Could not fetch categories: {e}")
                self._categories_cache = "CONSTITUTIONAL, FISCAL, LABOR, HEALTH, ENVIRONMENTAL, JUDICIAL, ADMINISTRATIVE, CIVIL, CRIMINAL, SOCIAL_SECURITY"
        
        return self._categories_cache
    
    # ========================================
    # STAGE 4: KNOWLEDGE GRAPH BUILDER
    # ========================================
    
    def run_knowledge_graph_builder(self, source_id: str) -> str:
        """
        Stage 4: Create structured law records with automated tagging and relationship linking.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            str: UUID of the created law
        """
        logger.info(f"📚 Kritis 2.0 Stage 4: Starting Knowledge Graph Builder for source {source_id}")
        
        # Step 1: Create core records using extracted metadata
        law_id = self._create_law_from_metadata(source_id)
        logger.info(f"✅ Created law record: {law_id}")
        
        # Step 2: Create articles and versions with rich analysis data
        article_versions = self._create_articles_from_analysis(source_id, law_id)
        logger.info(f"✅ Created {len(article_versions)} article versions")
        
        # Step 3: Perform automated tagging
        self._perform_automated_tagging(article_versions)
        logger.info(f"✅ Automated tagging completed")
        
        # Step 4: Perform relational linking
        self._perform_relational_linking(source_id, article_versions)
        logger.info(f"✅ Relational linking completed")
        
        # Step 5: Update historical status
        self._update_historical_status(article_versions)
        logger.info(f"✅ Historical status updates completed")
        
        logger.info(f"🎯 Knowledge Graph Builder completed: {law_id}")
        return law_id
    
    def _create_law_from_metadata(self, source_id: str) -> str:
        """Create law record using extracted metadata."""
        
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
        
        # Generate document-level summary from all analyses
        document_summary = self._generate_document_summary(source_id)
        
        # Generate slug from title
        title = metadata.get('official_title_pt', 'Unknown Law')
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', title.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        slug = f"{slug}-{int(time.time())}"  # Add timestamp for uniqueness
        
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
    
    def _generate_document_summary(self, source_id: str) -> Dict:
        """Generate document-level summary from all chunk analyses."""
        
        # Get all analyst analyses
        analyses_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-analyst").execute()
        
        if not analyses_response.data:
            return {
                'pt': {'informal_summary_title': 'Documento Legal', 'informal_summary': 'Análise não disponível'},
                'en': {'informal_summary_title': 'Legal Document', 'informal_summary': 'Analysis not available'}
            }
        
        # Extract summaries and titles from first analysis (primary)
        pt_summaries = []
        en_summaries = []
        pt_title = 'Documento Legal'
        en_title = 'Legal Document'
        
        for i, analysis in enumerate(analyses_response.data):
            data = analysis['analysis_data']
            if 'analysis' in data:
                pt_analysis = data['analysis'].get('pt', {})
                en_analysis = data['analysis'].get('en', {})
                
                # Use the title from the first analysis as the document title
                if i == 0:
                    pt_title = pt_analysis.get('informal_summary_title', 'Documento Legal')
                    en_title = en_analysis.get('informal_summary_title', 'Legal Document')
                
                if 'informal_summary' in pt_analysis:
                    pt_summaries.append(pt_analysis['informal_summary'])
                if 'informal_summary' in en_analysis:
                    en_summaries.append(en_analysis['informal_summary'])
        
        # Combine summaries
        combined_pt = ' '.join(pt_summaries)
        combined_en = ' '.join(en_summaries)
        
        # Generate final summary using proper titles
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
    
    def _create_articles_from_analysis(self, source_id: str, law_id: str) -> List[Dict]:
        """Create law articles and versions from analysis data."""
        
        # Get all analyst analyses
        analyses_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', f"{self.model_version}-analyst").order('created_at').execute()
        
        # Get corresponding chunks
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        chunks = chunks_response.data or []
        
        # Get any available mandate
        mandate_response = self.supabase_admin.table('mandates').select('id').limit(1).execute()
        if not mandate_response.data:
            raise Exception("No mandate found")
        mandate_id = mandate_response.data[0]['id']
        
        article_versions = []
        
        for i, (analysis, chunk) in enumerate(zip(analyses_response.data or [], chunks)):
            try:
                # Create article
                article_data = {
                    'law_id': law_id,
                    'article_number': str(i + 1)
                }
                
                article_response = self.supabase_admin.table('law_articles').insert(article_data).execute()
                if not article_response.data:
                    raise Exception(f"Failed to create article {i + 1}")
                
                article_id = article_response.data[0]['id']
                
                # Create version with complete analysis data for translations
                analysis_data = analysis['analysis_data']
                translations = {}
                effective_date = datetime.now().date().isoformat()  # Default fallback
                
                if 'analysis' in analysis_data:
                    for lang in ['pt', 'en']:
                        if lang in analysis_data['analysis']:
                            lang_data = analysis_data['analysis'][lang]
                            # Include complete analysis structure as per PROD3.md
                            translations[lang] = {
                                'informal_summary_title': lang_data.get('informal_summary_title', ''),
                                'informal_summary': lang_data.get('informal_summary', ''),
                                'key_dates': lang_data.get('key_dates', {}),
                                'key_entities': lang_data.get('key_entities', []),
                                'cross_references': lang_data.get('cross_references', [])
                            }
                            
                            # Extract effective date from analysis (prefer PT, fallback to EN)
                            if lang == 'pt' and 'key_dates' in lang_data:
                                dates = lang_data['key_dates']
                                if 'Effective Date' in dates and dates['Effective Date']:
                                    try:
                                        # Validate date format
                                        datetime.strptime(dates['Effective Date'], '%Y-%m-%d')
                                        effective_date = dates['Effective Date']
                                    except (ValueError, TypeError):
                                        pass  # Use fallback
                
                version_data = {
                    'article_id': article_id,
                    'mandate_id': mandate_id,
                    'status_id': 'ACTIVE',
                    'valid_from': effective_date,
                    'official_text': chunk['content'],
                    'translations': translations
                }
                
                version_response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
                if not version_response.data:
                    raise Exception(f"Failed to create version for article {i + 1}")
                
                version_id = version_response.data[0]['id']
                
                # Store version info with full analysis data for later processing
                article_versions.append({
                    'version_id': version_id,
                    'article_id': article_id,
                    'official_text': chunk['content'],
                    'analysis_data': analysis_data,
                    'chunk_index': i
                })
                
                logger.info(f"✅ Created article {i + 1} with version")
                
            except Exception as e:
                logger.error(f"❌ Error creating article {i + 1}: {e}")
                continue
        
        return article_versions
    
    def _perform_automated_tagging(self, article_versions: List[Dict]):
        """Perform automated tagging by searching for tag names in text."""
        
        # Get all tags
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
                
                # Simple string search
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
                    # Tag link might already exist
                    logger.debug(f"Could not create tag link: {e}")
            
            if matched_tags:
                logger.info(f"✅ Tagged version {version_id} with {len(matched_tags)} tags")
    
    def _perform_relational_linking(self, source_id: str, article_versions: List[Dict]):
        """Create law relationships based on cross-references in analysis."""
        
        # Get the current law
        current_law_response = self.supabase_admin.table('laws').select('id, enactment_date').eq('id', 
            self.supabase_admin.table('law_articles').select('law_id').eq('id', 
                article_versions[0]['article_id'] if article_versions else None
            ).execute().data[0]['law_id'] if article_versions else None
        ).execute()
        
        if not current_law_response.data:
            logger.warning("Could not find current law for relationship linking")
            return
        
        current_law = current_law_response.data[0]
        current_law_id = current_law['id']
        current_enactment_date = current_law['enactment_date']
        
        for article_version in article_versions:
            analysis_data = article_version['analysis_data']
            
            # Extract cross-references from analysis
            if 'analysis' not in analysis_data:
                continue
            
            pt_analysis = analysis_data['analysis'].get('pt', {})
            cross_references = pt_analysis.get('cross_references', [])
            
            for cross_ref in cross_references:
                try:
                    ref_type = cross_ref.get('type', '')
                    ref_number = cross_ref.get('number', '')
                    
                    if not ref_number:
                        continue
                    
                    # Search for referenced law
                    referenced_laws = self.supabase_admin.table('laws').select('id, enactment_date').ilike('official_number', f'%{ref_number}%').execute()
                    
                    if not referenced_laws.data:
                        logger.debug(f"Referenced law not found: {ref_number}")
                        continue
                    
                    for referenced_law in referenced_laws.data:
                        referenced_law_id = referenced_law['id']
                        referenced_enactment_date = referenced_law['enactment_date']
                        
                        # Directional check: current law must be newer
                        if current_enactment_date <= referenced_enactment_date:
                            logger.debug(f"Skipping relationship: current law is not newer than referenced law")
                            continue
                        
                        # Determine relationship type (simplified for now)
                        relationship_type = 'AMENDS'  # Default relationship
                        
                        # Create relationship
                        try:
                            self.supabase_admin.table('law_relationships').insert({
                                'source_law_id': current_law_id,
                                'target_law_id': referenced_law_id,
                                'relationship_type': relationship_type
                            }).execute()
                            
                            logger.info(f"✅ Created relationship: {current_law_id} {relationship_type} {referenced_law_id}")
                            
                        except Exception as e:
                            logger.debug(f"Could not create relationship: {e}")
                
                except Exception as e:
                    logger.debug(f"Error processing cross-reference: {e}")
    
    def _update_historical_status(self, article_versions: List[Dict]):
        """Update historical status of superseded laws."""
        
        # This is a simplified implementation
        # In a full implementation, this would examine the relationships created
        # and update the status of superseded law article versions
        
        logger.info("Historical status update completed (simplified implementation)")
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
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