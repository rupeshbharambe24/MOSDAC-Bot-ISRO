from pathlib import Path
from typing import List, Dict
from llama_cpp import Llama
from rag_pipeline.config import Config
import time

class ResponseGenerator:
    def __init__(self):
        # Get the absolute path to the model file
        model_path = Path(__file__).parent.parent / "rag_pipeline" / "models" / Config.LLM_MODEL
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        self.llm = Llama(
            model_path=Config.LLM_MODEL,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=35  # Adjust based on your GPU VRAM
        )
        print(f"Local LLM loaded successfully from {model_path}")

    def generate_response(self, query: str, context: List[Dict]) -> str:
        """Generate natural language response from retrieved context"""
        if not context:
            return "I couldn't find relevant information in the knowledge base."
        
        context_str = "\n".join(
            f"- {self._format_doc(doc)}" for doc in context[:Config.TOP_K]
        )

        prompt = f"""<s>[INST] You are a helpful assistant for MOSDAC satellite data. 
        Answer the user's question using only the provided context.

        Question: {query}
        Context:
        {context_str}

        Answer in clear, concise language. If you don't know, say so.[/INST]"""

        start_time = time.time()
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.2,
            echo=False
        )
        print(f"Generation time: {time.time()-start_time:.2f}s")
        
        return response['choices'][0]['text'].strip()

    def _format_doc(self, doc: Dict) -> str:
        """Format document for context"""
        if doc.get("type") == "satellite":
            return (f"Satellite {doc['satellite']} with instrument {doc['instrument']} "
                   f"measuring {', '.join(doc.get('parameters', []))}")
        elif doc.get("type") == "data_product":
            return f"Data product {doc['product']} from {doc['satellite']}"
        return str(doc)