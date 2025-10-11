"""
Local Translation Module for Kritis V6.0
Uses deep-translator for PT->EN translation with graceful fallback.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Check deep-translator availability
deep_translator_available = False
try:
    from deep_translator import GoogleTranslator
    deep_translator_available = True
    logger.info("✅ deep-translator loaded successfully")
except ImportError:
    logger.warning("⚠️ deep-translator not available - using passthrough mode")


def translate_text(text: str, source_lang: str = 'pt', target_lang: str = 'en') -> str:
    """
    Translate text from Portuguese to English using deep-translator.
    If translation library unavailable, returns original text (passthrough mode).
    
    Args:
        text: Text to translate (in Portuguese)
        source_lang: Source language code (default: 'pt')
        target_lang: Target language code (default: 'en')
    
    Returns:
        Translated text in English (or original if translation unavailable)
    """
    if not text or not text.strip():
        return ""
    
    # Try deep-translator
    if deep_translator_available:
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            logger.debug(f"✅ Translated: {text[:50]}... -> {translated[:50]}...")
            return translated
        except Exception as e:
            logger.warning(f"⚠️ Translation failed: {e}, using passthrough")
            return text
    
    # Passthrough mode: return original text
    logger.debug(f"⚠️ Passthrough mode (no translator): {text[:50]}...")
    return text


def translate_analysis_object(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate Portuguese analysis to create bilingual object.
    
    Args:
        analysis: Portuguese-only analysis object
    
    Returns:
        Bilingual analysis object with pt and en keys
    """
    pt_title = analysis.get('informal_summary_title', '')
    pt_summary = analysis.get('informal_summary', '')
    
    # Translate to English
    en_title = translate_text(pt_title)
    en_summary = translate_text(pt_summary)
    
    return {
        'pt': {
            'informal_summary_title': pt_title,
            'informal_summary': pt_summary
        },
        'en': {
            'informal_summary_title': en_title,
            'informal_summary': en_summary
        }
    }


def translate_tags(tags: Dict[str, list]) -> Dict[str, Any]:
    """
    Translate conceptual tags while preserving proper nouns.
    
    Args:
        tags: Portuguese tags object
    
    Returns:
        Bilingual tags object with pt and en keys
    """
    pt_tags = {
        "person": tags.get("person", []),
        "organization": tags.get("organization", []),
        "concept": tags.get("concept", [])
    }
    
    # English tags: copy person and organization, translate concepts
    en_tags = {
        "person": pt_tags["person"][:],  # Copy as-is (proper nouns)
        "organization": pt_tags["organization"][:],  # Copy as-is (proper nouns)
        "concept": []
    }
    
    # Translate each concept tag
    for concept in pt_tags["concept"]:
        translated_concept = translate_text(concept)
        en_tags["concept"].append(translated_concept)
    
    return {
        "pt": pt_tags,
        "en": en_tags
    }
