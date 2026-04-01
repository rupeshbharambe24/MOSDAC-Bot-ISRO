"""
Data Processors Subpackage

Contains all data processing components:
- Text normalization
- Language handling
- Metadata enrichment
- OCR cleaning
"""

from .text_normalizer import TextNormalizer
from .language_handler import LanguageHandler
from .metadata_enricher import MetadataEnricher
from .ocr_cleaner import HindiOCRCleaner

__all__ = [
    'TextNormalizer',
    'LanguageHandler',
    'MetadataEnricher',
    'HindiOCRCleaner'
]

# Processor-specific constants
SUPPORTED_LANGUAGES = ['en', 'hi']
DOCUMENT_TYPES = ['faq', 'report', 'technical', 'other']
