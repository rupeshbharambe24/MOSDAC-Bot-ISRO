import re
import unicodedata
from datetime import datetime
from typing import Dict


class TextNormalizer:
    def __init__(self):
        self.acronym_map = {
            "TPW": "Total Precipitable Water",
            "MJO": "Madden-Julian Oscillation",
            "SST": "Sea Surface Temperature",
            "OLR": "Outgoing Longwave Radiation",
            "SWH": "Significant Wave Height",
            "INSAT": "Indian National Satellite System",
            "SCATSAT": "Scatterometer Satellite",
            "MOSDAC": "Meteorological and Oceanographic Satellite Data Archival Centre",
            "IMD": "India Meteorological Department",
            "ISRO": "Indian Space Research Organisation",
            "VHRR": "Very High Resolution Radiometer",
        }

        self.date_patterns = [
            # "15th Jan 2024", "1st February 2024" — strip ordinal suffix before parsing
            (
                r"\b(\d{1,2})(?:th|st|nd|rd)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b",
                lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)}",
                "%d %b %Y",
            ),
            # "15-01-2024" or "15/01/2024"
            (
                r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
                lambda m: m.group(0).replace("/", "-"),
                "%d-%m-%Y",
            ),
        ]

    def normalize_encoding(self, text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    def remove_artifacts(self, text: str) -> str:
        # Remove non-printable chars (keep newlines and tabs)
        text = "".join(char for char in text if char.isprintable() or char in "\n\t")
        # Fix common OCR ligatures
        text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
        return text

    def standardize_dates(self, text: str) -> str:
        for pattern, normalizer, fmt in self.date_patterns:
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
            for match in reversed(matches):  # reverse to preserve offsets
                original = match.group(0)
                try:
                    cleaned = normalizer(match)
                    dt = datetime.strptime(cleaned, fmt)
                    standardized = dt.strftime("%Y-%m-%d")
                    text = text[: match.start()] + standardized + text[match.end() :]
                except ValueError:
                    continue
        return text

    def expand_acronyms(self, text: str) -> str:
        for acronym, expansion in self.acronym_map.items():
            # Only expand if not already expanded: match "SST" but not "SST (Sea Surface Temperature)"
            pattern = rf"\b{re.escape(acronym)}\b(?!\s*\()"
            text = re.sub(pattern, f"{acronym} ({expansion})", text)
        return text

    def normalize_whitespace(self, text: str) -> str:
        # Collapse multiple spaces (but preserve single newlines for paragraph structure)
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def process(self, text: str) -> str:
        text = self.normalize_encoding(text)
        text = self.remove_artifacts(text)
        text = self.standardize_dates(text)
        text = self.expand_acronyms(text)
        text = self.normalize_whitespace(text)
        return text
