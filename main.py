#!/usr/bin/env python3
"""
Agora Analyst - AI Analysis Service for Legal Documents
CLI entry point for the Kritis analysis pipeline.

Production-ready version with enhanced error handling and monitoring.
Active Workflows: V4.0 (PROD10), V5.0 (Enhanced Relationships)
"""

import argparse
import logging
import sys
import os
import uuid
from datetime import datetime
from analysis.kritis_analyzer_v40 import KritisAnalyzerV40
from analysis.kritis_analyzer_v50 import KritisAnalyzerV50
from lib.supabase_client import get_supabase_admin_client

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')

logging.basicConfig(
    level=getattr(logging, log_level),
    format=log_format
)
logger = logging.getLogger(__name__)

def validate_uuid(source_id: str) -> bool:
    """Validate that source_id is a proper UUID format."""
    try:
        uuid.UUID(source_id)
        return True
    except ValueError:
        return False

def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_ANON_KEY',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ Environment validation passed")
    return True

def update_job_status(job_id: str | None, status: str, result_message: str) -> None:
    """
    Update the status of a background job in the database.
    
    Args:
        job_id: UUID of the job to update (optional)
        status: Job status (SUCCESS or FAILED)
        result_message: Message describing the result
        
    Note: This function is designed to be resilient. It will never raise exceptions
          or break the main analysis pipeline. Job notifications are optional.
    """
    if not job_id:
        return
    
    try:
        logger.info(f"📝 Updating job {job_id} to status: {status}")
        supabase = get_supabase_admin_client()
        
        supabase.table("background_jobs").update({
            "status": status,
            "result_message": result_message,
            "updated_at": datetime.now().isoformat()  # Use timezone-aware datetime
        }).eq("id", job_id).execute()
        
        logger.info(f"✅ Job status updated successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to update job status (non-critical): {e}")
        # Don't raise - job notifications are optional and should never break the analysis

