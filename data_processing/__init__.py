"""
MOSDAC Data Processing Package

Provides tools for cleaning, normalizing, and enriching text data extracted from MOSDAC portal.
Includes support for both English and Hindi content processing.
"""

from .processors.text_normalizer import TextNormalizer
from .processors.language_handler import LanguageHandler
from .processors.metadata_enricher import MetadataEnricher
from .processors.ocr_cleaner import HindiOCRCleaner
from .schemas import Document
from .main import DataProcessor

__version__ = "0.1.0"
__all__ = [
    'TextNormalizer',
    'LanguageHandler',
    'MetadataEnricher',
    'HindiOCRCleaner',
    'Document',
    'DataProcessor'
]

# Package-level initialization
def init_package():
    """Initialize package resources"""
    import spacy
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        raise ImportError("English language model for spaCy not found. Run: python -m spacy download en_core_web_sm")

# init_package()  # Disabled: let callers initialize explicitly
