import json
from pathlib import Path
from typing import Dict, Any
from schemas import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        pass

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the raw data structure to match our Document model"""
        normalized = raw_data.copy()
        
        # Handle cases where text might be in different fields
        if 'raw_text' not in normalized and 'text' in normalized:
            normalized['raw_text'] = normalized['text']
        
        # Ensure metadata exists and has proper types
        if 'metadata' not in normalized:
            normalized['metadata'] = {}
        
        # Convert numeric metadata values to strings
        if 'pages' in normalized.get('metadata', {}):
            normalized['metadata']['pages'] = str(normalized['metadata']['pages'])
        
        return normalized

    def process_file(self, input_path: Path, output_path: Path):
        """Process a single file"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Normalize the data structure
            normalized_data = self.normalize_data(raw_data)
            
            # Create and validate the document
            document = Document(**normalized_data)
            
            # Save the processed data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(document.dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Processed: {input_path} -> {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing {input_path}: {str(e)}")

def process_all_files(input_dir: Path, output_dir: Path):
    """Process all JSON files in input directory"""
    processor = DataProcessor()
    
    # Process all JSON files in input directory and subdirectories
    for json_file in input_dir.rglob('*.json'):
        relative_path = json_file.relative_to(input_dir)
        output_path = output_dir / relative_path
        processor.process_file(json_file, output_path)

if __name__ == "__main__":
    # Configure these paths according to your directory structure
    INPUT_BASE = Path("R:\Projects\MOSDAC Help Bot\Codes\data_collection\data\mosdac\processed")
    OUTPUT_BASE = Path("./processed_output")
    
    print(f"Input directory: {INPUT_BASE.absolute()}")
    print(f"Output directory: {OUTPUT_BASE.absolute()}")
    
    if not INPUT_BASE.exists():
        print(f"Error: Input directory not found at {INPUT_BASE.absolute()}")
    else:
        process_all_files(INPUT_BASE, OUTPUT_BASE)
        print("Processing completed!")