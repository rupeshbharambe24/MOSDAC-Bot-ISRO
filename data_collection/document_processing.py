import os
import io
import logging
import tempfile
from typing import Dict, Any
from pathlib import Path
from PIL import Image
import pdfminer.high_level
import docx
import openpyxl
import PyPDF2
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from config import Config
from PIL import ImageEnhance, ImageFilter
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Set Tesseract path if needed (uncomment if required)
        # pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
        
        # For Windows, you might need to set poppler_path
        self.poppler_path = getattr(Config, 'POPPLER_PATH', None)

    def process_pdf(self, url: str, content: bytes) -> Dict[str, Any]:
        """Enhanced PDF processor with Hindi and scientific PDF handling"""
        result = {
            'source_url': url,
            'content_type': 'application/pdf',
            'text': '',
            'metadata': {},
            'tables': [],
            'figures': [],
            'visual_data': []
        }
        
        temp_path = None
        try:
            # First try standard extraction to detect content type
            initial_text = self._try_standard_extraction(content)
            
            # Determine processing approach
            if self._is_hindi_content(initial_text):
                raw_hindi = self._extract_hindi_with_ocr(content)
                result['text'] = self._clean_hindi_text(raw_hindi)
            else:
                scientific_data = self._extract_scientific_data(content)
                result.update(scientific_data)
                
                # Analyze visuals for scientific PDFs
                if any(keyword in url.lower() for keyword in ['report', 'study', 'prediction']):
                    result['visual_data'] = self._analyze_figures(content)
            
            # Extract metadata
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(content)
                temp_path = tmp.name
            
            with open(temp_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                if pdf_reader.metadata:
                    result['metadata'] = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'pages': len(pdf_reader.pages)
                    }
        
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {str(e)}")
        
        return result
    
    def _try_standard_extraction(self, content: bytes) -> str:
        """Try standard PDF text extraction"""
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text_pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_pages.append(text)
                return '\n'.join(text_pages)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}")
            # Fallback to pdfminer
            try:
                return pdfminer.high_level.extract_text(io.BytesIO(content))
            except Exception as e:
                logger.warning(f"pdfminer extraction failed: {str(e)}")
                raise ValueError("Standard extraction failed")

    def _is_hindi_content(self, text: str) -> bool:
        """Detect if text contains significant Hindi content"""
        if not text.strip():
            return False
        
        # Count Devanagari Unicode characters
        devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        return devanagari_chars / max(len(text), 1) > 0.3  # At least 30% Hindi chars

    def _extract_hindi_with_ocr(self, content: bytes) -> str:
        """Enhanced Hindi OCR with better preprocessing"""
        try:
            # Convert PDF to high-res images (600 DPI)
            images = convert_from_bytes(
                content,
                dpi=600,
                poppler_path=self.poppler_path,
                grayscale=True,
                thread_count=4
            )
            
            hindi_text = []
            for img in images:
                # Enhanced preprocessing specifically for Hindi
                img = img.filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Contrast(img).enhance(2.0)
                img = ImageEnhance.Brightness(img).enhance(1.2)
                
                # Binarization with adaptive threshold
                img = img.point(lambda x: 0 if x < 180 else 255)
                
                # Custom config for Hindi documents
                custom_config = r'--psm 6 --oem 1 -c preserve_interword_spaces=1'
                text = pytesseract.image_to_string(
                    img,
                    lang='hin+eng',
                    config=custom_config
                )
                hindi_text.append(text)
            
            return '\n'.join(hindi_text)
        except Exception as e:
            logger.error(f"Hindi OCR failed: {str(e)}")
            return ""

    def _extract_scientific_data(self, content: bytes) -> dict:
        """Extract data from scientific PDFs with visualizations"""
        result = {
            'text': '',
            'figures': [],
            'tables': []
        }
        
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                # Text extraction
                text_pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_pages.append(text)
                    
                    # Extract figures metadata
                    if page.images:
                        result['figures'].append({
                            'page': page.page_number,
                            'width': page.images[0]['width'], 
                            'height': page.images[0]['height']
                        })
                
                result['text'] = '\n'.join(text_pages)
                
                # Enhanced table extraction
                for page in pdf.pages:
                    tables = page.extract_tables({
                        'vertical_strategy': 'text', 
                        'horizontal_strategy': 'text',
                        'intersection_y_tolerance': 10
                    })
                    if tables:
                        result['tables'].extend(tables)
        
        except Exception as e:
            logger.error(f"Scientific extraction failed: {str(e)}")
        
        return result

    def _clean_hindi_text(self, text: str) -> str:
        """Clean and normalize Hindi OCR output"""
        # Comprehensive replacement dictionary for common Hindi OCR errors
        replacements = {
            # Single character replacements
            'T{': 'भा',
            'ffi': 'ति',
            'qr': 'क',
            'qrf': 'क्र',
            'z': '्य',
            't': 'र',
            'f': 'ी',
            'r': 'ा',
            'q': 'े',
            'E': 'स',
            'W': 'व',
            'G': 'द',
            'I': 'ल',
            'J': 'प',
            'c': 'न',
            '7': 'य',
            '?': 'म',
            '|': '।',
            '*': '्',
            '{': 'र्द',
            '}': 'न्द',
            '[': 'क्ष',
            ']': 'त्र',
            '\\': 'ज्ञ',
            '~': 'ड़',
            '`': 'ढ़',
            '^': 'ऋ',
            '_': 'ऊ',
            
            # Common multi-character patterns
            'ffidgur+c': 'तकनीकी',
            'rrnruft+r': 'प्राधिकरण',
            'urfu': 'शाखा',
            'aT. A. m.': 'भारत सरकार',
            'gffinwfrqvran': 'इलेक्ट्रॉनिक्स',
            'ffifuftqelaq': 'सूचना प्रौद्योगिकी',
            'gffiAw': 'मंत्रालय',
            'Biaa': 'विभाग',
            'sil.6ffitr': 'संचार एवं',
            'drfiG': 'सूचना',
            't$fr': 'प्रौद्योगिकी',
            'aTflTcgur+g': 'भारतीय मानक',
            '1eqIuFtir': 'ब्यूरो',
            'T6rfifirr': 'प्रमाणन',
            'fuqranrtfr': 'प्रकोष्ठ',
            'f{f,rq': 'संस्थान',
            'fttErfu': 'प्रमाणन',
            'sqr6': 'शाखा',
            'WrM': 'विभाग',
            'iti-q': 'स्तर',
            'sr6TffqrE': 'प्रयोगशाला',
            'frffie': 'पता',
            'qttal': 'ईमेल',
            'aTsrfc': 'भारतीय',
            'zJurrc7r': 'मानक ब्यूरो',
            'rfrIuffi{ul': 'प्रमाणन प्रकोष्ठ',
            'rJu6c?r': 'विभाग स्तर',
            'Fi11': 'दिनांक',
            'ilffr': 'हस्ताक्षर',
            '3paqq': 'निदेशक',
            'FiTnif': 'डॉ. ए.के.',
            'ffic': 'श्री',
            'sTrtr': 'वरिष्ठ',
            'sFrr': 'वैज्ञानिक',
            'Gnn': 'डॉ.',
            'frtqfi': 'मुख्य',
            '$raarfrdrcif': 'प्रौद्योगिकी प्रबंधक',
            'qqrfrfr': 'संचार एवं',
            '3Tqt': 'निदेशक',
            'zTEI\'iIcdI': 'मानकीकरण',
            'iEfilf': 'प्रयोगशाला',
            'rrrufr+-{ur': 'प्रमाणीकरण',
            'Afur': 'प्रक्रिया',
            'r"+vrra': 'प्राधिकरण',
            'anfta': 'स्तर',
            'rfiTulqt': 'प्रमाण पत्र',
            'rrgeifr': 'प्रभारी',
            'ffiia': 'तकनीकी',
            'ilfi': 'हस्ताक्षर',
            '*-{A': 'मुख्य',
            'ftfu': 'वैज्ञानिक',
            '$frr': 'प्रौद्योगिकी',
            'gert': 'विभाग',
            'arffi': 'मानक',
            '3rffi': 'निदेशक',
            'sd\'ffi+,\'!q': 'प्रमाणन प्रकोष्ठ',
            'geu': 'शाखा',
            'rirEr.s\'': 'डॉ. ए.के.',
            'tOfrr{Ir{dtstril': 'प्रमाणीकरण प्रक्रिया',
            'dtr': 'संचार',
            'gtsn': 'मंत्रालय',
            'grBz': 'विभाग',
            'rgrurr{': 'प्रौद्योगिकी',
            '*\'3nfi4': 'स्तर प्रमाणन',
            '=qmtmr': 'ईमेल'
        }
        
        # First pass - replace known multi-character patterns
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        # Second pass - handle common OCR artifacts
        text = text.replace('\n', ' ')  # Replace newlines with spaces
        text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
        text = re.sub(r'([ा-ृ])\s+([्])', r'\1\2', text)  # Fix split matras
        text = re.sub(r'([क-ह])\s+([ा-ौ])', r'\1\2', text)  # Fix split vowels
        
        # Fix common OCR errors in conjuncts
        conjunct_fixes = {
            'क र': 'क्र',
            'त र': 'त्र',
            'द र': 'द्र',
            'न र': 'न्र',
            'प र': 'प्र',
            'म र': 'म्र'
        }
        for wrong, correct in conjunct_fixes.items():
            text = text.replace(wrong, correct)
        
        # Handle English portions (dates, URLs etc.)
        text = re.sub(r'(\d+)(th|st|nd|rd)', r'\1\2', text)  # Fix dates
        text = text.replace('mosdac.qov.in', 'mosdac.gov.in')  # Fix URL
        
        return text.strip()

    def _extract_tables(self, page) -> list:
        """Improved table extraction with structure preservation"""
        tables = []
        try:
            # First try text-based extraction for Hindi documents
            table = page.extract_table({
                'vertical_strategy': 'text',
                'horizontal_strategy': 'text',
                'intersection_y_tolerance': 20,
                'intersection_x_tolerance': 20
            })
            
            if table and len(table) > 1:  # Valid table found
                tables.append(table)
            else:
                # Fallback to stream extraction
                table = page.extract_table({
                    'vertical_strategy': 'lines',
                    'horizontal_strategy': 'lines'
                })
                if table:
                    tables.append(table)
                    
        except Exception as e:
            logger.warning(f"Table extraction failed: {str(e)}")
        
        return tables

    def _analyze_figures(self, content: bytes) -> list:
        """Enhanced visualization analysis"""
        try:
            import cv2
            import numpy as np
            
            figures = []
            images = convert_from_bytes(content, dpi=200)
            
            for i, img in enumerate(images):
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Detect different elements
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Classify visualization type
                viz_type = 'graph'
                if len(contours) > 10 and cv2.mean(edges)[0] > 50:
                    viz_type = 'heatmap'
                elif len(contours) > 5 and cv2.mean(edges)[0] < 30:
                    viz_type = 'plot'
                    
                figures.append({
                    'page': i+1,
                    'type': viz_type,
                    'contours': len(contours),
                    'edge_density': float(cv2.mean(edges)[0])
                })
                
            return figures
        except Exception as e:
            logger.error(f"Visual analysis failed: {str(e)}")
            return []
        
    def process_docx(self, url: str, content: bytes) -> Dict[str, Any]:
        """Process DOCX without pandas"""
        result = {
            'source_url': url,
            'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text': '',
            'metadata': {}
        }
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            doc = docx.Document(tmp_path)
            result['text'] = '\n'.join([para.text for para in doc.paragraphs])
            
            prop = doc.core_properties
            result['metadata'] = {
                'title': prop.title,
                'author': prop.author,
                'subject': prop.subject
            }
            
            os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Error processing DOCX {url}: {str(e)}")
        
        return result

    def process_html(self, url: str, content: bytes) -> Dict[str, Any]:
        """Process HTML without pandas"""
        from bs4 import BeautifulSoup
        
        result = {
            'source_url': url,
            'content_type': 'text/html',
            'text': '',
            'metadata': {}
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            result['text'] = soup.get_text(separator='\n', strip=True)
            
            meta = {}
            for tag in soup.find_all('meta'):
                name = tag.get('name', tag.get('property', ''))
                if name:
                    meta[name.lower()] = tag.get('content', '')
            
            result['metadata'] = meta
            
        except Exception as e:
            logger.error(f"Error processing HTML {url}: {str(e)}")
        
        return result