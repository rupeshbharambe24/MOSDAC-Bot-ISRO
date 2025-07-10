import requests
from urllib.parse import urljoin, urlparse
import tldextract
from pathlib import Path
import time
import logging
from typing import Dict, Optional
from config import Config
from document_processing import DocumentProcessor
import json
from pathlib import Path
import re
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MosdacCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MOSDACBot/1.0)'
        })
        self.visited = set()
        self.document_processor = DocumentProcessor()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"
        return domain in Config.ALLOWED_DOMAINS

    def get_links(self, url: str) -> list:
        """Extract all links from a page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            return [urljoin(url, a['href']) for a in soup.find_all('a', href=True) 
                   if self.is_valid_url(urljoin(url, a['href']))]
        except Exception as e:
            logger.error(f"Error getting links from {url}: {str(e)}")
            return []

    def process_url(self, url: str, depth: int = 0):
        """Process a single URL"""
        if url in self.visited or depth > Config.MAX_DEPTH:
            return
        
        self.visited.add(url)
        logger.info(f"Processing {url} (depth {depth})")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            
            # Process based on content type
            result = None
            if content_type == 'text/html':
                result = self.document_processor.process_html(url, response.content)
                links = self.get_links(url)
                for link in links:
                    self.process_url(link, depth + 1)
            elif 'pdf' in content_type.lower():
                result = self.document_processor.process_pdf(url, response.content)
            elif 'wordprocessingml' in content_type.lower():
                result = self.document_processor.process_docx(url, response.content)
            else:
                logger.info(f"Skipping {url} with content type {content_type}")
                return
            
            # Save the extracted data
            if result:
                self._save_extracted_data(url, content_type, result)
            
            time.sleep(Config.REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")

    def _save_extracted_data(self, url: str, content_type: str, data: dict):
        """Save extracted data to filesystem with proper filename sanitization"""
        try:
            # Create a safe filename from the URL
            filename = url.replace('https://', '').replace('http://', '')
            
            # Remove problematic characters
            filename = re.sub(r'[<>:"/\\|?*&#=]', '_', filename)
            
            # Limit filename length and ensure it's not empty
            if len(filename) > 100:
                filename_hash = hashlib.md5(filename.encode()).hexdigest()
                filename = filename[:50] + '_' + filename_hash[:8]
            if not filename:
                filename = 'unknown_' + hashlib.md5(url.encode()).hexdigest()[:8]
            
            # Add .json extension
            filename += '.json'
            
            # Determine output directory based on content type
            if 'pdf' in content_type.lower():
                output_dir = Config.PROCESSED_DIR / 'pdfs'
            elif 'wordprocessingml' in content_type.lower():
                output_dir = Config.PROCESSED_DIR / 'docs'
            elif 'html' in content_type.lower():
                output_dir = Config.PROCESSED_DIR / 'html'
            elif 'rss' in content_type.lower():
                logger.info(f"Skipping RSS feed at {url}")
                return None
            else:
                output_dir = Config.PROCESSED_DIR / 'other'
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved extracted data to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving data from {url}: {str(e)}")

    def run(self):
        """Start crawling from the base URL"""
        self.process_url(Config.START_URL)