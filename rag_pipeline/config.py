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

    # LLM Configuration
    # Priority: Groq API (fast, high quality) → Local Mistral (offline fallback)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Local model fallback
    EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
    BASE_DIR = Path(__file__).parent.parent
    LLM_MODEL = str(BASE_DIR / "rag_pipeline" / "models" / "mistral-7b-instruct-v0.1.Q4_K_M.gguf")

    # Crawled data path (for document indexing)
    CRAWLED_DATA_DIR = str(BASE_DIR / "data_collection" / "data" / "mosdac" / "processed")

    # Vector Store
    VECTOR_STORE_PATH = str(BASE_DIR / "vector_store" / "faiss.index")
    EMBEDDING_DIM = 768

    # Retrieval Parameters
    TOP_K = 5
    SIMILARITY_THRESHOLD = 0.3
