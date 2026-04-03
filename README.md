# SatSage — AI Satellite Data Query Assistant

An AI-powered Help Bot for querying ISRO's satellite data hosted on the [MOSDAC portal](https://www.mosdac.gov.in). Uses a **Knowledge Graph (Neo4j) + RAG (Retrieval-Augmented Generation)** architecture with FAISS vector search and LLM-powered response generation.

## Architecture

```
User → React Frontend (Vite + shadcn/ui)
         ↓ /api/query/stream (SSE)
       FastAPI Server
         ↓
       Hybrid Retriever
         ├── FAISS Vector Store (crawled pages + graph data)
         ├── Neo4j Knowledge Graph (satellites, products, regions)
         └── Keyword fallback search
         ↓
       LLM (Groq API: Llama 3.3 70B → local Mistral-7B fallback)
         ↓
       Streaming Response + Sources
```

**Data Pipeline:**
```
MOSDAC Website → Web Crawler → Document Processor (PDF/DOCX/HTML)
  → Text Processing (OCR, Hindi, normalization)
  → Entity Extraction (spaCy) → Relationship Extraction (BERT + patterns)
  → BERT Relation Classifier (fine-tuned, F1 ≈ 0.92)
  → Knowledge Graph (Neo4j)  →  FAISS Vector Index
```

## Project Structure

```
├── api_server.py                    # FastAPI backend + admin endpoints
├── data_collection/                 # Web crawler and document processing
│   ├── config.py
│   ├── crawler.py                   # Recursive MOSDAC web crawler
│   ├── document_processing.py       # PDF/DOCX/HTML text extraction
│   ├── main.py
│   └── storage.py
├── data_processing/                 # Text processing pipeline
│   ├── main.py
│   ├── schemas.py
│   └── processors/
│       ├── text_normalizer.py
│       ├── language_handler.py
│       ├── metadata_enricher.py
│       └── ocr_cleaner.py
├── knowledge_graph_construction/    # Neo4j graph building
│   ├── entity_extractor.py
│   ├── relationship_extractor.py
│   ├── graph_builder.py
│   ├── graph_cleaner.py
│   ├── train_classifier.py          # Fine-tune BERT relation classifier
│   ├── rebuild_graph.py             # Re-validate and clean graph edges
│   ├── restore_parameters.py        # Recreate PARAMETER nodes + edges
│   ├── training_data_curated.json   # 342 curated training examples
│   └── query_interface.py
├── rag_pipeline/                    # Retrieval-Augmented Generation
│   ├── config.py
│   ├── retriever.py                 # Hybrid retriever (vector + graph + crawled)
│   ├── vector_store.py              # FAISS index with cosine similarity
│   ├── generator.py                 # Groq API + local Mistral-7B fallback
│   ├── graph_connector.py
│   └── models/
│       └── model-download.py
├── pipeline.py                      # One-click automation pipeline (8 steps)
├── tests/
│   └── eval_suite.py                # 38-test evaluation suite (4 metric categories)
├── frontend/                        # React + TypeScript + Vite + shadcn/ui
│   └── src/
│       ├── pages/
│       │   ├── QueryInterface.tsx   # Chat + streaming + PDF export
│       │   ├── Dashboard.tsx        # Live KG stats
│       │   ├── SatelliteCatalog.tsx # Search, filter, JSON export
│       │   └── AdminDashboard.tsx   # Feedback analytics + eval metrics + pipeline
│       └── components/
│           ├── query/
│           │   ├── ChatMessage.tsx  # Markdown, coverage map toggle
│           │   └── CoverageMap.tsx  # Leaflet geospatial map (14 regions)
│           └── layout/
├── requirements.txt
├── setup.py
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.10+**
- **Neo4j 5.x** — running on `bolt://localhost:7687`
- **Node.js 18+** — for the frontend
- **Groq API key** (free) — get it at https://console.groq.com/keys
- **System packages** (optional):
  - `poppler-utils` — for PDF processing
  - `tesseract-ocr` — for Hindi OCR

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/rupeshbharambe24/MOSDAC-Bot-ISRO.git
cd MOSDAC-Bot-ISRO

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm

# 4. Configure environment
cp .env.example .env
# Edit .env — set NEO4J_PASSWORD and GROQ_API_KEY

# 5. Start Neo4j, then run the API server
uvicorn api_server:app --reload --port 8001

# 6. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:8080** and start querying.

## Data Pipeline (first-time setup)

### Option A — One-click automation (recommended)

```bash
# Run the full 8-step pipeline (Neo4j must be running)
python pipeline.py

# Skip BERT training (quick reindex after new data)
python pipeline.py --skip-train

# Resume from a specific step (e.g. after a failure)
python pipeline.py --from-step 3
```

The pipeline writes live progress to `pipeline_status.json`, visible in the **Admin Dashboard → Pipeline tab**.

| Step | Script | Output |
|------|--------|--------|
| 1 | `data_collection/main.py` | Raw docs |
| 2 | `data_processing/main.py` | Cleaned JSON |
| 3 | `entity_extractor.py` | `entities/` dir |
| 4 | `relationship_extractor.py` | `relations/` dir |
| 5 | `graph_builder.py` | Neo4j populated |
| 6 | `train_classifier.py` | Trained BERT model |
| 7 | `rebuild_graph.py --execute` | Clean graph |
| 8 | FAISS reindex | Updated vector index |

### Option B — Manual step-by-step

