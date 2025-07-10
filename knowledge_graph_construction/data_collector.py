import os
import random
from neo4j import GraphDatabase
from tqdm import tqdm
from datetime import datetime

class TrainingDataGenerator:
    def __init__(self):
        # Configure your Neo4j connection here
        self.uri = "bolt://localhost:7687"
        self.user = "neo4j"  # Default username
        self.password = "mosdacisro"  # Change to your actual password
        self.driver = None
        self._connect()
        
    def _connect(self):
        """Establish Neo4j connection with error handling"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30
            )
            # Verify connection works
            with self.driver.session() as session:
                session.run("RETURN 1").single()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {str(e)}")

    def get_valid_examples(self, n=50):
        """Extract valid PROVIDES relationships from graph"""
        if not self.driver:
            self._connect()
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                    WHERE d.name IS NOT NULL AND size(d.name) > 3
                    RETURN s.name AS sat, d.name AS product
                    LIMIT $n
                    """, n=n)
                return [
                    {"text": f"{record['sat']} provides {record['product']}", "label": 1} 
                    for record in result
                ]
        except Exception as e:
            print(f"Error fetching valid examples: {str(e)}")
            return []

    def get_invalid_examples(self, n=50):
        """Generate invalid examples using negative sampling"""
        if not self.driver:
            self._connect()
            
        invalid_examples = []
        try:
            with self.driver.session() as session:
                # Get random satellites
                sats = session.run("""
                    MATCH (s:SATELLITE) 
                    RETURN s.name 
                    LIMIT 100
                    """).values()
                
                # Known invalid patterns
                invalid_terms = [
                    "40 Hz", "lanczos", "Genetic Algorithm", 
                    "raw data", "test", "v1.0", "beta"
                ]
                
                for _ in range(n):
                    sat = random.choice(sats)[0]
                    term = random.choice(invalid_terms)
                    invalid_examples.append({
                        "text": f"{sat} provides {term}",
                        "label": 0
                    })
        except Exception as e:
            print(f"Error generating invalid examples: {str(e)}")
            
        return invalid_examples

    def save_to_file(self, examples, filename="training_data.py"):
        """Save training data with backup"""
        try:
            # Create backup if file exists
            if os.path.exists(filename):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"training_data_backup_{timestamp}.py"
                os.rename(filename, backup_name)
            
            with open(filename, "w") as f:
                f.write("# Auto-generated training data\n")
                f.write("TRAINING_EXAMPLES = [\n")
                for ex in examples:
                    f.write(f"    {ex},\n")
                f.write("]\n")
            print(f"Saved {len(examples)} examples to {filename}")
        except Exception as e:
            print(f"Error saving training data: {str(e)}")

if __name__ == "__main__":
    print("MOSDAC Training Data Generator")
    print("------------------------------")
    
    try:
        generator = TrainingDataGenerator()
        
        print("\n1. Collecting valid examples...")
        valid = generator.get_valid_examples(100)
        print(f"Found {len(valid)} valid examples")
        
        print("\n2. Generating invalid examples...")
        invalid = generator.get_invalid_examples(100)
        print(f"Generated {len(invalid)} invalid examples")
        
        if not valid and not invalid:
            raise RuntimeError("No training data collected!")
        
        print("\n3. Saving data...")
        generator.save_to_file(valid + invalid)
        
        print("\nOperation completed successfully!")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("Please check your Neo4j connection settings and try again.")