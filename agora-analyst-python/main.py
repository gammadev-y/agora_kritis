#!/usr/bin/env python3
"""
Agora Analyst - AI Analysis Service for Legal Documents
CLI entry point for the Kritis 4.0 analysis pipeline.

Production-ready version with enhanced error handling and monitoring.
"""

import argparse
import logging
import sys
import os
import uuid
from analysis.document_analyzer import DocumentAnalyzer
from analysis.kritis_analyzer import KritisAnalyzer
from analysis.kritis_analyzer_v2 import KritisAnalyzerV2
from analysis.kritis_analyzer_v3 import KritisAnalyzerV3
from analysis.kritis_analyzer_v4 import KritisAnalyzerV4
from analysis.kritis_analyzer_v31 import KritisAnalyzerV31

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

def main():
    parser = argparse.ArgumentParser(
        description='Agora Analyst - AI Analysis Service for Legal Documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Legacy single-stage analysis
  python main.py analyze-source --source-id 12345678-1234-1234-1234-123456789abc
  
  # Kritis 1.0 3-stage pipeline  
  python main.py analyze-chunks --source-id 12345678-1234-1234-1234-123456789abc
  python main.py synthesize-summary --source-id 12345678-1234-1234-1234-123456789abc  
  python main.py ingest-law --source-id 12345678-1234-1234-1234-123456789abc
  
  # Kritis 2.0 Enhanced 4-stage pipeline
  python main.py extract-metadata --source-id 12345678-1234-1234-1234-123456789abc
  python main.py analyze-enhanced --source-id 12345678-1234-1234-1234-123456789abc
  python main.py build-knowledge-graph --source-id 12345678-1234-1234-1234-123456789abc
  
  # Kritis 3.0 Multi-Article Processing pipeline
  python main.py parse-articles --source-id 12345678-1234-1234-1234-123456789abc
  python main.py batch-analyze --source-id 12345678-1234-1234-1234-123456789abc
  python main.py build-multi-article-graph --source-id 12345678-1234-1234-1234-123456789abc
  
  # Kritis 4.0 Enhanced Analysis with Preamble and Intelligent Tagging
  python main.py enhanced-extract --source-id 12345678-1234-1234-1234-123456789abc
  python main.py enhanced-analyze-context --source-id 12345678-1234-1234-1234-123456789abc
  python main.py intelligent-graph --source-id 12345678-1234-1234-1234-123456789abc
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Legacy command for backward compatibility
    legacy_parser = subparsers.add_parser(
        'analyze-source', 
        help='Legacy: Run complete analysis in single stage (deprecated)'
    )
    legacy_parser.add_argument(
        '--source-id', 
        required=True, 
        help='UUID of the source document to analyze'
    )
    
    # Kritis 1.0 Commands
    stage1_parser = subparsers.add_parser(
        'analyze-chunks',
        help='Kritis 1.0 Stage 1: Analyze document chunks individually'
    )
    stage1_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to analyze'
    )
    
    stage2_parser = subparsers.add_parser(
        'synthesize-summary',
        help='Kritis 1.0 Stage 2: Synthesize chunk analyses into document summary'
    )
    stage2_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to synthesize'
    )
    
    stage3_parser = subparsers.add_parser(
        'ingest-law',
        help='Kritis 1.0 Stage 3: Create structured law records from analysis'
    )
    stage3_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to ingest as law'
    )
    
    # Kritis 2.0 Commands
    v2_stage1_parser = subparsers.add_parser(
        'extract-metadata',
        help='Kritis 2.0 Stage 1-2: Extract core metadata from first chunk'
    )
    v2_stage1_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to extract metadata from'
    )
    
    v2_stage2_parser = subparsers.add_parser(
        'analyze-enhanced',
        help='Kritis 2.0 Stage 3: Enhanced structured analysis with categories and entities'
    )
    v2_stage2_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to analyze'
    )
    
    v2_stage3_parser = subparsers.add_parser(
        'build-knowledge-graph',
        help='Kritis 2.0 Stage 4: Build knowledge graph with tagging and relationships'
    )
    v2_stage3_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to build knowledge graph from'
    )
    
    # Kritis 3.0 Commands - Multi-Article Processing
    v3_stage1_parser = subparsers.add_parser(
        'parse-articles',
        help='Kritis 3.0 Stage 1: Parse and separate multiple articles from chunks'
    )
    v3_stage1_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to parse articles from'
    )
    
    v3_stage2_parser = subparsers.add_parser(
        'batch-analyze',
        help='Kritis 3.0 Stage 2: Batch analysis of multiple articles with smart token management'
    )
    v3_stage2_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to batch analyze'
    )
    
    v3_stage3_parser = subparsers.add_parser(
        'build-multi-article-graph',
        help='Kritis 3.0 Stage 3: Build knowledge graph with multiple articles and enhanced relationships'
    )
    v3_stage3_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to build multi-article knowledge graph from'
    )
    
    # Kritis 4.0 Commands - Enhanced Analysis with Preamble and Intelligent Tagging
    v4_stage1_parser = subparsers.add_parser(
        'enhanced-extract',
        help='Kritis 4.0 Stage 1: Enhanced extractor with preamble separation and article parsing'
    )
    v4_stage1_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to parse with preamble extraction'
    )
    
    v4_stage2_parser = subparsers.add_parser(
        'enhanced-analyze-context',
        help='Kritis 4.0 Stage 2: Enhanced analysis with preamble context and enriched entity extraction'
    )
    v4_stage2_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to analyze with enhanced context'
    )
    
    v4_stage3_parser = subparsers.add_parser(
        'intelligent-graph',
        help='Kritis 4.0 Stage 3: Intelligent knowledge graph with enhanced tagging and preamble integration'
    )
    v4_stage3_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to build intelligent knowledge graph from'
    )
    
    # Kritis V3.1 Commands - PROD9 Refactored Pipeline
    v31_stage1_parser = subparsers.add_parser(
        'v31-extract',
        help='Kritis V3.1 Stage 1: PROD9 enhanced extractor with preamble separation'
    )
    v31_stage1_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to extract with PROD9 specifications'
    )
    
    v31_stage2_parser = subparsers.add_parser(
        'v31-analyze',
        help='Kritis V3.1 Stage 2: PROD9 enhanced analyst with structured tags'
    )
    v31_stage2_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to analyze with PROD9 specifications'
    )
    
    v31_stage3_parser = subparsers.add_parser(
        'v31-ingest',
        help='Kritis V3.1 Stage 3: PROD9 simplified schema law ingestion'
    )
    v31_stage3_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to ingest with PROD9 specifications'
    )
    
    # Kritis V3.1 Complete Pipeline Command
    v31_complete_parser = subparsers.add_parser(
        'v31-complete',
        help='Kritis V3.1 Complete Pipeline: Run all PROD9 stages (extract -> analyze -> ingest)'
    )
    v31_complete_parser.add_argument(
        '--source-id',
        required=True,
        help='UUID of the source document to process with complete PROD9 pipeline'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Production validation
    if not validate_environment():
        logger.error("❌ Environment validation failed")
        sys.exit(1)
    
    if not hasattr(args, 'source_id') or not args.source_id or not validate_uuid(args.source_id):
        logger.error(f"❌ Invalid source ID format. Expected UUID, got: {getattr(args, 'source_id', 'None')}")
        sys.exit(1)
    
    logger.info(f"🚀 Starting Kritis Analysis for Source ID: {args.source_id}")
    logger.info(f"📋 Command: {args.command}")

    try:
        if args.command == 'analyze-source':
            # Legacy analysis for backward compatibility
            logger.info("⚠️  Using legacy analysis mode. Consider using the new Kritis pipelines.")
            analyzer = DocumentAnalyzer()
            analyzer.analyze_source(args.source_id)
            
        elif args.command == 'analyze-chunks':
            # Kritis 1.0 Stage 1: Map Phase
            logger.info("🔄 Using Kritis 1.0 pipeline")
            kritis = KritisAnalyzer()
            success = kritis.run_map_phase(args.source_id)
            if success:
                logger.info("🎯 Kritis 1.0 Stage 1 completed successfully")
                logger.info("📋 Next step: python main.py synthesize-summary --source-id " + args.source_id)
            else:
                logger.error("❌ Kritis 1.0 Stage 1 failed")
                sys.exit(1)
                
        elif args.command == 'synthesize-summary':
            # Kritis 1.0 Stage 2: Reduce Phase
            kritis = KritisAnalyzer()
            summary = kritis.run_reduce_phase(args.source_id)
            logger.info("🎯 Kritis 1.0 Stage 2 completed successfully")
            logger.info(f"📄 Document Summary Generated:")
            logger.info(f"PT Title: {summary['pt']['informal_summary_title']}")
            logger.info(f"EN Title: {summary['en']['informal_summary_title']}")
            logger.info("📋 Next step: python main.py ingest-law --source-id " + args.source_id)
            
        elif args.command == 'ingest-law':
            # Kritis 1.0 Stage 3: Law Ingestion
            kritis = KritisAnalyzer()
            law_id = kritis.ingest_law_from_analysis(args.source_id)
            logger.info(f"🎯 Kritis 1.0 Stage 3 completed successfully")
            logger.info(f"📚 Law created with ID: {law_id}")
            logger.info("✅ Full Kritis 1.0 pipeline completed!")
            
        elif args.command == 'extract-metadata':
            # Kritis 2.0 Stage 1-2: Metadata Extraction
            logger.info("🚀 Using Kritis 2.0 Enhanced Pipeline")
            kritis_v2 = KritisAnalyzerV2()
            metadata = kritis_v2.run_extractor_phase(args.source_id)
            logger.info("🎯 Kritis 2.0 Stage 1-2 completed successfully")
            logger.info(f"📄 Extracted Metadata:")
            logger.info(f"Official Number: {metadata.get('official_number', 'N/A')}")
            logger.info(f"Title: {metadata.get('official_title_pt', 'N/A')}")
            logger.info(f"Type: {metadata.get('law_type_id', 'N/A')}")
            logger.info(f"Date: {metadata.get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py analyze-enhanced --source-id " + args.source_id)
            
        elif args.command == 'analyze-enhanced':
            # Kritis 2.0 Stage 3: Enhanced Analysis
            kritis_v2 = KritisAnalyzerV2()
            success = kritis_v2.run_analyst_phase(args.source_id)
            if success:
                logger.info("🎯 Kritis 2.0 Stage 3 completed successfully")
                logger.info("📋 Next step: python main.py build-knowledge-graph --source-id " + args.source_id)
            else:
                logger.error("❌ Kritis 2.0 Stage 3 failed")
                sys.exit(1)
            
        elif args.command == 'build-knowledge-graph':
            # Kritis 2.0 Stage 4: Knowledge Graph Building
            kritis_v2 = KritisAnalyzerV2()
            law_id = kritis_v2.run_knowledge_graph_builder(args.source_id)
            logger.info(f"🎯 Kritis 2.0 Stage 4 completed successfully")
            logger.info(f"📚 Law created with enhanced knowledge graph: {law_id}")
            logger.info("✅ Full Kritis 2.0 Enhanced Pipeline completed!")
            
        elif args.command == 'parse-articles':
            # Kritis 3.0 Stage 1: Enhanced Extractor - Smart Article Parser
            logger.info("🚀 Using Kritis 3.0 Multi-Article Processing Pipeline")
            kritis_v3 = KritisAnalyzerV3()
            result = kritis_v3.run_enhanced_extractor_phase(args.source_id)
            logger.info("🎯 Kritis 3.0 Stage 1 completed successfully")
            logger.info(f"📄 Parsing Results:")
            logger.info(f"Total Articles Found: {result['total_articles']}")
            if result['metadata']:
                logger.info(f"Official Number: {result['metadata'].get('official_number', 'N/A')}")
                logger.info(f"Title: {result['metadata'].get('official_title_pt', 'N/A')}")
                logger.info(f"Type: {result['metadata'].get('law_type_id', 'N/A')}")
                logger.info(f"Date: {result['metadata'].get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py batch-analyze --source-id " + args.source_id)
            
        elif args.command == 'batch-analyze':
            # Kritis 3.0 Stage 2: Batch Analyst - Multi-Article Processor
            kritis_v3 = KritisAnalyzerV3()
            result = kritis_v3.run_batch_analyst_phase(args.source_id)
            logger.info("🎯 Kritis 3.0 Stage 2 completed successfully")
            logger.info(f"📊 Analysis Results:")
            logger.info(f"Articles Analyzed: {result['total_articles_analyzed']}")
            logger.info(f"Batches Processed: {result['batches_processed']}")
            logger.info("📋 Next step: python main.py build-multi-article-graph --source-id " + args.source_id)
            
        elif args.command == 'build-multi-article-graph':
            # Kritis 3.0 Stage 3: Multi-Article Knowledge Graph Builder
            kritis_v3 = KritisAnalyzerV3()
            law_id = kritis_v3.run_multi_article_knowledge_graph_builder(args.source_id)
            logger.info(f"🎯 Kritis 3.0 Stage 3 completed successfully")
            logger.info(f"📚 Law created with multi-article knowledge graph: {law_id}")
            logger.info("✅ Full Kritis 3.0 Multi-Article Pipeline completed!")
            
        elif args.command == 'enhanced-extract':
            # Kritis 4.0 Stage 1: Enhanced Extractor with Preamble Handling
            logger.info("🚀 Using Kritis 4.0 Enhanced Analysis Pipeline with Preamble Handling")
            kritis_v4 = KritisAnalyzerV4()
            result = kritis_v4.run_enhanced_extractor_with_preamble(args.source_id)
            logger.info("🎯 Kritis 4.0 Stage 1 completed successfully")
            logger.info(f"📄 Enhanced Parsing Results:")
            logger.info(f"Total Articles Found: {result['total_articles']}")
            logger.info(f"Has Preamble: {'Yes' if result['has_preamble'] else 'No'}")
            if result['metadata']:
                logger.info(f"Official Number: {result['metadata'].get('official_number', 'N/A')}")
                logger.info(f"Title: {result['metadata'].get('official_title_pt', 'N/A')}")
                logger.info(f"Type: {result['metadata'].get('law_type_id', 'N/A')}")
                logger.info(f"Date: {result['metadata'].get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py enhanced-analyze-context --source-id " + args.source_id)
            
        elif args.command == 'enhanced-analyze-context':
            # Kritis 4.0 Stage 2: Enhanced Analyst with Preamble Context
            kritis_v4 = KritisAnalyzerV4()
            result = kritis_v4.run_enhanced_analyst_with_context(args.source_id)
            logger.info("🎯 Kritis 4.0 Stage 2 completed successfully")
            logger.info(f"📊 Enhanced Analysis Results:")
            logger.info(f"Items Analyzed: {result['total_items_analyzed']}")
            logger.info(f"Successful Analyses: {result.get('successful_analyses', 'Unknown')}")
            logger.info(f"Failed Analyses: {result.get('failed_analyses', 'Unknown')}")
            logger.info(f"Completion Rate: {result.get('completion_rate', 'Unknown')}%")
            logger.info(f"Has Preamble Analysis: {'Yes' if result['has_preamble_analysis'] else 'No'}")
            logger.info(f"Batches Processed: {result['batches_processed']}")
            
            # Report any analysis issues
            if result.get('failed_analyses', 0) > 0:
                logger.warning(f"⚠️ {result['failed_analyses']} articles had analysis errors")
                logger.warning("These articles will have fallback analysis data")
            
            logger.info("📋 Next step: python main.py intelligent-graph --source-id " + args.source_id)
            
        elif args.command == 'intelligent-graph':
            # Kritis 4.0 Stage 3: Intelligent Knowledge Graph Builder
            kritis_v4 = KritisAnalyzerV4()
            law_id = kritis_v4.run_intelligent_knowledge_graph_builder(args.source_id)
            logger.info(f"🎯 Kritis 4.0 Stage 3 completed successfully")
            logger.info(f"📚 Law created with intelligent knowledge graph and enhanced tagging: {law_id}")
            logger.info("✅ Full Kritis 4.0 Enhanced Pipeline completed!")
            
        elif args.command == 'v31-extract':
            # Kritis V3.1 Stage 1: PROD9 Enhanced Extractor
            logger.info("🚀 Using Kritis V3.1 PROD9 Refactored Pipeline")
            kritis_v31 = KritisAnalyzerV31()
            result = kritis_v31.run_enhanced_extractor_phase(args.source_id)
            logger.info("🎯 Kritis V3.1 Stage 1 completed successfully")
            logger.info(f"📄 PROD9 Extraction Results:")
            logger.info(f"Total Articles Found: {result['total_articles']}")
            logger.info(f"Has Preamble: {'Yes' if result['has_preamble'] else 'No'}")
            if result['metadata']:
                logger.info(f"Official Number: {result['metadata'].get('official_number', 'N/A')}")
                logger.info(f"Title: {result['metadata'].get('official_title', 'N/A')}")
                logger.info(f"Type: {result['metadata'].get('law_type_id', 'N/A')}")
                logger.info(f"Date: {result['metadata'].get('enactment_date', 'N/A')}")
            logger.info("📋 Next step: python main.py v31-analyze --source-id " + args.source_id)
            
        elif args.command == 'v31-analyze':
            # Kritis V3.1 Stage 2: PROD9 Enhanced Analyst
            kritis_v31 = KritisAnalyzerV31()
            result = kritis_v31.run_enhanced_analyst_phase(args.source_id)
            logger.info("🎯 Kritis V3.1 Stage 2 completed successfully")
            logger.info(f"📊 PROD9 Analysis Results:")
            logger.info(f"Items Analyzed: {result['total_items_analyzed']}")
            logger.info(f"Successful Analyses: {result['successful_analyses']}")
            logger.info(f"Completion Rate: {result['completion_rate']:.1f}%")
            
            if result['successful_analyses'] < result['total_items_analyzed']:
                failed = result['total_items_analyzed'] - result['successful_analyses']
                logger.warning(f"⚠️ {failed} items had analysis errors and will use fallback data")
            
            logger.info("📋 Next step: python main.py v31-ingest --source-id " + args.source_id)
            
        elif args.command == 'v31-ingest':
            # Kritis V3.1 Stage 3: PROD9 Law Ingestion
            kritis_v31 = KritisAnalyzerV31()
            law_id = kritis_v31.run_enhanced_law_ingestion(args.source_id)
            logger.info(f"🎯 Kritis V3.1 Stage 3 completed successfully")
            logger.info(f"📚 Law created with PROD9 simplified schema: {law_id}")
            logger.info("✅ Full Kritis V3.1 PROD9 Pipeline completed!")
            
        elif args.command == 'v31-complete':
            # Kritis V3.1 Complete Pipeline: All stages in sequence
            logger.info("🚀 Starting Kritis V3.1 Complete PROD9 Pipeline")
            kritis_v31 = KritisAnalyzerV31()
            
            # Stage 1: Extract
            logger.info("📋 Stage 1/3: Enhanced Extraction...")
            extract_result = kritis_v31.run_enhanced_extractor_phase(args.source_id)
            logger.info(f"✅ Stage 1 complete: {extract_result['total_articles']} articles, preamble: {extract_result['has_preamble']}")
            
            # Stage 2: Analyze
            logger.info("📋 Stage 2/3: Enhanced Analysis...")
            analyze_result = kritis_v31.run_enhanced_analyst_phase(args.source_id)
            logger.info(f"✅ Stage 2 complete: {analyze_result['successful_analyses']}/{analyze_result['total_items_analyzed']} items analyzed ({analyze_result['completion_rate']:.1f}%)")
            
            # Stage 3: Ingest
            logger.info("📋 Stage 3/3: Law Ingestion...")
            law_id = kritis_v31.run_enhanced_law_ingestion(args.source_id)
            logger.info(f"✅ Stage 3 complete: Law created {law_id}")
            
            logger.info("🎉 Complete Kritis V3.1 PROD9 Pipeline finished successfully!")
            logger.info(f"📚 Final Law ID: {law_id}")
            logger.info("🔗 The law follows the PROD9 simplified schema:")
            logger.info("   - Direct laws -> law_article_versions relationship")
            logger.info("   - Preamble stored as article_order = 0")
            logger.info("   - JSONB tags on both laws and versions tables")
            logger.info("   - Enhanced structured analysis with cross-references")
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Analysis interrupted by user")
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
        sys.exit(1)
    
    logger.info("🎉 Analysis completed successfully!")

if __name__ == "__main__":
    main()