```bash
cd data_collection && python main.py && cd ..
python -m data_processing.main
cd knowledge_graph_construction
python entity_extractor.py
python relationship_extractor.py
python graph_builder.py
python train_classifier.py --epochs 15
python rebuild_graph.py --execute
python restore_parameters.py
cd ..
```

## API Endpoints

| Method | Endpoint              | Description |
|--------|-----------------------|-------------|
| POST   | `/query`              | Natural language query (full response) |
| POST   | `/query/stream`       | SSE streaming response |
| POST   | `/feedback`           | Store thumbs up/down feedback |
| GET    | `/health`             | Health check |
| GET    | `/satellites`         | List all satellites from knowledge graph |
| GET    | `/stats`              | Knowledge graph statistics |
| GET    | `/admin/feedback`     | Feedback analytics (counts, daily trend, recent log) |
| GET    | `/admin/eval`         | Latest evaluation metrics results |
| POST   | `/admin/eval/run`     | Trigger background evaluation run |
| GET    | `/admin/pipeline/status` | Live pipeline step progress |
| POST   | `/admin/pipeline/run` | Trigger full automation pipeline |

### Example

```bash
curl -X POST http://localhost:8001/query \
     -H "Content-Type: application/json" \
     -d '{"message": "What data does INSAT-3D provide?", "history": []}'
```

## Knowledge Graph Schema (Neo4j)

```cypher
(:SATELLITE {name, source})
(:INSTRUMENT {name})
(:DATA_PRODUCT {name, source})
(:PARAMETER {name})
(:REGION {name, lat, lon})

(:SATELLITE)-[:PROVIDES]->(:DATA_PRODUCT)
(:SATELLITE)-[:HAS_INSTRUMENT]->(:INSTRUMENT)
(:INSTRUMENT)-[:MEASURES]->(:PARAMETER)
(:DATA_PRODUCT)-[:COVERS]->(:REGION)
```

**Cleaned graph stats (post-classifier):** 12 satellites · 154 products · 13 parameters · 123 regions · 828 indexed documents

## Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | Groq API (Llama 3.3 70B) + local Mistral-7B fallback |
| **Backend API** | FastAPI + Uvicorn (SSE streaming) |
| **Knowledge Graph** | Neo4j (py2neo + neo4j driver) |
| **Vector Search** | FAISS (cosine similarity) + sentence-transformers |
| **NLP / ML** | spaCy, HuggingFace Transformers (BERT fine-tuned) |
| **Frontend** | React 18 + TypeScript + Vite |
| **UI Components** | shadcn/ui + Tailwind CSS + Recharts |
| **Maps** | Leaflet.js (vanilla, no react-leaflet) |
| **PDF Export** | jsPDF |
| **Data Extraction** | pdfplumber, python-docx, BeautifulSoup |

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | (required) |
| `GROQ_API_KEY` | Groq API key for LLM | (recommended) |
| `GROQ_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `N_GPU_LAYERS` | GPU layers for local LLM fallback | `0` |

## Features

- **Streaming chat** with SSE — tokens appear in real time as LLM generates
- **Conversation history** persistence (localStorage, last 6 messages sent as context)
- **Hybrid retrieval** — curated KB → vector similarity → graph Cypher → keyword fallback
- **Geospatial coverage map** — Leaflet map with 14 MOSDAC regions; auto-detected from bot response; 3 tile styles (Dark / Satellite / Light)
- **Export chat as PDF** — branded A4 layout with source citations, page numbers
- **Admin dashboard** (`/admin`) — three tabs: Feedback (thumbs up/down analytics, 7-day trend chart, recent log) · Eval Metrics (overall score, radar chart, per-test detail) · Pipeline (live step progress, run/resume/skip controls)
- **One-click automation pipeline** (`pipeline.py`) — 8-step orchestrator: scrape → process → entity extraction → relationship extraction → graph build → BERT train → graph clean → FAISS reindex; supports `--skip-train` and `--from-step N`
- **Evaluation suite** (`tests/eval_suite.py`) — 38 tests across entity extraction, query expansion, retrieval quality, response quality; run offline or against live API
- **Fine-tuned BERT relation classifier** (F1 ≈ 0.92) used to validate and clean all graph edges
- **Dashboard** with live KG stats · **Satellite catalog** with search + JSON export
- **Dark/light mode** · **Error boundary** · **Mobile-responsive sidebar**
- **Sub-second responses** via Groq API

## Sample Queries

```
What is MOSDAC?
What data products does INSAT-3DR provide?
Which satellites provide rainfall data for the Bay of Bengal?
Tell me about sea surface temperature products
How do I access data from MOSDAC?
Track cyclone formation using SCATSAT-1
```

## Running the Evaluation Suite

```bash
# Full suite (requires API server running on port 8001)
python tests/eval_suite.py

# Offline mode — entity extraction and query expansion only
python tests/eval_suite.py --offline

# Custom API URL
python tests/eval_suite.py --api-url http://localhost:8001
```

Results are saved to `eval_results.json` and visible in the Admin Dashboard → Eval Metrics tab.

## Known Limitations

- Hindi language support is basic (pattern matching only)
- No authentication — designed for local/demo use
- Knowledge graph quality depends on automated entity extraction (some noisy names remain)

## Author

**Rupesh Bharambe** — [GitHub](https://github.com/rupeshbharambe24)

Built as part of **ISRO's Bharatiya Antariksh Hackathon 2025**.