def main():
    parser = argparse.ArgumentParser(
        description='Agora Analyst - AI Analysis Service for Legal Documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Kritis V4.0 (PROD10) - Complete Pipeline
  python main.py --source-id <UUID> v40-complete
  
  # Kritis V4.0 (PROD10) - Individual Stages
  python main.py --source-id <UUID> v40-extract
  python main.py --source-id <UUID> v40-analyze
  python main.py --source-id <UUID> v40-synthesize
  python main.py --source-id <UUID> v40-ingest
  
  # Kritis V5.0 (Enhanced Relationships) - Complete Pipeline (RECOMMENDED)
  python main.py --source-id <UUID> v50-complete
  
  # Kritis V5.0 (Enhanced Relationships) - Individual Stages
  python main.py --source-id <UUID> v50-extract
  python main.py --source-id <UUID> v50-analyze
  python main.py --source-id <UUID> v50-build-graph
  
  # Background job notification (optional)
  python main.py --source-id <UUID> --job-id <JOB_UUID> v50-complete
        """
    )
    
    # Add global arguments BEFORE subparsers (so they work with all commands)
    parser.add_argument(
        '--source-id',
        required=False,  # Changed to False - only required for analysis commands
        help='UUID of the source document to analyze'
    )
    
    parser.add_argument(
        '--job-id',
        required=False,
        help='Optional: UUID of the background job for status tracking'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Workflow Discovery Command
    describe_workflows_parser = subparsers.add_parser(
        'describe-workflows',
        help='List all available workflows as JSON manifest (for dynamic integration)'
    )
    
    # Kritis V4.0 Commands - PROD10 Final Definitive Pipeline
    v40_stage1_parser = subparsers.add_parser(
        'v40-extract',
        help='Kritis V4.0 Stage 1: PROD10 enhanced extractor'
    )
    
    v40_stage2_parser = subparsers.add_parser(
        'v40-analyze',
        help='Kritis V4.0 Stage 2: PROD10 definitive analyst with V4.2 prompts'
    )
    
    v40_stage3_parser = subparsers.add_parser(
        'v40-synthesize',
        help='Kritis V4.0 Stage 3: PROD10 final summary synthesis with category suggestions'
    )
    
    v40_stage4_parser = subparsers.add_parser(
        'v40-ingest',
        help='Kritis V4.0 Stage 4: PROD10 definitive law ingestion with cross-references'
    )
    
    v40_complete_parser = subparsers.add_parser(
        'v40-complete',
        help='Kritis V4.0 Complete Pipeline: Run all PROD10 stages'
    )
    
    # Kritis V5.0 Commands - Enhanced Relationship Processing (RECOMMENDED)
    v50_stage1_parser = subparsers.add_parser(
        'v50-extract',
        help='Kritis V5.0 Stage 1: Enhanced extractor with HTML preservation'
    )
    
    v50_stage2_parser = subparsers.add_parser(
        'v50-analyze',
        help='Kritis V5.0 Stage 2: Enhanced analyst with cross-reference extraction (URLs + article numbers)'
    )
    
    v50_stage3_parser = subparsers.add_parser(
        'v50-build-graph',
        help='Kritis V5.0 Stage 3: Knowledge Graph Builder with consistent relationships'
    )
    
    v50_complete_parser = subparsers.add_parser(
        'v50-complete',
        help='Kritis V5.0 Complete Pipeline: Run all stages with enhanced relationship processing (RECOMMENDED)'
    )
    
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle describe-workflows command (doesn't require validation or source_id)
    if args.command == 'describe-workflows':
        import json
        workflows = [
            {
                "id": "v40-complete",
                "name": "Kritis V4.0 - Complete Pipeline (PROD10)",
                "description": "Runs the complete V4.0 pipeline with all 4 stages: extraction, analysis, synthesis, and law ingestion. This is the production-ready PROD10 version.",
                "stages": ["extract", "analyze", "synthesize", "ingest"],
                "version": "4.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v40-extract",
                "name": "Kritis V4.0 - Extraction Only",
                "description": "Runs only the PROD10 enhanced extraction stage. Extracts preamble and articles from legal documents.",
                "stages": ["extract"],
                "version": "4.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v40-analyze",
                "name": "Kritis V4.0 - Analysis Only",
                "description": "Runs only the PROD10 analysis stage with V4.2 prompts. Analyzes extracted content.",
                "stages": ["analyze"],
                "version": "4.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v40-synthesize",
                "name": "Kritis V4.0 - Synthesis Only",
                "description": "Runs only the PROD10 synthesis stage. Creates final summary and category suggestions.",
                "stages": ["synthesize"],
                "version": "4.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v40-ingest",
                "name": "Kritis V4.0 - Ingestion Only",
                "description": "Runs only the PROD10 law ingestion stage. Creates law records with cross-references.",
                "stages": ["ingest"],
                "version": "4.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v50-complete",
                "name": "Kritis V5.0 - Complete Pipeline (Enhanced Relationships)",
                "description": "Runs the complete V5.0 pipeline with enhanced relationship processing. Features URL-based reference matching, law-to-law and article-to-article relationships, temporal validation, and automatic status updates. RECOMMENDED for new documents.",
                "stages": ["extract", "analyze", "build-graph"],
                "version": "5.0",
                "status": "stable",
                "recommended": True,
                "features": [
                    "URL-based reference matching",
                    "Law-to-law relationships",
                    "Article-to-article relationships",
                    "Preamble cross-reference processing",
                    "Temporal consistency validation",
                    "Automatic status updates (superseded/revoked)",
                    "Conflict resolution with delete_law_and_children()"
                ]
            },
            {
                "id": "v50-extract",
                "name": "Kritis V5.0 - Extraction Only",
                "description": "Runs only the enhanced extraction stage with HTML preservation.",
                "stages": ["extract"],
                "version": "5.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v50-analyze",
                "name": "Kritis V5.0 - Analysis Only",
                "description": "Runs only the enhanced analysis stage with cross-reference extraction (URLs + article numbers).",
                "stages": ["analyze"],
                "version": "5.0",
                "status": "stable",
                "recommended": False
            },
            {
                "id": "v50-build-graph",
                "name": "Kritis V5.0 - Knowledge Graph Builder Only",
                "description": "Runs only the knowledge graph building stage with consistent relationship processing.",
                "stages": ["build-graph"],
                "version": "5.0",
                "status": "stable",
                "recommended": False
            }
        ]
        print(json.dumps(workflows, indent=2))
        return
    
    # Production validation (required for all other commands)
    if not validate_environment():
        logger.error("❌ Environment validation failed")
        sys.exit(1)
    
    if not hasattr(args, 'source_id') or not args.source_id or not validate_uuid(args.source_id):
        logger.error(f"❌ Invalid source ID format. Expected UUID, got: {getattr(args, 'source_id', 'None')}")
        sys.exit(1)
    
    # Get job_id if provided for background job tracking
    job_id = getattr(args, 'job_id', None)
    if job_id:
        logger.info(f"📌 Background job ID: {job_id}")
    
    logger.info(f"🚀 Starting Kritis Analysis for Source ID: {args.source_id}")
    logger.info(f"📋 Command: {args.command}")

    try:
        # ========================================
        # KRITIS V4.0 COMMANDS (PROD10)
        # ========================================
        
        if args.command == 'v40-extract':

            # Kritis V4.0 Stage 1: PROD10 Enhanced Extractor
            logger.info("🚀 Using Kritis V4.0 PROD10 Pipeline")
            kritis_v40 = KritisAnalyzerV40()
            result = kritis_v40.run_enhanced_extractor_phase(args.source_id)
            logger.info("🎯 Kritis V4.0 Stage 1 completed successfully")
            logger.info(f"📄 PROD10 Extraction Results:")
            logger.info(f"Total Articles Found: {result['total_articles']}")
            logger.info(f"Has Preamble: {'Yes' if result['has_preamble'] else 'No'}")
            if result['metadata']:
                logger.info(f"Official Number: {result['metadata'].get('official_number', 'N/A')}")
                logger.info(f"Title: {result['metadata'].get('official_title', 'N/A')}")
                logger.info(f"Type: {result['metadata'].get('law_type_id', 'N/A')}")
                logger.info(f"Date: {result['metadata'].get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py v40-analyze --source-id " + args.source_id)
            
        elif args.command == 'v40-analyze':
            # Kritis V4.0 Stage 2: PROD10 Definitive Analyst with V4.2 prompts
            kritis_v40 = KritisAnalyzerV40()
            result = kritis_v40.run_definitive_analyst_phase(args.source_id)
            logger.info("🎯 Kritis V4.0 Stage 2 completed successfully")
            logger.info(f"📊 PROD10 Analysis Results (V4.2 prompts):")
            logger.info(f"Items Analyzed: {result['total_items_analyzed']}")
            logger.info(f"Successful Analyses: {result['successful_analyses']}")
            logger.info(f"Completion Rate: {result['completion_rate']:.1f}%")
            
            if result['successful_analyses'] < result['total_items_analyzed']:
                failed = result['total_items_analyzed'] - result['successful_analyses']
                logger.warning(f"⚠️ {failed} items had analysis errors and will use fallback data")
            
            logger.info("📋 Next step: python main.py v40-synthesize --source-id " + args.source_id)
            
        elif args.command == 'v40-synthesize':
            # Kritis V4.0 Stage 3: PROD10 Final Summary Synthesis
            kritis_v40 = KritisAnalyzerV40()
            result = kritis_v40.run_final_synthesis_phase(args.source_id)
            logger.info("🎯 Kritis V4.0 Stage 3 completed successfully")
            logger.info(f"📝 PROD10 Synthesis Results:")
            logger.info(f"Synthesis Completed: {'Yes' if result['synthesis_completed'] else 'No'}")
            logger.info(f"Suggested Category: {result.get('suggested_category', 'Unknown')}")
            logger.info(f"Summaries Processed: {result.get('summaries_processed', 0)}")
            
            logger.info("📋 Next step: python main.py v40-ingest --source-id " + args.source_id)
            
        elif args.command == 'v40-ingest':
            # Kritis V4.0 Stage 4: PROD10 Definitive Law Ingestion
            kritis_v40 = KritisAnalyzerV40()
            law_id = kritis_v40.run_definitive_law_ingestion(args.source_id)
            logger.info(f"🎯 Kritis V4.0 Stage 4 completed successfully")
            logger.info(f"📚 Law created with PROD10 definitive specifications: {law_id}")
            logger.info("✅ Full Kritis V4.0 PROD10 Pipeline completed!")
            
        elif args.command == 'v40-complete':
            # Kritis V4.0 Complete Pipeline: All stages in sequence
            logger.info("🚀 Starting Kritis V4.0 Complete PROD10 Pipeline")
            kritis_v40 = KritisAnalyzerV40()
            
            law_id = kritis_v40.run_complete_v40_pipeline(args.source_id)
            
            logger.info("🎉 Complete Kritis V4.0 PROD10 Pipeline finished successfully!")
            logger.info(f"📚 Final Law ID: {law_id}")
            logger.info("🔗 The law follows the PROD10 definitive specifications:")
            logger.info("   - Perfected AI persona with specific style guide")
            logger.info("   - Enhanced tag structure with organized categories")
            logger.info("   - Cross-reference processing with relationship types")
            logger.info("   - Final summary synthesis with category suggestions")
        
        # ========================================
        # KRITIS V5.0 COMMANDS (ENHANCED RELATIONSHIPS) - RECOMMENDED
        # ========================================
        
        elif args.command == 'v50-extract':
            # Kritis V5.0 Stage 1: Enhanced Extractor
            logger.info("🚀 Using Kritis V5.0 Enhanced Relationship Pipeline (RECOMMENDED)")
            kritis_v50 = KritisAnalyzerV50()
            result = kritis_v50.run_enhanced_extractor_phase(args.source_id)
            logger.info("🎯 Kritis V5.0 Stage 1 completed successfully")
            logger.info(f"📄 Extraction Results:")
            logger.info(f"Total Articles: {result['total_articles']}")
            logger.info(f"Has Preamble: {'Yes' if result['has_preamble'] else 'No'}")
            if result['metadata']:
                logger.info(f"Official Number: {result['metadata'].get('official_number', 'N/A')}")
                logger.info(f"Title: {result['metadata'].get('official_title', 'N/A')}")
                logger.info(f"Date: {result['metadata'].get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py v50-analyze --source-id " + args.source_id)
        
        elif args.command == 'v50-analyze':
            # Kritis V5.0 Stage 2: Enhanced Analyst with Cross-References
            kritis_v50 = KritisAnalyzerV50()
            result = kritis_v50.run_kritis_v50_analyst_phase(args.source_id)
            logger.info("🎯 Kritis V5.0 Stage 2 completed successfully")
            logger.info(f"📊 Enhanced Analysis with Cross-References:")
            logger.info(f"Items Analyzed: {result['total_items_analyzed']}")
            logger.info(f"Successful: {result['successful_analyses']}")
            logger.info(f"Completion Rate: {result['completion_rate']:.1f}%")
            logger.info("📋 Next step: python main.py v50-build-graph --source-id " + args.source_id)
        
        elif args.command == 'v50-build-graph':
            # Kritis V5.0 Stage 3: Knowledge Graph Builder
            kritis_v50 = KritisAnalyzerV50()
            result = kritis_v50.run_knowledge_graph_builder_phase(args.source_id)
            logger.info("🎯 Kritis V5.0 Stage 3 completed successfully")
            logger.info(f"📚 Law created with enhanced relationship graph: {result['law_id']}")
            logger.info(f"🔗 Relationships Created:")
            logger.info(f"   - Law-to-Law: {result['relationships_created']['law_relationships']}")
            logger.info(f"   - Article-to-Article: {result['relationships_created']['article_references']}")
            logger.info("✅ Full Kritis V5.0 Pipeline completed!")
        
        elif args.command == 'v50-complete':
            # Kritis V5.0 Complete Pipeline: All stages in sequence
            logger.info("🚀 Starting Kritis V5.0 Complete Enhanced Relationship Pipeline (RECOMMENDED)")
            kritis_v50 = KritisAnalyzerV50()
            
            # Stage 1: Extract
            logger.info("📋 Stage 1/3: Enhanced Extraction...")
            extract_result = kritis_v50.run_enhanced_extractor_phase(args.source_id)
            logger.info(f"✅ Stage 1 complete: {extract_result['total_articles']} articles")
            
            # Stage 2: Analyze with Enhanced Cross-References
            logger.info("📋 Stage 2/3: Enhanced Analysis with Cross-References...")
            analyze_result = kritis_v50.run_kritis_v50_analyst_phase(args.source_id)
            logger.info(f"✅ Stage 2 complete: {analyze_result['successful_analyses']}/{analyze_result['total_items_analyzed']} items ({analyze_result['completion_rate']:.1f}%)")
            
            # Stage 3: Build Knowledge Graph
            logger.info("📋 Stage 3/3: Knowledge Graph Building...")
            graph_result = kritis_v50.run_knowledge_graph_builder_phase(args.source_id)
            logger.info(f"✅ Stage 3 complete: Law {graph_result['law_id']}")
            
            logger.info("🎉 Complete Kritis V5.0 Pipeline finished successfully!")
            logger.info(f"📚 Final Law ID: {graph_result['law_id']}")
            logger.info("🔗 Enhanced Relationship Features:")
            logger.info(f"   - URL-based reference matching (reliable)")
            logger.info(f"   - Article-to-article relationships: {graph_result['relationships_created']['article_references']}")
            logger.info(f"   - Law-to-law relationships: {graph_result['relationships_created']['law_relationships']}")
            logger.info("   - Temporal consistency validation")
            logger.info("   - Automatic status updates (superseded/revoked)")
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Analysis interrupted by user")
        update_job_status(
            job_id=job_id,
            status="FAILED",
            result_message="Analysis interrupted by user"
        )
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        logger.error(f"📊 Analysis Summary:")
        logger.error(f"   - Source ID: {args.source_id}")
        logger.error(f"   - Command: {args.command}")
        logger.error(f"   - Error: {str(e)}")
        if log_level == 'DEBUG':
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        
        # Update job status on error
        update_job_status(
            job_id=job_id,
            status="FAILED",
            result_message=f"Error: {str(e)}"
        )
        sys.exit(1)
    else:
        # Update job status on success
        update_job_status(
            job_id=job_id,
            status="SUCCESS",
            result_message=f"Successfully completed {args.command} for source {args.source_id}"
        )
    
    logger.info("🎉 Analysis completed successfully!")

if __name__ == "__main__":
    main()