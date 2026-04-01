import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_AUTH = (
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", ""),
    )

    # Model Configuration
    EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
    BASE_DIR = Path(__file__).parent.parent
    LLM_MODEL = str(BASE_DIR / "rag_pipeline" / "models" / "mistral-7b-instruct-v0.1.Q4_K_M.gguf")  # Quantized model

    # Vector Store
    VECTOR_STORE_PATH = str(BASE_DIR / "vector_store" / "faiss.index")
    EMBEDDING_DIM = 768

    # Retrieval Parameters
    TOP_K = 5
    # Cosine similarity threshold (0 to 1). With normalized vectors + IndexFlatIP,
    # 1.0 = identical, 0 = orthogonal. 0.3 is a reasonable starting threshold.
    SIMILARITY_THRESHOLD = 0.3
