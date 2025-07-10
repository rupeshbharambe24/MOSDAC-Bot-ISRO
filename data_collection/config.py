import os
from pathlib import Path

class Config:
    POPPLER_PATH = r'C:\Program Files\poppler-24.08.0\Library\bin'
    HINDI_OCR_DPI = 600
    HINDI_OCR_PREPROCESS = True
    
    # Crawler settings
    START_URL = "https://www.mosdac.gov.in/"
    ALLOWED_DOMAINS = ["mosdac.gov.in"]
    MAX_DEPTH = 3
    REQUEST_DELAY = 1.0  # seconds
    
    # Storage settings
    OUTPUT_DIR = Path("data/mosdac")
    RAW_DIR = OUTPUT_DIR / "raw"
    PROCESSED_DIR = OUTPUT_DIR / "processed"
    DATABASE_URL = "sqlite:///mosdac_data.db"
    
    # Document processing
    PDF_TIMEOUT = 30  # seconds
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def setup_dirs(cls):
        os.makedirs(cls.RAW_DIR, exist_ok=True)
        os.makedirs(cls.PROCESSED_DIR / 'pdfs', exist_ok=True)
        os.makedirs(cls.PROCESSED_DIR / 'docs', exist_ok=True)
        os.makedirs(cls.PROCESSED_DIR / 'html', exist_ok=True)
        os.makedirs(cls.PROCESSED_DIR / 'other', exist_ok=True)

Config.setup_dirs()