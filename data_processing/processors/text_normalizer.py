import re
import unicodedata
from datetime import datetime
from typing import Dict

class TextNormalizer:
    def __init__(self):
        self.acronym_map = {
            "TPW": "Total Precipitable Water",
            "MJO": "Madden-Julian Oscillation",
            "SST": "Sea Surface Temperature"
        }
        
        self.date_patterns = [
            (r"\b(\d{1,2})(th|st|nd|rd)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b", "%d %b %Y"),
            (r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", "%d-%m-%Y")
        ]

    def normalize_encoding(self, text: str) -> str:
        return unicodedata.normalize('NFKC', text)

    def remove_artifacts(self, text: str) -> str:
        # Remove non-printable chars
        text = ''.join(char for char in text if char.isprintable())
        # Fix common OCR errors
        text = re.sub(r'ﬁ', 'fi', text)
        text = re.sub(r'ﬂ', 'fl', text)
        return text

    def standardize_dates(self, text: str) -> str:
        for pattern, fmt in self.date_patterns:
            matches = re.finditer(pattern, text, flags=re.IGNORECASE)
            for match in matches:
                original = match.group(0)
                try:
                    dt = datetime.strptime(original, fmt)
                    standardized = dt.strftime("%Y-%m-%d")
                    text = text.replace(original, standardized)
                except ValueError:
                    continue
        return text

    def expand_acronyms(self, text: str) -> str:
        for acronym, expansion in self.acronym_map.items():
            text = re.sub(rf"\b{acronym}\b", f"{acronym} ({expansion})", text)
        return text

    def normalize_whitespace(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def process(self, text: str) -> str:
        text = self.normalize_encoding(text)
        text = self.remove_artifacts(text)
        text = self.standardize_dates(text)
        text = self.expand_acronyms(text)
        text = self.normalize_whitespace(text)
        return text