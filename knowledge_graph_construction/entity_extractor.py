import spacy
from spacy.tokens import DocBin
from pathlib import Path
import json
from typing import List, Dict
import logging
import re
from tqdm import tqdm  # Added for progress bar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        # Load English and Hindi models
        try:
            self.nlp_en = spacy.load("en_core_web_lg")
            # self.nlp_hi = spacy.blank("hi")  # Hindi base model
            logger.info("Loaded language models")
        except OSError:
            logger.error("Language models not found. Run:\n"
                       "python -m spacy download en_core_web_lg")
            raise

        # Domain-specific entity patterns with enhanced data products
        self.patterns = {
            "SATELLITE": ["INSAT-3D", "INSAT-3DR", "SCATSAT-1", "Oceansat-2", "SARAL", "Kalpana-1", "Megha-Tropiques"],
            "PARAMETER": ["TPW", "MJO", "SST", "SWH", "WS", "OLR", "Rainfall"],
            "INSTRUMENT": ["SCAT", "VHRR", "SAPHIR", "AVHRR", "DWR", "IMAGER"],
            "DATA_PRODUCT": [
                "Sea Surface Temperature", "SST", "Wind Speed", "WS",
                "Rainfall", "Total Precipitable Water", "TPW",
                "Ocean Wind Vectors", "Outgoing Longwave Radiation", "OLR",
                "Ocean Color Data", "Chlorophyll", "Sea Surface Height"
            ],
            "REGION": [
                "Arabian Sea", "Bay of Bengal", "Indian Ocean", 
                "Kerala", "Gujarat", "Himalayas",
                r"\d+°[NSEW]", r"\d+-\d+°[NSEW]",
                r"\d+\.\d+° [NS], \d+\.\d+° [EW]"
            ],
            "STATION": ["IMD", "NRSC", "ISRO", "Meteorological Department"]
        }

        # Terms that indicate data products
        self.product_indicators = [
            "data", "product", "dataset", "measurement",
            "observation", "parameter", "variable"
        ]

        # Geographical terms
        self.geo_terms = [
            "sea", "ocean", "bay", "gulf", "region", "area", 
            "coast", "peninsula", "territory", "zone"
        ]

        # Initialize the entity ruler
        self.add_custom_entities()

    def add_custom_entities(self):
        """Add domain-specific entity ruler with enhanced patterns"""
        if "entity_ruler" not in self.nlp_en.pipe_names:
            ruler = self.nlp_en.add_pipe("entity_ruler")
        else:
            ruler = self.nlp_en.get_pipe("entity_ruler")
        
        patterns = []
        
        for label, terms in self.patterns.items():
            # For DATA_PRODUCT, create both exact and partial match patterns
            if label == "DATA_PRODUCT":
                for term in terms:
                    # Exact match
                    patterns.append({"label": label, "pattern": term})
                    # Acronym match
                    if " " in term:
                        acronym = "".join(word[0] for word in term.split())
                        patterns.append({"label": label, "pattern": acronym})
            else:
                patterns.extend([{"label": label, "pattern": term} for term in terms])
        
        ruler.add_patterns(patterns)
        logger.info(f"Added {len(patterns)} custom entity patterns")

    def _is_data_product(self, text: str, context: str = "") -> bool:
        """Determine if an entity should be labeled as DATA_PRODUCT"""
        # Check if it matches exact data product names
        text_lower = text.lower()
        if any(product.lower() in text_lower for product in self.patterns["DATA_PRODUCT"]):
            return True
            
        # Check for acronyms of known products
        if " " not in text and len(text) <= 5:
            return any(
                acronym.lower() == text_lower
                for product in self.patterns["DATA_PRODUCT"]
                if " " in product
                for acronym in ["".join(word[0] for word in product.split())]
            )
            
        # Check for product indicators in surrounding context
        if any(indicator in context.lower() for indicator in self.product_indicators):
            return True
            
        return False

    def extract_entities(self, text: str, language: str = "en") -> List[Dict]:
        """Enhanced entity extraction with better DATA_PRODUCT handling"""
        doc = self.nlp_en(text) if language == "en" else self.nlp_en(text)
        
        entities = []
        for ent in doc.ents:
            # Handle DATA_PRODUCT identification first
            if self._is_data_product(ent.text, text[max(0, ent.start_char-50):ent.end_char+50]):
                ent_type = "DATA_PRODUCT"
            # Handle geographical regions
            elif ent.label_ in ["GPE", "LOC"] or any(term in ent.text.lower() for term in self.geo_terms):
                ent_type = "REGION"
            # Convert ORG to SATELLITE when appropriate
            elif ent.label_ == "ORG" and any(sat in ent.text for sat in self.patterns["SATELLITE"]):
                ent_type = "SATELLITE"
            # Default to original label
            else:
                ent_type = ent.label_
            
            entities.append({
                "text": ent.text,
                "label": ent_type,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        return entities

    def batch_process(self, input_dir: Path, output_dir: Path):
        """Process all JSON files in directory with enhanced entity handling"""
        output_dir.mkdir(parents=True, exist_ok=True)  # Changed to parents=True
        
        processed_files = 0
        for json_file in tqdm(list(input_dir.rglob("*.json")), desc="Processing files"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extract entities from both text and metadata
                text_entities = self.extract_entities(data.get("text", ""), 
                                                    data.get("language", "en"))
                metadata_entities = []
                for key, value in data.get("metadata", {}).items():
                    if isinstance(value, str):
                        metadata_entities.extend(self.extract_entities(value, "en"))
                
                # Save results with proper path handling
                relative_path = json_file.relative_to(input_dir)
                output_path = output_dir / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    "source": str(json_file),
                    "text_entities": text_entities,
                    "metadata_entities": metadata_entities
                }
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                processed_files += 1
                if processed_files % 100 == 0:
                    logger.info(f"Processed {processed_files} files...")
                
            except Exception as e:
                logger.error(f"Error processing {json_file}: {str(e)}")
                continue
        
        logger.info(f"Finished processing. Total files processed: {processed_files}")

if __name__ == "__main__":
    extractor = EntityExtractor()
    _HERE = Path(__file__).parent
    input_dir = (_HERE / ".." / "data_processing" / "processed_output").resolve()
    output_dir = _HERE / "entities"
    
    # Verify input directory exists
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        exit(1)
    
    extractor.batch_process(input_dir, output_dir)