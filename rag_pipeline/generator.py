import os
from pathlib import Path
from typing import List, Dict, Optional
from rag_pipeline.config import Config
import time
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self):
        self._groq_client = None
        self._local_llm = None

        # Try Groq API first (fast, high quality)
        if Config.GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=Config.GROQ_API_KEY)
                # Quick validation
                self._groq_client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                )
                logger.info(f"Using Groq API with model: {Config.GROQ_MODEL}")
                return
            except Exception as e:
                logger.warning(f"Groq API init failed: {e}. Falling back to local model.")
                self._groq_client = None

        # Fallback: local Mistral via llama.cpp
        model_path = Config.LLM_MODEL
        if Path(model_path).exists():
            try:
                from llama_cpp import Llama
                n_gpu = int(os.getenv("N_GPU_LAYERS", "0"))
                self._local_llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=4,
                    n_gpu_layers=n_gpu,
                )
                logger.info(f"Using local LLM from {model_path} (gpu_layers={n_gpu})")
            except Exception as e:
                logger.error(f"Failed to load local LLM: {e}")
        else:
            logger.warning(
                f"No LLM available. Set GROQ_API_KEY in .env or download the model:\n"
                f"  python rag_pipeline/models/model-download.py"
            )

    def generate_response(
        self, query: str, context: List[Dict], history: List[str] = None
    ) -> str:
        """Generate response using Groq API or local LLM."""
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

        system_prompt = (
            "You are a helpful assistant for MOSDAC (Meteorological and Oceanographic "
            "Satellite Data Archival Centre), ISRO's satellite data portal. "
            "Answer the user's question using the provided context. "
            "Be specific and cite satellite names, instruments, and data products when relevant. "
            "If you don't know something, say so honestly."
        )

        user_prompt = (
            f"{history_str}"
            f"Question: {query}\n\n"
            f"Context:\n{context_str}"
        )

        start_time = time.time()

        if self._groq_client:
            response = self._generate_groq(system_prompt, user_prompt)
        elif self._local_llm:
            response = self._generate_local(system_prompt, user_prompt)
        else:
            return "LLM not configured. Set GROQ_API_KEY in .env or download the local model."

        logger.info(f"Generation time: {time.time() - start_time:.2f}s")
        return response

    def _generate_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Generate via Groq API."""
        try:
            response = self._groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            if self._local_llm:
                logger.info("Falling back to local LLM")
                return self._generate_local(system_prompt, user_prompt)
            return f"Error generating response: {e}"

    def _generate_local(self, system_prompt: str, user_prompt: str) -> str:
        """Generate via local Mistral model."""
        prompt = (
            f"<s>[INST] {system_prompt}\n\n{user_prompt}\n\n"
            f"Answer in clear, concise language.[/INST]"
        )
        response = self._local_llm(
            prompt,
            max_tokens=512,
            temperature=0.2,
            echo=False,
        )
        return response["choices"][0]["text"].strip()

    def _format_doc(self, doc: Dict) -> str:
        """Format document for context inclusion in prompt."""
        doc_type = doc.get("type", "")

        if doc_type == "satellite":
            products = doc.get("products", [])
            if products:
                return f"Satellite {doc.get('satellite', '?')} provides: {', '.join(products[:5])}"
            return f"Satellite: {doc.get('satellite', '?')}"

        elif doc_type == "data_product":
            regions = ", ".join(doc.get("regions", []))
            base = f"Data product '{doc.get('product', '?')}' from {doc.get('satellite', '?')}"
            if regions:
                base += f" covering {regions}"
            return base

        elif doc_type == "curated":
            return doc.get("text", "")[:500]

        elif doc_type == "crawled_page":
            return f"[{doc.get('source_url', 'MOSDAC')}] {doc.get('text', '')[:300]}"

        # Fallback
        name = doc.get("product") or doc.get("satellite") or doc.get("name", "")
        text = doc.get("text", str(doc))[:300]
        if name:
            return f"{name}: {text}"
        return text
