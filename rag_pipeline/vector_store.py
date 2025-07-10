import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rag_pipeline.config import Config
from typing import List, Dict

class VectorStore:
    def __init__(self):
        os.makedirs(os.path.dirname(Config.VECTOR_STORE_PATH), exist_ok=True)
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index = self._initialize_index()

    def _initialize_index(self) -> faiss.Index:
        """Initialize or load FAISS index"""
        if os.path.exists(Config.VECTOR_STORE_PATH):
            return faiss.read_index(Config.VECTOR_STORE_PATH)
        return faiss.IndexFlatL2(Config.EMBEDDING_DIM)

    def add_documents(self, documents: List[Dict[str, any]]):
        """Add documents to vector store"""
        texts = [doc["text"] for doc in documents]
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        self.index.add(np.array(embeddings).astype('float32'))
        faiss.write_index(self.index, Config.VECTOR_STORE_PATH)

    def search(self, query: str, k: int = Config.TOP_K) -> List[int]:
        """Search for similar documents"""
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(query_embedding, k)
        return [
            idx for idx, dist in zip(indices[0], distances[0])
            if dist < Config.SIMILARITY_THRESHOLD
        ]

    def save_index(self):
        """Save the index to disk"""
        faiss.write_index(self.index, Config.VECTOR_STORE_PATH)