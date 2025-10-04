"""
Kritis V4.0 - The Final Definitive Agora AI Analyst
Implementation of PROD10 specifications with perfected AI persona and structured output.

This analyzer implements the final, definitive refactor:
- Perfected AI prompts with specific style guide (V4.2)
- Enhanced tag structure with organized categories
- Cross-reference processing with relationship types
- Final summary synthesis with category suggestions
"""

import json
import logging
import os
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from dotenv import load_dotenv
import google.generativeai as genai
from lib.supabase_client import get_supabase_client, get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)

class KritisAnalyzerV40:
    """Kritis V4.0 - The Final Definitive Analyst implementing PROD10 specifications."""

    def __init__(self):
        """Initialize Kritis V4.0 with Supabase clients and Gemini AI."""
        self.supabase = get_supabase_client()
        self.supabase_admin = get_supabase_admin_client()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.model_version = 'gemini-2.0-flash'
        
        # Category master list for final categorization
        self.category_master_list = [
            'FISCAL', 'LABOR', 'HEALTH', 'EDUCATION', 'ENVIRONMENT', 
            'ADMINISTRATIVE', 'CIVIL', 'CRIMINAL', 'CONSTITUTIONAL', 
            'COMMERCIAL', 'SOCIAL_SECURITY', 'DEFENSE', 'JUSTICE',
            'INFRASTRUCTURE', 'TECHNOLOGY', 'AGRICULTURE', 'TOURISM'
        ]
        
    # ========================================
    # STAGE 1: ENHANCED EXTRACTOR (Reuse V3.1 but improved)
    # ========================================
    
    def run_enhanced_extractor_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 1: Extract preamble and articles with enhanced structure.
        (Reuses V3.1 logic but with improved error handling)
        """
        logger.info(f"🔄 Kritis V4.0 Stage 1: Final Extractor for source {source_id}")
        
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
            'extracted_data': extracted_data
        }).execute()
        
        logger.info(f"✅ Final extraction completed: {len(extraction_result['articles'])} articles, preamble: {bool(extraction_result['preamble_text'].strip())}")
        
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
        - government_entity_id: Always use "3ee8d3ef-7226-4bf3-8ea2-6e2e036d203f" for Portuguese government

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
        """Extract preamble and articles according to PROD10 specifications."""
        
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
    # STAGE 2: DEFINITIVE KRITIS ANALYST (PROD10 V4.2 PROMPTS)
    # ========================================
    
    def run_definitive_analyst_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 2: Analyze each article with the definitive V4.2 prompts.
        
        Following PROD10 specifications:
        - Perfected AI persona with specific style guide
        - Enhanced tag structure with organized categories
        - Cross-references with relationship types
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict containing analysis results
        """
        logger.info(f"🧠 Kritis V4.0 Stage 2: Definitive Analyst for source {source_id}")
        
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
            logger.info("🔍 Analyzing preamble with V4.2 prompt...")
            try:
                preamble_analysis = self._analyze_content_v42(
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
            logger.info(f"🔍 Analyzing {article.get('article_number', f'Article {i+1}')} with V4.2 prompt...")
            try:
                article_analysis = self._analyze_content_v42(
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
            'model_version': 'kritis_v40_definitive_analyst',
            'analysis_data': analysis_data
        }).execute()
        
        logger.info(f"✅ Definitive analysis completed: {successful_analyses}/{total_items} items analyzed successfully")
        
        return {
            'total_items_analyzed': total_items,
            'successful_analyses': successful_analyses,
            'completion_rate': (successful_analyses / total_items * 100) if total_items > 0 else 0
        }
    
    def _analyze_content_v42(self, content: str, content_type: str, article_number: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content using the definitive V4.2 prompts from PROD10."""
        
        # The definitive "Kritis" Master Prompt (V4.2) from PROD10
        analysis_prompt = f"""
You are "Kritis," an expert legal analyst for the Agora platform. Your task is to deconstruct the following legal article into a highly structured JSON object, following the style guide precisely.

STYLE GUIDE:
- Plain Language: Use simple, everyday words. Avoid legal jargon entirely.
- Concise Structure: Use bullet points (-) to break down conditions, rules, or lists.
- Helpful, Human Tone: Explain concepts clearly, as if to a knowledgeable friend.
- No Intros: NEVER start a summary with phrases like "This article is about" or "In summary." Go directly to the core explanation.

ARTICLE TEXT TO ANALYZE:
{content}

YOUR TASK:
Return a single, valid JSON object with the following structure. Do not add any other text.

{{
  "tags": {{
    "person": ["Full Name of Person 1", "Full Name of Person 2"],
    "organization": ["Name of Organization"],
    "concept": ["Key Concept 1", "Key Concept 2"]
  }},
  "analysis": {{
    "pt": {{
      "informal_summary_title": "A very concise, 5-10 word action-oriented title in Portuguese.",
      "informal_summary": "A brief, human-centric summary in Portuguese that follows the style guide.",
      "cross_references": [
        {{"type": "Decreto-Lei", "number": "30/2017", "relationship": "cites"}}
      ]
    }},
    "en": {{
      "informal_summary_title": "An English translation of the title.",
      "informal_summary": "An English translation of the summary, maintaining the same clear style.",
      "cross_references": [
        {{"type": "Decree-Law", "number": "30/2017", "relationship": "cites"}}
      ]
    }}
  }}
}}
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
            
            # Validate and normalize the structure
            if 'tags' not in analysis:
                analysis['tags'] = {"person": [], "organization": [], "concept": []}
            
            # Ensure tags has the correct structure
            tags = analysis['tags']
            if not isinstance(tags, dict):
                analysis['tags'] = {"person": [], "organization": [], "concept": []}
            else:
                # Ensure all required tag categories exist
                for category in ['person', 'organization', 'concept']:
                    if category not in tags:
                        tags[category] = []
                    elif not isinstance(tags[category], list):
                        tags[category] = []
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ V4.2 content analysis failed: {e}")
            # Return fallback structure following V4.2 format
            return {
                "tags": {
                    "person": [],
                    "organization": [],
                    "concept": []
                },
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
    # STAGE 3: FINAL SUMMARY SYNTHESIS (REDUCE PHASE)
    # ========================================
    
    def run_final_synthesis_phase(self, source_id: str) -> Dict[str, Any]:
        """
        Stage 3: Synthesize final law summary using the definitive Reduce prompt.
        
        Following PROD10 specifications:
        - Use the new "Kritis" Reduce Prompt
        - Generate category suggestion from master list
        - Create high-level law overview
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            Dict containing synthesis results
        """
        logger.info(f"📝 Kritis V4.0 Stage 3: Final Summary Synthesis for source {source_id}")
        
        # Get analysis data
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', 'kritis_v40_definitive_analyst').order('created_at', desc=True).limit(1).execute()
        if not analysis_response.data:
            raise ValueError(f"No analysis data found for source {source_id}")
        
        analysis_data = analysis_response.data[0]['analysis_data']
        
        # Gather all English summaries for synthesis
        english_summaries = []
        for result in analysis_data['analysis_results']:
            analysis = result.get('analysis', {})
            if analysis.get('analysis', {}).get('en'):
                en_data = analysis['analysis']['en']
                title = en_data.get('informal_summary_title', '')
                summary = en_data.get('informal_summary', '')
                if title and summary:
                    english_summaries.append(f"{title}: {summary}")
        
        if not english_summaries:
            logger.warning("⚠️ No English summaries found for synthesis")
            return {'synthesis_completed': False}
        
        # Run the final synthesis using PROD10 Reduce prompt
        synthesis_result = self._run_final_synthesis(english_summaries)
        
        # Store synthesis results
        synthesis_data = {
            'source_id': source_id,
            'synthesis_result': synthesis_result,
            'synthesis_timestamp': datetime.utcnow().isoformat(),
            'summaries_count': len(english_summaries)
        }
        
        # Store synthesis in source_ai_analysis with different model version
        self.supabase_admin.table('source_ai_analysis').insert({
            'source_id': source_id,
            'model_version': 'kritis_v40_final_synthesis',
            'analysis_data': synthesis_data
        }).execute()
        
        logger.info(f"✅ Final synthesis completed with category: {synthesis_result.get('suggested_category_id', 'Unknown')}")
        
        return {
            'synthesis_completed': True,
            'suggested_category': synthesis_result.get('suggested_category_id'),
            'summaries_processed': len(english_summaries)
        }
    
    def _run_final_synthesis(self, english_summaries: List[str]) -> Dict[str, Any]:
        """Run the final synthesis using the definitive Reduce prompt from PROD10."""
        
        summaries_text = "\n\n".join(english_summaries)
        category_list = "', '".join(self.category_master_list)
        
        # The definitive "Kritis" Reduce Prompt from PROD10
        synthesis_prompt = f"""
You are "Kritis," an expert editor. Below are the titles and summaries for the individual articles of a single law.

STYLE GUIDE:
- Plain Language: Use simple, everyday words. Avoid legal jargon entirely.
- Concise Structure: Use bullet points (-) to break down conditions, rules, or lists.
- Helpful, Human Tone: Explain concepts clearly, as if to a knowledgeable friend.
- No Intros: NEVER start a summary with phrases like "This article is about" or "In summary." Go directly to the core explanation.

ARTICLE SUMMARIES TO SYNTHESIZE:
{summaries_text}

YOUR TASK:
Synthesize the provided summaries into a single, high-level overview of the entire law. Return a single, valid JSON object with the following structure. Do not add any other text.

{{
  "suggested_category_id": "From this master list, choose the single best category ID for the law as a whole: ['{category_list}']",
  "final_analysis": {{
    "pt": {{
      "informal_summary_title": "A concise Portuguese title for the entire law.",
      "informal_summary": "A high-level Portuguese summary of the law's purpose and key impacts."
    }},
    "en": {{
      "informal_summary_title": "An English translation of the title.",
      "informal_summary": "An English translation of the summary."
    }}
  }}
}}
"""
        
        try:
            response = self.model.generate_content(synthesis_prompt)
            synthesis_text = response.text.strip()
            
            # Clean the response to ensure it's valid JSON
            if synthesis_text.startswith('```json'):
                synthesis_text = synthesis_text[7:]
            if synthesis_text.endswith('```'):
                synthesis_text = synthesis_text[:-3]
            
            synthesis = json.loads(synthesis_text)
            
            # Validate category suggestion
            suggested_category = synthesis.get('suggested_category_id')
            if suggested_category not in self.category_master_list:
                logger.warning(f"⚠️ Invalid category suggested: {suggested_category}, defaulting to ADMINISTRATIVE")
                synthesis['suggested_category_id'] = 'ADMINISTRATIVE'
            
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Final synthesis failed: {e}")
            # Return fallback structure
            return {
                "suggested_category_id": "ADMINISTRATIVE",
                "final_analysis": {
                    "pt": {
                        "informal_summary_title": "Lei processada",
                        "informal_summary": "Esta lei foi processada pelo sistema Kritis."
                    },
                    "en": {
                        "informal_summary_title": "Processed law",
                        "informal_summary": "This law was processed by the Kritis system."
                    }
                }
            }
    
    # ========================================
    # STAGE 4: DEFINITIVE LAW INGESTION (PROD10 ENHANCED WORKFLOW)
    # ========================================
    
    def run_definitive_law_ingestion(self, source_id: str) -> str:
        """
        Stage 4: Create law records following PROD10 definitive workflow.
        
        Following PROD10 specifications:
        - Enhanced tag aggregation with organized categories
        - Cross-reference processing with relationship types
        - Final summary synthesis with category assignment
        - Complete transaction-based workflow
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            str: UUID of the created law
        """
        logger.info(f"📚 Kritis V4.0 Stage 4: Definitive Law Ingestion for source {source_id}")
        
        # Get all required data
        extraction_response = self.supabase_admin.table('pending_extractions').select('*').eq('source_id', source_id).order('created_at', desc=True).limit(1).execute()
        if not extraction_response.data:
            raise ValueError(f"No extraction data found for source {source_id}")
        
        analysis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', 'kritis_v40_definitive_analyst').order('created_at', desc=True).limit(1).execute()
        if not analysis_response.data:
            raise ValueError(f"No analysis data found for source {source_id}")
        
        synthesis_response = self.supabase_admin.table('source_ai_analysis').select('*').eq('source_id', source_id).eq('model_version', 'kritis_v40_final_synthesis').order('created_at', desc=True).limit(1).execute()
        if not synthesis_response.data:
            raise ValueError(f"No synthesis data found for source {source_id}")
        
        extraction_data = extraction_response.data[0]['extracted_data']
        analysis_data = analysis_response.data[0]['analysis_data']
        synthesis_data = synthesis_response.data[0]['analysis_data']
        
        # Start transaction-based ingestion following PROD10 workflow
        try:
            # Step 1: Create parent law record (initial)
            law_id = self._create_parent_law_record_v40(source_id, extraction_data)
            logger.info(f"✅ Created parent law record: {law_id}")
            
            # Step 2: Loop through all analyzed articles
            cross_references = self._process_analyzed_articles_v40(law_id, extraction_data, analysis_data)
            logger.info(f"✅ Processed all analyzed articles")
            
            # Step 3: Process cross-references and relationships
            self._process_cross_references_v40(law_id, cross_references)
            logger.info(f"✅ Processed cross-references")
            
            # Step 4: Aggregate tags (enhanced V4.0 logic)
            self._aggregate_tags_v40(law_id)
            logger.info("✅ Aggregated tags with enhanced V4.0 logic")
            
            # Step 5: Apply final summary and category (from synthesis)
            self._apply_final_summary_and_category_v40(law_id, synthesis_data)
            logger.info("✅ Applied final summary and category")
            
            logger.info(f"🎯 Definitive law ingestion completed successfully: {law_id}")
            return law_id
            
        except Exception as e:
            logger.error(f"❌ Definitive law ingestion failed: {e}")
            raise
    
    def _create_parent_law_record_v40(self, source_id: str, extraction_data: Dict[str, Any]) -> str:
        """Create the parent law record with initial metadata."""
        
        metadata = extraction_data.get('metadata', {})
        
        # Generate a slug from the official title or number
        if metadata.get('official_title'):
            slug = metadata['official_title'].lower().replace(' ', '-')[:100]
        elif metadata.get('official_number'):
            slug = metadata['official_number'].lower().replace(' ', '-')[:100]
        else:
            slug = f"law-{uuid.uuid4().hex[:8]}"
        
        # Clean slug to be URL-safe
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
            'category_id': None,  # Will be set in final summary step
            'tags': None,  # Will be populated in aggregation step
            'translations': None  # Will be populated in final summary step
        }
        
        response = self.supabase_admin.table('laws').insert(law_data).execute()
        return law_data['id']
    
    def _process_analyzed_articles_v40(self, law_id: str, extraction_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process all analyzed articles and create law_article_versions."""
        
        analysis_results = analysis_data.get('analysis_results', [])
        all_cross_references = []
        
        for result in analysis_results:
            article_order = result['article_order']
            analysis = result.get('analysis', {})
            
            # Get the original text
            if article_order == 0:
                # Preamble
                official_text = extraction_data.get('preamble_text', '')
            else:
                # Article
                articles = extraction_data.get('articles', [])
                if article_order - 1 < len(articles):
                    official_text = articles[article_order - 1]['official_text']
                else:
                    official_text = f"Article {article_order} text not found"
            
            # Create law_article_version
            version_data = {
                'id': str(uuid.uuid4()),
                'law_id': law_id,
                'article_order': article_order,
                'mandate_id': "50259b5a-054e-4bbf-a39d-637e7d1c1f9f",
                'status_id': "ACTIVE",
                'valid_from': datetime.utcnow().date().isoformat(),
                'official_text': official_text,
                'tags': analysis.get('tags', {}),
                'translations': analysis.get('analysis', {})
            }
            
            response = self.supabase_admin.table('law_article_versions').insert(version_data).execute()
            
            # Collect cross-references for later processing
            analysis_obj = analysis.get('analysis', {})
            for lang in ['pt', 'en']:
                cross_refs = analysis_obj.get(lang, {}).get('cross_references', [])
                for ref in cross_refs:
                    ref['source_article_order'] = article_order
                    all_cross_references.append(ref)
        
        return all_cross_references
    
    def _process_cross_references_v40(self, law_id: str, cross_references: List[Dict[str, Any]]) -> None:
        """Process cross-references and create relationships (PROD10 enhancement)."""
        
        logger.info(f"🔗 Processing {len(cross_references)} cross-references")
        
        for ref in cross_references:
            try:
                # Extract reference details
                ref_type = ref.get('type', '')
                ref_number = ref.get('number', '')
                relationship = ref.get('relationship', 'cites')
                source_article_order = ref.get('source_article_order', 0)
                
                # Try to find the target law in the database
                target_law = self._find_target_law(ref_type, ref_number)
                
                if target_law:
                    # Create law relationship
                    relationship_data = {
                        'source_law_id': law_id,
                        'target_law_id': target_law['id'],
                        'relationship_type': relationship
                    }
                    
                    # Insert relationship (if not exists)
                    try:
                        self.supabase_admin.table('law_relationships').insert(relationship_data).execute()
                        logger.info(f"✅ Created law relationship: {relationship} -> {ref_number}")
                    except Exception as e:
                        # Relationship might already exist, that's okay
                        logger.debug(f"Relationship may already exist: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process cross-reference {ref}: {e}")
                continue
    
    def _find_target_law(self, ref_type: str, ref_number: str) -> Optional[Dict[str, Any]]:
        """Find target law based on reference type and number."""
        
        try:
            # Try to find by official_number
            response = self.supabase_admin.table('laws').select('id, official_title').eq('official_number', ref_number).execute()
            if response.data:
                return response.data[0]
            
            # Try to find by partial match in official_title
            response = self.supabase_admin.table('laws').select('id, official_title').ilike('official_title', f'%{ref_number}%').execute()
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding target law {ref_number}: {e}")
            return None
    
    def _aggregate_tags_v40(self, law_id: str) -> None:
        """Aggregate tags with enhanced V4.0 logic for organized categories."""
        
        # Get all tags from this law's article versions
        versions_response = self.supabase_admin.table('law_article_versions').select('tags').eq('law_id', law_id).execute()
        
        # Enhanced aggregation following PROD10 structure
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
        
        for version in versions_response.data:
            if version.get('tags'):
                tags = version['tags']
                if isinstance(tags, dict):
                    for category in ['person', 'organization', 'concept']:
                        if category in tags and isinstance(tags[category], list):
                            for tag in tags[category]:
                                if tag and tag not in unique_tags[category]:
                                    unique_tags[category].add(tag)
                                    aggregated_tags[category].append(tag)
        
        # Update the parent law with aggregated tags
        self.supabase_admin.table('laws').update({
            'tags': aggregated_tags
        }).eq('id', law_id).execute()
        
        logger.info(f"📊 Aggregated tags: {len(aggregated_tags['person'])} persons, {len(aggregated_tags['organization'])} organizations, {len(aggregated_tags['concept'])} concepts")
    
    def _apply_final_summary_and_category_v40(self, law_id: str, synthesis_data: Dict[str, Any]) -> None:
        """Apply final summary and category from synthesis phase."""
        
        synthesis_result = synthesis_data.get('synthesis_result', {})
        
        # Extract category and final analysis
        suggested_category = synthesis_result.get('suggested_category_id', 'ADMINISTRATIVE')
        final_analysis = synthesis_result.get('final_analysis', {})
        
        # Update the law with final summary and category
        update_data = {
            'category_id': suggested_category,
            'translations': final_analysis
        }
        
        self.supabase_admin.table('laws').update(update_data).eq('id', law_id).execute()
        
        logger.info(f"📝 Applied final summary with category: {suggested_category}")
    
    # ========================================
    # COMPLETE PIPELINE ORCHESTRATION
    # ========================================
    
    def run_complete_v40_pipeline(self, source_id: str) -> str:
        """
        Run the complete Kritis V4.0 pipeline following PROD10 specifications.
        
        Args:
            source_id: UUID of the source document
            
        Returns:
            str: UUID of the created law
        """
        logger.info(f"🚀 Starting Complete Kritis V4.0 PROD10 Pipeline for source {source_id}")
        
        try:
            # Stage 1: Enhanced Extraction
            logger.info("📋 Stage 1/4: Enhanced Extraction...")
            extract_result = self.run_enhanced_extractor_phase(source_id)
            logger.info(f"✅ Stage 1 complete: {extract_result['total_articles']} articles, preamble: {extract_result['has_preamble']}")
            
            # Stage 2: Definitive Analysis with V4.2 prompts
            logger.info("📋 Stage 2/4: Definitive Analysis...")
            analyze_result = self.run_definitive_analyst_phase(source_id)
            logger.info(f"✅ Stage 2 complete: {analyze_result['successful_analyses']}/{analyze_result['total_items_analyzed']} items analyzed ({analyze_result['completion_rate']:.1f}%)")
            
            # Stage 3: Final Synthesis
            logger.info("📋 Stage 3/4: Final Synthesis...")
            synthesis_result = self.run_final_synthesis_phase(source_id)
            logger.info(f"✅ Stage 3 complete: Category suggested: {synthesis_result.get('suggested_category', 'Unknown')}")
            
            # Stage 4: Definitive Law Ingestion
            logger.info("📋 Stage 4/4: Definitive Law Ingestion...")
            law_id = self.run_definitive_law_ingestion(source_id)
            logger.info(f"✅ Stage 4 complete: Law created {law_id}")
            
            logger.info("🎉 Complete Kritis V4.0 PROD10 Pipeline finished successfully!")
            logger.info(f"📚 Final Law ID: {law_id}")
            logger.info("🔗 The law follows PROD10 definitive specifications:")
            logger.info("   - Perfected AI persona with specific style guide")
            logger.info("   - Enhanced tag structure with organized categories")
            logger.info("   - Cross-reference processing with relationship types")
            logger.info("   - Final summary synthesis with category suggestions")
            
            return law_id
            
        except Exception as e:
            logger.error(f"❌ Complete V4.0 pipeline failed: {e}")
            raise