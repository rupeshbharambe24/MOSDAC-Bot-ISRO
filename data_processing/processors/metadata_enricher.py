import spacy
from typing import List, Dict
import re

class MetadataEnricher:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.doc_type_patterns = {
            "faq": [r"question", r"answer", r"faq", r"frequently asked"],
            "report": [r"report", r"study", r"analysis"],
            "technical": [r"specification", r"technical", r"user manual"]
        }

    def detect_document_type(self, text: str) -> str:
        text_lower = text.lower()
        for doc_type, patterns in self.doc_type_patterns.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                return doc_type
        return "other"

    def extract_keywords(self, text: str, lang: str = "en") -> List[str]:
        if lang != "en":
            return []
            
        doc = self.nlp(text)
        keywords = []
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ in ["NOUN", "PROPN"]:
                keywords.append(chunk.text)
        return list(set(keywords))[:10]  # Return top 10 unique keywords

    def process(self, text: str, lang: str) -> Dict:
        return {
            "document_type": self.detect_document_type(text),
            "keywords": self.extract_keywords(text, lang)
        }