from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import torch
from pathlib import Path
import json
import logging
from typing import List, Dict, Tuple
import spacy
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MOSDACRelationshipExtractor:
    # Updated relation patterns with explicit patterns
    RELATION_PATTERNS = {
        "PROVIDES": [
            ("SATELLITE", "DATA_PRODUCT"),
            ("SATELLITE", "SERVICE")
        ],
        "MEASURES": [
            ("INSTRUMENT", "PARAMETER"),
            ("SENSOR", "VARIABLE")
        ],
        "HAS": [
            ("MISSION", "DOCUMENT"),
            ("PROJECT", "REPORT")
        ],
        "COVERS": [
            ("SATELLITE", "REGION"),
            ("INSTRUMENT", "REGION"),
            ("DATA_PRODUCT", "REGION")
        ],
        "LOCATED_IN": [
            ("STATION", "REGION"),
            ("OBSERVATORY", "REGION")
        ]
    }

    # Enhanced entity patterns with data products
    MOSDAC_ENTITIES = {
        "SATELLITE": ["INSAT", "SCATSAT", "Oceansat", "SARAL", "Kalpana"],
        "INSTRUMENT": ["VHRR", "SAPHIR", "SCAT", "DWR", "AVHRR"],
        "PARAMETER": ["TPW", "SST", "OLR", "WS", "SWH", "MJO"],
        "DATA_PRODUCT": ["Sea Surface Temperature", "Wind Speed", "Rainfall", 
                        "Ocean Wind Vectors", "Total Precipitable Water"],
        "REGION": ["Arabian Sea", "Bay of Bengal", "Indian Ocean", r"\d+°[NSEW]"],
        "STATION": ["IMD", "NRSC", "ISRO"]
    }

    # Explicit patterns for PROVIDES relationships
    PROVIDES_PATTERNS = [
        (r"\b(INSAT-\d+D?)\b.*\b(provides|offers|delivers)\b.*\b(SST|Sea Surface Temperature)\b", "PROVIDES"),
        (r"\b(SCATSAT-\d*)\b.*\b(provides|measures)\b.*\b(Ocean Wind Vectors?|Wind Speed)\b", "PROVIDES"),
        (r"\b(Oceansat-\d*)\b.*\b(provides|generates)\b.*\b(Ocean Color Data|Chlorophyll)\b", "PROVIDES")
    ]

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load models
        self._load_models()
        self._initialize_patterns()
        
        logger.info(f"Using device: {self.device}")
        logger.info("MOSDAC Relationship Extractor initialized")

    def _load_models(self):
        """Load required NLP models"""
        try:
            # Base relation extraction model
            self.rel_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            self.rel_model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased").to(self.device)
            
            # Spacy for sentence segmentation
            self.nlp = spacy.load("en_core_web_sm", disable=["ner"])
            self.nlp.add_pipe("sentencizer")
            
            logger.info("Loaded language models")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise

    def _initialize_patterns(self):
        """Initialize MOSDAC-specific patterns"""
        self.entity_patterns = defaultdict(list)
        for entity_type, examples in self.MOSDAC_ENTITIES.items():
            for pattern in examples:
                self.entity_patterns[entity_type].append(re.compile(pattern, re.IGNORECASE))
        
        # Compile PROVIDES patterns
        self.provides_regexes = []
        for pattern, rel_type in self.PROVIDES_PATTERNS:
            self.provides_regexes.append((re.compile(pattern, re.IGNORECASE), rel_type))

    def _match_mosdac_entity(self, text: str) -> str:
        """Identify MOSDAC-specific entities using patterns"""
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return entity_type
        return "OTHER"

    def _extract_sentences_with_entities(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Extract sentences containing entity pairs"""
        doc = self.nlp(text)
        sentences = []
        
        for sent in doc.sents:
            sent_entities = []
            for ent in entities:
                if ent["start"] >= sent.start_char and ent["end"] <= sent.end_char:
                    # Enhance entity type with MOSDAC patterns
                    mosdac_type = self._match_mosdac_entity(ent["text"])
                    ent["mosdac_type"] = mosdac_type if mosdac_type != "OTHER" else ent["label"]
                    sent_entities.append(ent)
            
            if len(sent_entities) >= 2:
                sentences.append({
                    "text": sent.text,
                    "entities": sent_entities,
                    "start": sent.start_char,
                    "end": sent.end_char
                })
        
        return sentences

    def _find_explicit_provides(self, text: str) -> List[Dict]:
        """Find explicit PROVIDES relationships using patterns"""
        relations = []
        for pattern, rel_type in self.provides_regexes:
            for match in pattern.finditer(text):
                satellite = match.group(1)
                product = match.group(3)
                relations.append({
                    "head": satellite,
                    "head_type": "SATELLITE",
                    "type": rel_type,
                    "tail": product,
                    "tail_type": "DATA_PRODUCT",
                    "evidence": text,
                    "source": "explicit_pattern"
                })
        return relations

    def _predict_relation(self, text: str, entity1: Dict, entity2: Dict) -> str:
        """Predict relationship between two entities"""
        # First check for explicit patterns
        if ("SATELLITE" in [entity1.get("mosdac_type"), entity2.get("mosdac_type")] and
            "DATA_PRODUCT" in [entity1.get("mosdac_type"), entity2.get("mosdac_type")]):
            provides_rels = self._find_explicit_provides(text)
            if provides_rels:
                return "PROVIDES"
        
        # Then use BERT for other cases
        input_text = f"{text} [E1]{entity1['text']}[/E1] [E2]{entity2['text']}[/E2]"
        inputs = self.rel_tokenizer(input_text, return_tensors="pt", truncation=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.rel_model(**inputs)
        
        predicted_class = torch.argmax(outputs.logits).item()
        return list(self.RELATION_PATTERNS.keys())[predicted_class % len(self.RELATION_PATTERNS)]

    def _predict_relation_batch(self, inputs: List[Tuple[str, Dict, Dict]], batch_size: int = 100) -> List[str]:
        """Batch predict relations for better GPU utilization"""
        results = []
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            input_texts = [
                f"{text} [E1]{e1['text']}[/E1] [E2]{e2['text']}[/E2]"
                for text, e1, e2 in batch
            ]
            
            encoded = self.rel_tokenizer(
                input_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.rel_model(**encoded)
            
            predicted_classes = torch.argmax(outputs.logits, dim=1).tolist()
            relation_labels = list(self.RELATION_PATTERNS.keys())
            results.extend([relation_labels[i % len(relation_labels)] for i in predicted_classes])
        
        return results

    def _validate_relation(self, rel_type: str, entity1: Dict, entity2: Dict) -> bool:
        """Validate if relation makes sense for the entity types"""
        valid_pairs = self.RELATION_PATTERNS.get(rel_type, [])
        e1_type = entity1.get("mosdac_type", entity1["label"])
        e2_type = entity2.get("mosdac_type", entity2["label"])
        
        return (e1_type, e2_type) in valid_pairs

    def extract_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Enhanced relationship extraction with explicit patterns"""
        relations = []
        
        # First find explicit PROVIDES relationships
        relations.extend(self._find_explicit_provides(text))
        
        # Then process all sentences
        sentences = self._extract_sentences_with_entities(text, entities)
        
        for sent in sentences:
            sent_entities = sent["entities"]
            entity_pairs = []
            
            # Prepare all possible entity pairs
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i+1:]:
                    entity_pairs.append((sent["text"], ent1, ent2))
            
            # Batch predict relations
            if entity_pairs:
                predicted_rels = self._predict_relation_batch(entity_pairs)
                
                for (text, ent1, ent2), rel_type in zip(entity_pairs, predicted_rels):
                    if self._validate_relation(rel_type, ent1, ent2):
                        relations.append({
                            "head": ent1["text"],
                            "head_type": ent1.get("mosdac_type", ent1["label"]),
                            "type": rel_type,
                            "tail": ent2["text"],
                            "tail_type": ent2.get("mosdac_type", ent2["label"]),
                            "evidence": text,
                            "source": "model"
                        })
                    
                    # Check reverse relation
                    rev_rel_type = self._predict_relation(text, ent2, ent1)
                    if self._validate_relation(rev_rel_type, ent2, ent1):
                        relations.append({
                            "head": ent2["text"],
                            "head_type": ent2.get("mosdac_type", ent2["label"]),
                            "type": rev_rel_type,
                            "tail": ent1["text"],
                            "tail_type": ent1.get("mosdac_type", ent1["label"]),
                            "evidence": text,
                            "source": "model"
                        })
        
        # Add co-occurrence based relations as fallback
        relations.extend(self._add_cooccurrence_relations(text, entities))
        
        return relations

    def _add_cooccurrence_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Add simple co-occurrence based relations with pattern matching"""
        cooc_relations = []
        
        for i, ent1 in enumerate(entities):
            for ent2 in entities[i+1:]:
                for rel_type, valid_pairs in self.RELATION_PATTERNS.items():
                    e1_type = ent1.get("mosdac_type", ent1["label"])
                    e2_type = ent2.get("mosdac_type", ent2["label"])
                    
                    if (e1_type, e2_type) in valid_pairs:
                        cooc_relations.append({
                            "head": ent1["text"],
                            "head_type": e1_type,
                            "type": rel_type,
                            "tail": ent2["text"],
                            "tail_type": e2_type,
                            "evidence": text[max(0, ent1["start"]-50):ent2["end"]+50],
                            "source": "pattern"
                        })
                    # Check reverse
                    elif (e2_type, e1_type) in valid_pairs:
                        cooc_relations.append({
                            "head": ent2["text"],
                            "head_type": e2_type,
                            "type": rel_type,
                            "tail": ent1["text"],
                            "tail_type": e1_type,
                            "evidence": text[max(0, ent1["start"]-50):ent2["end"]+50],
                            "source": "pattern"
                        })
        
        return cooc_relations

    def batch_process(self, input_dir: Path, output_dir: Path):
        """Process all entity files in directory"""
        output_dir.mkdir(parents=True, exist_ok=True)
        processed_files = 0
        
        for json_file in input_dir.rglob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    entity_data = json.load(f)
                
                # Get original text
                source_path = Path(entity_data["source"])
                if not source_path.exists():
                    logger.warning(f"Source file not found: {source_path}")
                    continue
                    
                with open(source_path, "r", encoding="utf-8") as f:
                    original_data = json.load(f)
                    text = original_data.get("text", "")
                
                # Extract relations
                all_entities = entity_data["text_entities"] + entity_data["metadata_entities"]
                relations = self.extract_relations(text, all_entities)
                
                # Save results
                output_path = output_dir / json_file.relative_to(input_dir)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    "source": str(source_path),
                    "entities": all_entities,
                    "relations": relations,
                    "stats": {
                        "entity_count": len(all_entities),
                        "relation_count": len(relations)
                    }
                }
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                processed_files += 1
                if processed_files % 100 == 0:
                    logger.info(f"Processed {processed_files} files...")
                    
            except Exception as e:
                logger.error(f"Error processing {json_file}: {str(e)}")
                continue
        
        logger.info(f"Completed processing. Total files: {processed_files}")

if __name__ == "__main__":
    # Initialize extractor
    extractor = MOSDACRelationshipExtractor()
    
    # Configure paths
    input_dir = Path("entities")  # From entity extraction step
    output_dir = Path("relations")
    
    # Run processing
    extractor.batch_process(input_dir, output_dir)