import os
from pathlib import Path
from typing import List, Dict
from llama_cpp import Llama
from rag_pipeline.config import Config
import time
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self):
        model_path = Config.LLM_MODEL

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found at: {model_path}\n"
                "Download it with: python rag_pipeline/models/model-download.py"
            )

        n_gpu = int(os.getenv("N_GPU_LAYERS", "0"))
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=n_gpu,
        )
        logger.info(f"Local LLM loaded from {model_path} (gpu_layers={n_gpu})")

    def generate_response(
        self, query: str, context: List[Dict], history: List[str] = None
    ) -> str:
        """Generate natural language response from retrieved context and conversation history."""
        if not context:
            return "I couldn't find relevant information in the knowledge base."

        context_str = "\n".join(
            f"- {self._format_doc(doc)}" for doc in context[: Config.TOP_K]
        )

        history_str = ""
        if history:
            history_str = (
                "Previous conversation:\n"
                + "\n".join(history)
                + "\n\n"
            )

        prompt = (
            f"<s>[INST] You are a helpful assistant for MOSDAC satellite data. "
            f"Answer the user's question using the provided context. "
            f"Consider the conversation history for follow-up questions.\n\n"
            f"{history_str}"
            f"Question: {query}\n"
            f"Context:\n{context_str}\n\n"
            f"Answer in clear, concise language. If you don't know, say so.[/INST]"
        )

        start_time = time.time()
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.2,
            echo=False,
        )
        logger.info(f"Generation time: {time.time() - start_time:.2f}s")

        return response["choices"][0]["text"].strip()

    def _format_doc(self, doc: Dict) -> str:
        """Format document for context inclusion in prompt."""
        doc_type = doc.get("type", "")
        if doc_type == "satellite":
            params = ", ".join(doc.get("parameters", []))
            return (
                f"Satellite {doc.get('satellite', '?')} with instrument "
                f"{doc.get('instrument', '?')} measuring {params}"
            )
        elif doc_type == "data_product":
            regions = ", ".join(doc.get("regions", []))
            base = f"Data product {doc.get('product', '?')} from {doc.get('satellite', '?')}"
            if regions:
                base += f" covering {regions}"
            return base
        name = doc.get("product") or doc.get("satellite") or doc.get("name", "")
        if name:
            return f"{name}: {doc.get('text', str(doc))[:200]}"
        return str(doc)[:300]
