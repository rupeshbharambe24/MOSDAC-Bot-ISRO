import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline.generator import ResponseGenerator
from rag_pipeline.retriever import HybridRetriever
from rag_pipeline.config import Config
from neo4j import GraphDatabase
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MOSDAC Help Bot API",
    description="Backend for MOSDAC satellite data query system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
retriever = HybridRetriever()
generator = ResponseGenerator()

# Neo4j driver for direct queries (satellites, stats)
_neo4j_driver = GraphDatabase.driver(
    Config.NEO4J_URI, auth=Config.NEO4J_AUTH, encrypted=False
)

# Index documents on startup
logger.info("Indexing documents from knowledge graph...")
retriever.index_documents()
logger.info("Indexing complete.")


class HistoryMessage(BaseModel):
    content: str
    isBot: bool


class QueryRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []


@app.post("/query")
async def process_query(query: QueryRequest):
    message = query.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Retrieve relevant documents
        context = retriever.retrieve(message)

        # Build conversation history for context-aware generation
        conv_history = []
        for h in query.history[-6:]:  # Last 3 turns (6 messages)
            role = "Assistant" if h.isBot else "User"
            conv_history.append(f"{role}: {h.content}")

        # Generate response
        response = generator.generate_response(message, context, conv_history)

        # Format sources from actual retrieved data
        sources = []
        for doc in context[:3]:
            doc_type = doc.get("type", "")
            if doc_type == "curated":
                satellite = doc.get("category", "MOSDAC").title()
                dataset = doc.get("text", "")[:80] + "..."
            elif doc_type == "crawled_page":
                satellite = "MOSDAC Portal"
                dataset = doc.get("source_url", "").replace("https://www.mosdac.gov.in/", "").replace("-", " ").title() or "Web Page"
            else:
                satellite = doc.get("satellite", "Unknown")
                dataset = doc.get("product", doc.get("name", "Dataset"))

            sources.append(
                {
                    "satellite": satellite,
                    "dataset": dataset,
                    "timeRange": "Available",
                    "url": doc.get("source_url", "https://mosdac.gov.in"),
                }
            )

        return {"response": response, "sources": sources}

    except Exception as e:
        logger.exception(f"Error processing query: {message}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your query. Please try again.",
        )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/satellites")
async def list_satellites():
    """List all satellites in the knowledge graph with their instruments and products."""
    try:
        with _neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:SATELLITE)
                OPTIONAL MATCH (s)-[:HAS_INSTRUMENT]->(i:INSTRUMENT)
                OPTIONAL MATCH (s)-[:PROVIDES]->(d:DATA_PRODUCT)
                WITH s,
                     COLLECT(DISTINCT i.name) AS instruments,
                     COLLECT(DISTINCT d.name) AS products
                RETURN {
                    name: s.name,
                    source: s.source,
                    instruments: instruments,
                    products: products
                } AS satellite
                ORDER BY s.name
            """)
            satellites = [record["satellite"] for record in result]
        return {"satellites": satellites, "count": len(satellites)}
    except Exception as e:
        logger.exception("Failed to list satellites")
        raise HTTPException(status_code=500, detail="Could not retrieve satellite data.")


@app.get("/stats")
async def graph_stats():
    """Return knowledge graph statistics."""
    try:
        with _neo4j_driver.session() as session:
            counts = {}
            for label in ["SATELLITE", "INSTRUMENT", "DATA_PRODUCT", "PARAMETER", "REGION"]:
                result = session.run(
                    f"MATCH (n:{label}) RETURN count(n) AS c"
                )
                counts[label.lower() + "_count"] = result.single()["c"]

            rel_count = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            ).single()["c"]
            counts["relationship_count"] = rel_count

        return {"stats": counts}
    except Exception as e:
        logger.exception("Failed to get stats")
        raise HTTPException(status_code=500, detail="Could not retrieve graph statistics.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
