import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rag_pipeline.config import Config
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        os.makedirs(os.path.dirname(Config.VECTOR_STORE_PATH) or ".", exist_ok=True)
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index = self._initialize_index()
        self._doc_count = self.index.ntotal

    def _initialize_index(self) -> faiss.Index:
        """Initialize or load FAISS index using Inner Product (cosine similarity with normalized vectors)."""
        if os.path.exists(Config.VECTOR_STORE_PATH):
            return faiss.read_index(Config.VECTOR_STORE_PATH)
        return faiss.IndexFlatIP(Config.EMBEDDING_DIM)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to vector store. Re-indexes if document count changed."""
        if self.index.ntotal > 0 and self.index.ntotal == len(documents):
            logger.info(f"Vector index up to date ({self.index.ntotal} vectors).")
            return
        if self.index.ntotal > 0:
            logger.info(
                f"Document count changed ({self.index.ntotal} → {len(documents)}), re-indexing..."
            )
            self.index = faiss.IndexFlatIP(Config.EMBEDDING_DIM)

        texts = [doc.get("text", "") for doc in documents]
        if not texts:
            return

        embeddings = self.encoder.encode(texts, show_progress_bar=True, normalize_embeddings=True)
        self.index.add(np.array(embeddings).astype("float32"))
        self._doc_count = self.index.ntotal
        faiss.write_index(self.index, Config.VECTOR_STORE_PATH)
        logger.info(f"Indexed {len(texts)} documents into vector store.")

    def search(self, query: str, k: int = None) -> List[int]:
        """Search for similar documents using cosine similarity.

        Returns indices of documents with similarity >= SIMILARITY_THRESHOLD.
        With normalized vectors and IndexFlatIP, scores range from -1 to 1
        where 1 = identical, 0 = orthogonal.
        """
        if k is None:
            k = Config.TOP_K

        if self.index.ntotal == 0:
            return []

        query_embedding = self.encoder.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        return [
            int(idx)
            for idx, score in zip(indices[0], scores[0])
            if idx >= 0 and score >= Config.SIMILARITY_THRESHOLD
        ]

    def clear(self):
        """Reset the index and delete the persisted file."""
        self.index = faiss.IndexFlatIP(Config.EMBEDDING_DIM)
        self._doc_count = 0
        if os.path.exists(Config.VECTOR_STORE_PATH):
            os.remove(Config.VECTOR_STORE_PATH)

    def save_index(self):
        """Save the index to disk."""
        faiss.write_index(self.index, Config.VECTOR_STORE_PATH)
