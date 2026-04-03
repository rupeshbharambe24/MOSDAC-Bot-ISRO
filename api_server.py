import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

# Count indexed documents by type
type_counts = {}
for d in retriever.documents:
    t = d.get("type", "unknown")
    type_counts[t] = type_counts.get(t, 0) + 1
logger.info(f"Index breakdown: {type_counts}")


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

        sources = _format_sources(context)

        return {"response": response, "sources": sources}

    except Exception as e:
        logger.exception(f"Error processing query: {message}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your query. Please try again.",
        )


def _format_sources(context):
    """Format context docs into source objects."""
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
        sources.append({
            "satellite": satellite,
            "dataset": dataset,
            "timeRange": "Available",
            "url": doc.get("source_url", "https://mosdac.gov.in"),
        })
    return sources


@app.post("/query/stream")
async def stream_query(query: QueryRequest):
    """SSE streaming endpoint for real-time response generation."""
    message = query.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        context = retriever.retrieve(message)
        conv_history = []
        for h in query.history[-6:]:
            role = "Assistant" if h.isBot else "User"
            conv_history.append(f"{role}: {h.content}")

        sources = _format_sources(context)

        def event_stream():
            # Send sources first
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            # Stream text tokens
            for token in generator.stream_response(message, context, conv_history):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            # Signal completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.exception(f"Error streaming query: {message}")
        raise HTTPException(status_code=500, detail="Streaming failed.")


@app.post("/feedback")
async def submit_feedback(feedback: dict):
    """Store user feedback on bot responses."""
    import datetime
    feedback_file = Path(__file__).parent / "feedback.jsonl"
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "message_id": feedback.get("messageId", ""),
        "query": feedback.get("query", ""),
        "response": feedback.get("response", "")[:500],
        "type": feedback.get("type", ""),  # "up" or "down"
    }
    try:
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"Feedback saved: {entry['type']} for message {entry['message_id']}")
    except Exception as e:
        logger.warning(f"Failed to save feedback: {e}")
    return {"status": "ok"}


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


@app.get("/admin/eval")
async def admin_eval_results():
    """Return the latest eval_results.json produced by tests/eval_suite.py."""
    results_file = Path(__file__).parent / "eval_results.json"
    if not results_file.exists():
        return {"available": False, "message": "No eval results yet. Run POST /admin/eval/run first."}
    try:
        data = json.loads(results_file.read_text(encoding="utf-8"))
        data["available"] = True
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read eval results: {e}")


@app.post("/admin/eval/run")
async def admin_run_eval(background_tasks: BackgroundTasks):
    """Trigger a background eval run. Results appear in /admin/eval when done."""
    import subprocess, sys
    eval_script = Path(__file__).parent / "tests" / "eval_suite.py"
    if not eval_script.exists():
        raise HTTPException(status_code=404, detail="eval_suite.py not found")

    def _run():
        try:
            subprocess.run(
                [sys.executable, str(eval_script), "--api-url", "http://localhost:8001"],
                cwd=str(Path(__file__).parent),
                timeout=300,
                capture_output=True,
            )
        except Exception as e:
            logger.error(f"Eval run failed: {e}")

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Evaluation running in background. Poll GET /admin/eval for results."}


@app.get("/admin/feedback")
async def admin_feedback():
    """Return feedback analytics for the admin dashboard."""
    import datetime
    feedback_file = Path(__file__).parent / "feedback.jsonl"
    entries = []
    if feedback_file.exists():
        with open(feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    total = len(entries)
    up = sum(1 for e in entries if e.get("type") == "up")
    down = sum(1 for e in entries if e.get("type") == "down")

    # Daily counts for last 7 days
    today = datetime.date.today()
    daily: dict[str, dict] = {}
    for i in range(6, -1, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        daily[d] = {"date": d, "up": 0, "down": 0}
    for e in entries:
        ts = e.get("timestamp", "")
        day = ts[:10] if ts else ""
        if day in daily:
            if e.get("type") == "up":
                daily[day]["up"] += 1
            elif e.get("type") == "down":
                daily[day]["down"] += 1

    # Most disliked queries (unique queries with at least one thumbs-down)
    disliked: dict[str, int] = {}
    for e in entries:
        if e.get("type") == "down":
            q = e.get("query", "").strip()
            if q:
                disliked[q] = disliked.get(q, 0) + 1
    top_disliked = sorted(disliked.items(), key=lambda x: x[1], reverse=True)[:5]

    # Recent 20 entries (newest first)
    recent = list(reversed(entries[-20:]))

    return {
        "total": total,
        "up": up,
        "down": down,
        "up_pct": round(up / total * 100, 1) if total else 0,
        "down_pct": round(down / total * 100, 1) if total else 0,
        "daily": list(daily.values()),
        "top_disliked": [{"query": q, "count": c} for q, c in top_disliked],
        "recent": recent,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
