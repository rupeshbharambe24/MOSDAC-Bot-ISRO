import re

class HindiOCRCleaner:
    def __init__(self):
        self.hindi_replacements = {
            'qr': 'क',
            'qrf': 'क्र',
            'T{': 'भा',
            'ffi': 'ति',
            'z': '्य',
            't': 'र',
            'f': 'ी',
            'r': 'ा'
        }

    def clean_hindi_text(self, text: str) -> str:
        for wrong, correct in self.hindi_replacements.items():
            text = text.replace(wrong, correct)
        
        # Fix conjuncts
        text = re.sub(r'([क-ह])\s+([ा-ौ])', r'\1\2', text)
        return text