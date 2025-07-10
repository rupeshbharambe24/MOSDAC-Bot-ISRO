from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline.generator import ResponseGenerator
from rag_pipeline.retriever import HybridRetriever
from rag_pipeline.config import Config
import uvicorn
import atexit
from neo4j import GraphDatabase

app = FastAPI(
    title="Antariksh Query Nexus API",
    description="Backend for MOSDAC satellite data query system",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

driver = GraphDatabase.driver(Config.NEO4J_URI, auth=Config.NEO4J_AUTH)

# Initialize components
retriever = HybridRetriever()
generator = ResponseGenerator()

def close_neo4j_driver():
    driver.close()

atexit.register(close_neo4j_driver)

class QueryRequest(BaseModel):
    message: str

@app.post("/query")
async def process_query(query: QueryRequest):
    try:
        message = query.message
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Retrieve relevant documents
        context = retriever.retrieve(message)
        
        # Generate response
        response = generator.generate_response(message, context)
        
        # Format sources for frontend
        sources = []
        if context:
            for doc in context[:3]:
                sources.append({
                    "satellite": doc.get("satellite", "Unknown"),
                    "dataset": doc.get("product", doc.get("type", "Dataset")),
                    "timeRange": "Available",
                    "url": "https://mosdac.gov.in"
                })
        
        return {
            "response": response,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)