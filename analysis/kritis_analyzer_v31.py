"""
Kritis V3.1 - The Refactored Agora AI Analyst
Complete architectural refactor implementing PROD9 specifications.

This analyzer implements the simplified database schema approach:
- Direct laws -> law_article_versions relationship
- JSONB tags on both laws and versions
- Preamble-aware extraction (article_order = 0 for preamble)
- Enhanced structured analysis output
"""

import json
import logging
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)

class KritisAnalyzerV31:
    """Kritis V3.1 - Refactored analyzer following PROD9 specifications."""

    def __init__(self):
        """Initialize Kritis V3.1 with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = 'gemini-2.0-flash'
        
    # ========================================
    # STAGE 1: ENHANCED EXTRACTOR WITH PREAMBLE AWARENESS
    # ========================================
    
    def run_enhanced_extractor_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 1: Extract preamble and articles with enhanced structure.
        
        Following PROD9 specifications:
        - Separate preamble text from numbered articles
        - Return JSON with preamble_text and articles array
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict containing extraction results and metadata
        """
        logger.info(f"🔄 Kritis V3.1 Stage 1: Enhanced Extractor for source {source_id}")
        
        # Get document chunks
        chunks_response = self.supabase_admin.table('document_chunks').select('*').eq('source_id', source_id).order('chunk_index').execute()
        if not chunks_response.data:
            raise ValueError(f"No document chunks found for source {source_id}")
        
        chunks = chunks_response.data
        
        # Combine all chunk content
        full_text = ""
        for chunk in chunks:
            full_text += chunk['content'] + "\n\n"
        
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
        self.supabase_admin.table('pending_extractions').insert({
            'source_id': source_id,
            'status': 'COMPLETED',
            'extracted_data': extracted_data,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"✅ Enhanced extraction completed: {len(extraction_result['articles'])} articles, preamble: {bool(extraction_result['preamble_text'].strip())}")
        
        return {
            'total_articles': len(extraction_result['articles']),
            'has_preamble': bool(extraction_result['preamble_text'].strip()),
            'metadata': metadata
        }
    
    def _extract_metadata(self, first_chunk_text: str) -> Dict[str, Any]:
        """Extract law metadata from the first chunk."""
        
        metadata_prompt = f"""
        You are a legal document metadata extractor. Analyze this Portuguese legal document text and extract the core metadata.

        Text to analyze:
        {first_chunk_text}

        Return a JSON object with these fields:
        - official_number: The official law number (e.g., "Lei n.º 123/2023")
        - official_title: The official title of the law
        - law_type_id: The type of law (e.g., "LEI", "DECRETO_LEI", "RESOLUCAO")
        - enactment_date: The enactment date in YYYY-MM-DD format
        - government_entity_id: Always use "b8b3c8e5-4c2d-4e6f-8a9b-1c2d3e4f5a6b" for Portuguese government

        Only include fields you can confidently extract. Return valid JSON only.
        """
        
        try:
            response = self.model.generate_content(metadata_prompt)
            metadata_text = response.text.strip()
            
            # Clean the response to ensure it's valid JSON
            if metadata_text.startswith('```json'):
                metadata_text = metadata_text[7:]
            if metadata_text.endswith('```'):
                metadata_text = metadata_text[:-3]
            
            metadata = json.loads(metadata_text)
            
            # Ensure government_entity_id is set
            metadata['government_entity_id'] = "3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f"
            
            return metadata
            
        except Exception as e:
            logger.warning(f"⚠️ Metadata extraction failed: {e}")
            return {
                'government_entity_id': "3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f"
            }
    
    def _extract_preamble_and_articles(self, full_text: str) -> Dict[str, Any]:
        """Extract preamble and articles according to PROD9 specifications."""
        
        extraction_prompt = f"""
        You are a Portuguese legal document parser. Your task is to separate the preamble from the numbered articles in this legal document.

        The preamble is all text that appears BEFORE the first "Artigo 1.º" (or similar first article marker).
        Articles are the numbered sections starting with "Artigo 1.º", "Artigo 2.º", etc.

        Document text:
        {full_text}

        Return a JSON object with exactly this structure:
        {{
            "preamble_text": "All text before the first article, or empty string if none",
            "articles": [
                {{
                    "article_number": "Artigo 1.º",
                    "official_text": "The complete text of article 1"
                }},
                {{
                    "article_number": "Artigo 2.º", 
                    "official_text": "The complete text of article 2"
                }}
            ]
        }}

        Important rules:
        1. If there is text before "Artigo 1.º", put it in preamble_text
        2. Each article should have its complete text (including the article number)
        3. Preserve original formatting and spacing
        4. If no preamble exists, use empty string ""
        5. Return valid JSON only

        Return the JSON object:
        """
        
        try:
            response = self.model.generate_content(extraction_prompt)
            extraction_text = response.text.strip()
            
            # Clean the response to ensure it's valid JSON
            if extraction_text.startswith('```json'):
                extraction_text = extraction_text[7:]
            if extraction_text.endswith('```'):
                extraction_text = extraction_text[:-3]
            
            # Additional cleaning - remove any markdown formatting
            import re
            extraction_text = re.sub(r'^```.*?\n', '', extraction_text, flags=re.MULTILINE)
            extraction_text = re.sub(r'\n```$', '', extraction_text)
            extraction_text = extraction_text.strip()
            
            logger.info(f"🔍 Attempting to parse extraction JSON (length: {len(extraction_text)} chars)")
            result = json.loads(extraction_text)
            
            # Validate the structure
            if 'preamble_text' not in result:
                result['preamble_text'] = ""
            if 'articles' not in result:
                result['articles'] = []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.error(f"Raw response (first 500 chars): {extraction_text[:500] if 'extraction_text' in locals() else 'No response'}")
            # Fallback: return empty structure
            return {
                "preamble_text": "",
                "articles": []
            }
        except Exception as e:
            logger.error(f"❌ Preamble/article extraction failed: {e}")
            # Fallback: return empty structure
            return {
                "preamble_text": "",
                "articles": []
            }
    
    # ========================================
    # STAGE 2: ENHANCED KRITIS ANALYST
    # ========================================
    
    def run_enhanced_analyst_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 2: Analyze each article and preamble with structured output.
        
        Following PROD9 specifications:
        - Enhanced structured JSON output with tags array
        - Analysis for both preamble and articles
        - Category suggestions and cross-references
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict containing analysis results
        """
        logger.info(f"🧠 Kritis V3.1 Stage 2: Enhanced Analyst for source {source_id}")
        
        # Get extraction data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        if not extraction_response.data:
            raise ValueError(f"No extraction data found for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        
        analysis_results = []
        total_items = 0
        successful_analyses = 0
        
        # Analyze preamble if it exists
        if extraction_data.get('preamble_text', '').strip():
            logger.info("🔍 Analyzing preamble...")
            try:
                preamble_analysis = self._analyze_content(
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
                article_analysis = self._analyze_content(
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
        
        # Store in source_ai_analysis table
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': 'kritis_v31_enhanced_analyst',
            'analysis_data': analysis_data,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"✅ Enhanced analysis completed: {successful_analyses}/{total_items} items analyzed successfully")
        
        return {
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'completion_rate': (successful_analyses / total_items * 100) if total_items > 0 else 0
        }
    
    def _analyze_content(self, content: str, content_type: str, article_number: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content (preamble or article) with enhanced structured output."""
        
        if content_type == "preamble":
            analysis_prompt = f"""
            You are Kritis, an expert Portuguese legal analyst. Analyze this legal document preamble.

            Preamble text:
            {content}

            Return a JSON object with this EXACT structure:
            {{
                "suggested_category_id": "FISCAL|ADMINISTRATIVO|PENAL|CIVIL|CONSTITUCIONAL|LABORAL|COMERCIAL|AMBIENTAL|EDUCACAO|SAUDE",
                "tags": [
                    {{"type": "person", "name": "Name of person mentioned"}},
                    {{"type": "concept", "name": "Legal concept or topic"}},
                    {{"type": "entity", "name": "Organization or institution"}},
                    {{"type": "location", "name": "Geographic location"}}
                ],
                "analysis": {{
                    "pt": {{
                        "informal_summary_title": "Brief Portuguese title summarizing the preamble",
                        "informal_summary": "Detailed Portuguese analysis of the preamble purpose and context",
                        "cross_references": [
                            {{"type": "Decreto-Lei", "number": "123/2023"}},
                            {{"type": "Lei", "number": "456/2022"}}
                        ]
                    }},
                    "en": {{
                        "informal_summary_title": "Brief English title summarizing the preamble",
                        "informal_summary": "Detailed English analysis of the preamble purpose and context",
                        "cross_references": [
                            {{"type": "Decree-Law", "number": "123/2023"}},
                            {{"type": "Law", "number": "456/2022"}}
                        ]
                    }}
                }}
            }}

            Only include tags that are clearly present in the text. Return valid JSON only.
            """
        else:
            analysis_prompt = f"""
            You are Kritis, an expert Portuguese legal analyst. Analyze this legal article.

            Article: {article_number or "Article"}
            Text:
            {content}

            Return a JSON object with this EXACT structure:
            {{
                "article_number": "{article_number or 'Unknown'}",
                "suggested_category_id": "FISCAL|ADMINISTRATIVO|PENAL|CIVIL|CONSTITUCIONAL|LABORAL|COMERCIAL|AMBIENTAL|EDUCACAO|SAUDE",
                "tags": [
                    {{"type": "person", "name": "Name of person mentioned"}},
                    {{"type": "concept", "name": "Legal concept or topic"}},
                    {{"type": "entity", "name": "Organization or institution"}},
                    {{"type": "location", "name": "Geographic location"}}
                ],
                "analysis": {{
                    "pt": {{
                        "informal_summary_title": "Brief Portuguese title summarizing the article",
                        "informal_summary": "Detailed Portuguese analysis of what this article establishes",
                        "cross_references": [
                            {{"type": "Decreto-Lei", "number": "123/2023"}},
                            {{"type": "Lei", "number": "456/2022"}}
                        ]
                    }},
                    "en": {{
                        "informal_summary_title": "Brief English title summarizing the article",
                        "informal_summary": "Detailed English analysis of what this article establishes",
                        "cross_references": [
                            {{"type": "Decree-Law", "number": "123/2023"}},
                            {{"type": "Law", "number": "456/2022"}}
                        ]
                    }}
                }}
            }}

            Only include tags that are clearly present in the text. Return valid JSON only.
            """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            analysis_text = response.text.strip()
            
            # Clean the response to ensure it's valid JSON
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text[7:]
            if analysis_text.endswith('```'):
                analysis_text = analysis_text[:-3]
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {e}")
            # Return fallback structure
            return {
                "suggested_category_id": "ADMINISTRATIVO",
                "tags": [],
                "analysis": {
                    "pt": {
                        "informal_summary_title": "Análise indisponível",
                        "informal_summary": "Não foi possível analisar este conteúdo automaticamente.",
                        "cross_references": []
                    },
                    "en": {
                        "informal_summary_title": "Analysis unavailable",
                        "informal_summary": "Could not automatically analyze this content.",
                        "cross_references": []
                    }
                }
            }
    
    # ========================================
    # STAGE 3: ENHANCED LAW INGESTION
    # ========================================
    
    def run_enhanced_law_ingestion(self, source_id: str) -> str:
        """
        Stage 3: Create law records following PROD9 simplified schema.
        
        Following PROD9 specifications:
        - Direct laws -> law_article_versions relationship
        - Preamble as article_order = 0
        - JSONB tags on both tables
        - Transaction-based ingestion
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            str: UUID of the created law
        """
        logger.info(f"📚 Kritis V3.1 Stage 3: Enhanced Law Ingestion for source {source_id}")
        
        # Get extraction and analysis data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        if not extraction_response.data:
            raise ValueError(f"No extraction data found for source {source_id}")
        
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', 'kritis_v31_enhanced_analyst').order('created_at', desc=True).limit(1).execute()
        if not analysis_response.data:
            raise ValueError(f"No analysis data found for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        analysis_data = analysis_response.data[0]['analysis_data']
        
        # Start transaction-based ingestion
        try:
            # Step 1: Create parent law record
            law_id = self._create_parent_law_record(source_id, extraction_data)
            logger.info(f"✅ Created parent law record: {law_id}")
            
            # Step 2: Process and insert preamble (if exists)
            preamble_version_id = None
            if extraction_data.get('preamble_text', '').strip():
                preamble_version_id = self._insert_preamble_version(law_id, extraction_data, analysis_data)
                logger.info(f"✅ Created preamble version: {preamble_version_id}")
            
            # Step 3: Process and insert articles
            article_version_ids = self._insert_article_versions(law_id, extraction_data, analysis_data)
            logger.info(f"✅ Created {len(article_version_ids)} article versions")
            
            # Step 4: Aggregate tags and update parent law
            self._aggregate_tags_and_update_law(law_id)
            logger.info("✅ Aggregated tags and updated parent law")
            
            # Step 5: Generate and store law summary
            self._generate_and_store_law_summary(law_id, analysis_data)
            logger.info("✅ Generated and stored law summary")
            
            logger.info(f"🎯 Enhanced law ingestion completed successfully: {law_id}")
            return law_id
            
        except Exception as e:
            logger.error(f"❌ Enhanced law ingestion failed: {e}")
            raise
    
    def _create_parent_law_record(self, source_id: str, extraction_data: Dict[str, Any]) -> str:
        """Create the parent law record according to PROD9 specifications."""
        
        metadata = extraction_data.get('metadata', {})
        
        # Generate a slug from the official title or number
        if metadata.get('official_title'):
            slug = metadata['official_title'].lower().replace(' ', '-')[:100]
        elif metadata.get('official_number'):
            slug = metadata['official_number'].lower().replace(' ', '-')[:100]
        else:
            slug = f"law-{uuid.uuid4().hex[:8]}"
        
        # Clean slug to be URL-safe
        import re
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        
        law_data = {
            'id': str(uuid.uuid4()),
            'government_entity_id': metadata.get('government_entity_id', "3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f"),
            'source_id': source_id,
            'official_title': metadata.get('official_title', 'Untitled Law'),
            'slug': slug,
            'official_number': metadata.get('official_number'),
            'type_id': metadata.get('law_type_id'),
            'enactment_date': metadata.get('enactment_date'),
            'tags': None,  # Will be populated in aggregation step
            'translations': None  # Will be populated in summary step
        }
        
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        return law_data['id']
    
    def _insert_preamble_version(self, law_id: str, extraction_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """Insert preamble as article_order = 0."""
        
        preamble_text = extraction_data['preamble_text']
        
        # Find preamble analysis
        preamble_analysis = None
        for result in analysis_data['analysis_results']:
            if result['content_type'] == 'preamble':
                preamble_analysis = result['analysis']
                break
        
        version_data = {
            'id': str(uuid.uuid4()),
            'law_id': law_id,
            'article_order': 0,  # Explicit identifier for preamble
            'mandate_id': "50259b5a-054e-4bbf-a39d-637e7d1c1f9f",  # Actual mandate ID
            'status_id': "ACTIVE",
            'valid_from': datetime.utcnow().date().isoformat(),
            'official_text': preamble_text,
            'tags': preamble_analysis.get('tags', []) if preamble_analysis else [],
            'translations': preamble_analysis.get('analysis', {}) if preamble_analysis else {}
        }
        
        response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
        return version_data['id']
    
    def _insert_article_versions(self, law_id: str, extraction_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> List[str]:
        """Insert all articles as law_article_versions."""
        
        articles = extraction_data.get('articles', [])
        analysis_results = analysis_data.get('analysis_results', [])
        
        # Create mapping of article analyses
        article_analyses = {}
        for result in analysis_results:
            if result['content_type'] == 'article':
                article_analyses[result['article_order']] = result['analysis']
        
        version_ids = []
        
        for i, article in enumerate(articles):
            article_order = i + 1  # So "Artigo 1.º" is order 1, "Artigo 2.º" is order 2, etc.
            analysis = article_analyses.get(article_order, {})
            
            version_data = {
                'id': str(uuid.uuid4()),
                'law_id': law_id,
                'article_order': article_order,
                'mandate_id': "50259b5a-054e-4bbf-a39d-637e7d1c1f9f",  # Actual mandate ID
                'status_id': "ACTIVE",
                'valid_from': datetime.utcnow().date().isoformat(),
                'official_text': article['official_text'],
                'tags': analysis.get('tags', []),
                'translations': analysis.get('analysis', {})
            }
            
            response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
            version_ids.append(version_data['id'])
        
        return version_ids
    
    def _aggregate_tags_and_update_law(self, law_id: str) -> None:
        """Aggregate all tags from law_article_versions and update parent law."""
        
        # Get all tags from this law's article versions
        versions_response = self.supabase_admin.table('law_article_versions').select('tags').eq('law_id', law_id).execute()
        
        all_tags = []
        unique_tags = set()
        
        for version in versions_response.data:
            if version.get('tags'):
                for tag in version['tags']:
                    tag_key = f"{tag.get('type', '')}:{tag.get('name', '')}"
                    if tag_key not in unique_tags:
                        unique_tags.add(tag_key)
                        all_tags.append(tag)
        
        # Update the parent law with aggregated tags
        self.supabase_admin.table('laws').update({
            'tags': all_tags
        }).eq('id', law_id).execute()
    
    def _generate_and_store_law_summary(self, law_id: str, analysis_data: Dict[str, Any]) -> None:
        """Generate high-level law summary and store in translations field."""
        
        # Collect all individual summaries
        summaries_pt = []
        summaries_en = []
        
        for result in analysis_data['analysis_results']:
            analysis = result.get('analysis', {})
            if analysis.get('pt', {}).get('informal_summary'):
                summaries_pt.append(analysis['pt']['informal_summary'])
            if analysis.get('en', {}).get('informal_summary'):
                summaries_en.append(analysis['en']['informal_summary'])
        
        # Generate synthesized summary
        if summaries_pt:
            combined_summary_pt = "\n\n".join(summaries_pt)
            combined_summary_en = "\n\n".join(summaries_en)
            
            synthesis_prompt = f"""
            You are Kritis, an expert legal analyst. Create a high-level summary of this entire law based on its individual article analyses.

            Portuguese summaries:
            {combined_summary_pt}

            English summaries:
            {combined_summary_en}

            Return a JSON object with this structure:
            {{
                "pt": {{
                    "informal_summary_title": "Brief Portuguese title for the entire law",
                    "informal_summary": "High-level Portuguese summary of the law's overall purpose and impact"
                }},
                "en": {{
                    "informal_summary_title": "Brief English title for the entire law", 
                    "informal_summary": "High-level English summary of the law's overall purpose and impact"
                }}
            }}

            Return valid JSON only.
            """
            
            try:
                response = self.model.generate_content(synthesis_prompt)
                synthesis_text = response.text.strip()
                
                # Clean the response
                if synthesis_text.startswith('```json'):
                    synthesis_text = synthesis_text[7:]
                if synthesis_text.endswith('```'):
                    synthesis_text = synthesis_text[:-3]
                
                synthesis = json.loads(synthesis_text)
                
                # Update the law with synthesized summary
                self.supabase_admin.table('laws').update({
                    'translations': synthesis
                }).eq('id', law_id).execute()
                
            except Exception as e:
                logger.warning(f"⚠️ Law summary synthesis failed: {e}")
                # Use fallback summary
                fallback_summary = {
                    "pt": {
                        "informal_summary_title": "Lei analisada",
                        "informal_summary": "Esta lei foi processada pelo sistema Kritis."
                    },
                    "en": {
                        "informal_summary_title": "Analyzed law",
                        "informal_summary": "This law was processed by the Kritis system."
                    }
                }
                
                self.supabase_admin.table('laws').update({
                    'translations': fallback_summary
                }).eq('id', law_id).execute()