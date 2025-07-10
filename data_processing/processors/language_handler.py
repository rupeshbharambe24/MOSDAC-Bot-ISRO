from langdetect import detect, LangDetectException
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from typing import Tuple

class LanguageHandler:
    def detect_language(self, text: str) -> str:
        try:
            # Sample first 500 chars for faster detection
            sample = text[:500].replace('\n', ' ')
            return detect(sample)
        except LangDetectException:
            return "en"  # Default to English

    def transliterate_hindi(self, text: str) -> str:
        if any('\u0900' <= c <= '\u097F' for c in text):
            return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return text

    def process(self, text: str) -> Tuple[str, str]:
        lang = self.detect_language(text)
        if lang == "hi":
            text = self.transliterate_hindi(text)
        return text, lang