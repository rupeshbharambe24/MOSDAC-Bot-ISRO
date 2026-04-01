import json
from pathlib import Path
from typing import Dict, Any
from .schemas import Document
from .processors.text_normalizer import TextNormalizer
from .processors.language_handler import LanguageHandler
from .processors.metadata_enricher import MetadataEnricher
from .processors.ocr_cleaner import HindiOCRCleaner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        self.text_normalizer = TextNormalizer()
        self.language_handler = LanguageHandler()
        self.ocr_cleaner = HindiOCRCleaner()
        # MetadataEnricher needs spaCy — lazy-init on first use
        self._metadata_enricher = None

    @property
    def metadata_enricher(self) -> MetadataEnricher:
        if self._metadata_enricher is None:
            self._metadata_enricher = MetadataEnricher()
        return self._metadata_enricher

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the raw data structure to match our Document model."""
        normalized = raw_data.copy()

        # Handle cases where text might be in different fields
        if "raw_text" not in normalized and "text" in normalized:
            normalized["raw_text"] = normalized["text"]

        # Ensure metadata exists and has proper types
        if "metadata" not in normalized:
            normalized["metadata"] = {}

        # Convert numeric metadata values to strings
        if "pages" in normalized.get("metadata", {}):
            normalized["metadata"]["pages"] = str(normalized["metadata"]["pages"])

        return normalized

    def process_text(self, text: str) -> Dict[str, Any]:
        """Run all text processors and return enriched data."""
        # 1. Detect language
        processed_text, language = self.language_handler.process(text)

        # 2. Clean Hindi OCR artifacts if Hindi detected
        if language == "hi":
            processed_text = self.ocr_cleaner.clean_hindi_text(processed_text)

        # 3. Normalize text (encoding, artifacts, dates, acronyms, whitespace)
        processed_text = self.text_normalizer.process(processed_text)

        # 4. Enrich metadata (document type + keywords)
        metadata = self.metadata_enricher.process(processed_text, language)

        return {
            "text": processed_text,
            "language": language,
            "metadata": metadata,
        }

    def process_file(self, input_path: Path, output_path: Path):
        """Process a single file through the full pipeline."""
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # Normalize the data structure
            normalized_data = self.normalize_data(raw_data)

            # Run the processing pipeline on the text content
            text = normalized_data.get("raw_text", normalized_data.get("text", ""))
            if text:
                enriched = self.process_text(text)
                normalized_data["text"] = enriched["text"]
                normalized_data["raw_text"] = enriched["text"]
                normalized_data["language"] = enriched["language"]
                # Merge enriched metadata with existing
                existing_meta = normalized_data.get("metadata", {})
                existing_meta.update(enriched["metadata"])
                normalized_data["metadata"] = existing_meta

            # Validate against schema
            document = Document(**normalized_data)

            # Save the processed data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(document.dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Processed: {input_path.name} -> {output_path.name}")

        except Exception as e:
            logger.error(f"Error processing {input_path}: {e}")


def process_all_files(input_dir: Path, output_dir: Path):
    """Process all JSON files in input directory."""
    processor = DataProcessor()

    json_files = list(input_dir.rglob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to process.")

    for json_file in json_files:
        relative_path = json_file.relative_to(input_dir)
        output_path = output_dir / relative_path
        processor.process_file(json_file, output_path)

    logger.info("Processing completed.")


if __name__ == "__main__":
    INPUT_BASE = Path("../data_collection/data/mosdac/processed")
    OUTPUT_BASE = Path("./processed_output")

    print(f"Input directory: {INPUT_BASE.absolute()}")
    print(f"Output directory: {OUTPUT_BASE.absolute()}")

    if not INPUT_BASE.exists():
        print(f"Error: Input directory not found at {INPUT_BASE.absolute()}")
    else:
        process_all_files(INPUT_BASE, OUTPUT_BASE)
