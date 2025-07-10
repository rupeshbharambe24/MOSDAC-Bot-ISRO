import os
import sys
import time
import torch
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import (
    ServiceUnavailable,
    AuthError,
    Neo4jError
)

class Neo4jConnectionManager:
    """Handles all Neo4j connection operations with retry logic"""
    def __init__(self, uri, auth, max_retries=3, retry_delay=2):
        self.uri = uri
        self.auth = auth
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.driver = None

    def connect(self):
        """Establish connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=basic_auth(*self.auth),
                    encrypted=False,
                    connection_timeout=15
                )
                # Verify connection
                with self.driver.session() as session:
                    session.run("RETURN 1").single()
                print("✅ Neo4j connection established successfully")
                return True
            except AuthError as e:
                raise ConnectionError(f"Authentication failed: {str(e)}")
            except ServiceUnavailable as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Connection attempt {attempt + 1} failed. Retrying...")
                    time.sleep(self.retry_delay)
                    continue
                raise ConnectionError(f"Could not connect to Neo4j after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise ConnectionError(f"Unexpected connection error: {str(e)}")
        return False

    def close(self):
        """Close the connection"""
        if self.driver:
            self.driver.close()
            self.driver = None

class GraphCleaner:
    def __init__(self):
        # Configuration
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_auth = ("neo4j", "mosdacisro")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize components
        self.connection = Neo4jConnectionManager(self.neo4j_uri, self.neo4j_auth)
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.relation_model = self._load_model()

    def _load_model(self):
        """Load the pre-trained relationship classifier"""
        model_path = "models/mosdac_relation_classifier"
        if not os.path.exists(model_path):
            print("❌ Model not found. Please train the model first.")
            sys.exit(1)
        
        print("Loading pre-trained model...")
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        return model.to(self.device)

    def clean_provides_relations(self):
        """Clean invalid PROVIDES relationships with comprehensive error handling"""
        if not self.connection.connect():
            return False

        try:
            with self.connection.driver.session() as session:
                # Get total count for progress bar
                total_result = session.run(
                    "MATCH (s:SATELLITE)-[r:PROVIDES]->() RETURN count(r) AS count"
                )
                total = total_result.single()["count"] if total_result else 0

                if total == 0:
                    print("⚠️ No PROVIDES relationships found in the database")
                    return False

                print(f"🔍 Found {total} PROVIDES relationships to validate")
                
                # Process in smaller batches for stability
                batch_size = 50
                processed = 0
                deleted = 0
                errors = 0
                max_errors = 5  # Maximum allowed consecutive errors

                with tqdm(total=total, desc="Validating relationships") as pbar:
                    while processed < total and errors < max_errors:
                        try:
                            # Get batch with explicit properties
                            result = session.run(
                                """
                                MATCH (s:SATELLITE)-[r:PROVIDES]->(d)
                                WHERE s.name IS NOT NULL AND d.name IS NOT NULL
                                RETURN s.name AS sat, d.name AS prod, elementId(r) AS rel_id
                                SKIP $skip LIMIT $limit
                                """,
                                skip=processed, limit=batch_size
                            )
                            
                            batch = [dict(record) for record in result]
                            if not batch:
                                break
                            
                            # Prepare texts for classification
                            texts = []
                            valid_records = []
                            for rec in batch:
                                try:
                                    if rec.get('sat') and rec.get('prod'):
                                        texts.append(f"{rec['sat']} provides {rec['prod']}")
                                        valid_records.append(rec)
                                except Exception as e:
                                    print(f"\n⚠️ Error preparing record: {str(e)}")
                                    continue
                            
                            if not texts:
                                processed += len(batch)
                                pbar.update(len(batch))
                                continue
                            
                            # Classify relationships
                            try:
                                inputs = self.tokenizer(
                                    texts,
                                    padding=True,
                                    truncation=True,
                                    return_tensors="pt",
                                    max_length=128
                                ).to(self.device)
                                
                                with torch.no_grad():
                                    outputs = self.relation_model(**inputs)
                                
                                # Process classification results
                                for i, rec in enumerate(valid_records):
                                    try:
                                        if outputs.logits[i].argmax() == 0:  # Invalid
                                            session.run(
                                                "MATCH ()-[r]->() WHERE elementId(r) = $rel_id DELETE r",
                                                rel_id=rec["rel_id"]
                                            )
                                            deleted += 1
                                    except Exception as e:
                                        print(f"\n⚠️ Error deleting relationship: {str(e)}")
                                        continue
                                
                                processed += len(batch)
                                pbar.update(len(batch))
                                errors = 0  # Reset error counter after successful batch
                                
                            except Exception as e:
                                print(f"\n⚠️ Error classifying batch: {str(e)}")
                                errors += 1
                                continue
                            
                        except Exception as e:
                            print(f"\n⚠️ Error processing batch: {str(e)}")
                            errors += 1
                            continue

                if errors >= max_errors:
                    print("\n❌ Stopped due to too many consecutive errors")
                    return False

                print(f"\n✅ Completed! Removed {deleted} invalid relationships")
                return True

        except Neo4jError as e:
            print(f"❌ Neo4j error during cleaning: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            self.connection.close()

if __name__ == "__main__":
    try:
        cleaner = GraphCleaner()
        if cleaner.clean_provides_relations():
            print("✨ Relationship cleaning completed successfully")
            sys.exit(0)
        else:
            print("❌ Relationship cleaning failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)