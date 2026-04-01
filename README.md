# ISRO SatQuery — MOSDAC Help Bot

An AI-powered Help Bot for querying ISRO's satellite data hosted on the [MOSDAC portal](https://www.mosdac.gov.in). Uses a Knowledge Graph (Neo4j) + RAG (Retrieval-Augmented Generation) architecture with FAISS vector search and a local Mistral-7B LLM.

## Architecture

```
User → React Frontend (Vite + shadcn/ui)
         ↓ /api/query
       FastAPI Server (api_server.py)
         ↓
       Hybrid Retriever
         ├── FAISS Vector Store (sentence-transformers embeddings)
         └── Neo4j Knowledge Graph (satellites, instruments, parameters)
         ↓
       Mistral-7B Local LLM (llama.cpp, GGUF quantized)
         ↓
       Response + Sources
```

**Data Pipeline:**
```
MOSDAC Website → Web Crawler → Document Processor (PDF/DOCX/HTML)
  → Text Processing (OCR, Hindi, normalization)
  → Entity Extraction (spaCy) → Relationship Extraction (BERT + patterns)
  → Knowledge Graph (Neo4j) → Graph Cleaning (classifier)
```

## Project Structure

```
├── api_server.py                    # FastAPI backend (POST /query, GET /health)
├── data_collection/                 # Web crawler and document processing
│   ├── config.py                    # Crawler configuration
│   ├── crawler.py                   # Recursive MOSDAC web crawler
│   ├── document_processing.py       # PDF/DOCX/HTML text extraction
│   ├── main.py                      # Crawler entry point
│   └── storage.py                   # SQLite storage handler
├── data_processing/                 # Text processing pipeline
│   ├── main.py                      # Pipeline orchestrator
│   ├── schemas.py                   # Pydantic document model
│   └── processors/
│       ├── text_normalizer.py       # Encoding, dates, acronyms, whitespace
│       ├── language_handler.py      # Language detection + Hindi transliteration
│       ├── metadata_enricher.py     # Document type + keyword extraction (spaCy)
│       └── ocr_cleaner.py           # Hindi OCR artifact cleaning
├── knowledge_graph_construction/    # Neo4j graph building
│   ├── entity_extractor.py          # spaCy NER for satellites, instruments, etc.
│   ├── relationship_extractor.py    # BERT + pattern-based relation extraction
│   ├── graph_builder.py             # Neo4j graph construction (py2neo)
│   ├── graph_cleaner.py             # BERT classifier to validate relationships
│   ├── query_interface.py           # Simple graph query API
│   ├── data_collector.py            # Training data generator for classifier
│   └── training_data.py             # Auto-generated training examples
├── rag_pipeline/                    # Retrieval-Augmented Generation
│   ├── config.py                    # Model paths, Neo4j credentials, thresholds
│   ├── retriever.py                 # Hybrid retriever (vector + graph)
│   ├── vector_store.py              # FAISS index with cosine similarity
│   ├── generator.py                 # Mistral-7B response generation (llama.cpp)
│   ├── graph_connector.py           # Neo4j Cypher queries for RAG
│   ├── app.py                       # CLI / interactive bot entry point
│   └── models/
│       └── model-download.py        # Script to download Mistral-7B GGUF
├── frontend/                        # React + TypeScript + Vite + shadcn/ui
│   └── src/
│       ├── pages/                   # Dashboard, QueryInterface, SatelliteCatalog
│       └── components/              # Chat UI, sidebar, globe visualization
├── requirements.txt
├── setup.py
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.10+**
- **Neo4j 5.x** — running on `bolt://localhost:7687`
- **Node.js 18+** — for the frontend
- **System packages:**
  - `poppler-utils` (for PDF processing)
  - `tesseract-ocr` (for Hindi OCR, optional)

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/rupeshbharambe24/ISRO-SatQuery.git
cd ISRO-SatQuery

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm

# 4. Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials

# 5. Download the LLM model (~4GB)
python rag_pipeline/models/model-download.py

# 6. Start Neo4j, then run the API server
uvicorn api_server:app --reload --port 8000

# 7. Start the frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:8080` and proxies API calls to the FastAPI backend at port 8000.

## API Endpoints

| Method | Endpoint  | Description                |
|--------|-----------|----------------------------|
| POST   | `/query`  | Process a natural language query |
| GET    | `/health` | Health check               |

### Example

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"message": "Which satellite provides SST data for India?"}'
```

## Knowledge Graph Schema (Neo4j)

```cypher
(:SATELLITE {name, source})
(:INSTRUMENT {name, source})
(:DATA_PRODUCT {name, source})
(:PARAMETER {name})
(:REGION {name, lat, lon})

(:SATELLITE)-[:HAS_INSTRUMENT]->(:INSTRUMENT)
(:SATELLITE)-[:PROVIDES]->(:DATA_PRODUCT)
(:INSTRUMENT)-[:MEASURES]->(:PARAMETER)
(:DATA_PRODUCT)-[:COVERS]->(:REGION)
```

## Pipeline Steps

1. **Data Collection** — `python data_collection/main.py` crawls MOSDAC and extracts text from HTML/PDF/DOCX
2. **Data Processing** — `python -m data_processing.main` normalizes text, detects language, extracts keywords
3. **Entity Extraction** — `python knowledge_graph_construction/entity_extractor.py` extracts satellites, instruments, parameters
4. **Relationship Extraction** — `python knowledge_graph_construction/relationship_extractor.py` finds relations between entities
5. **Graph Construction** — `python knowledge_graph_construction/graph_builder.py` builds the Neo4j knowledge graph
6. **Query** — `uvicorn api_server:app` serves the API, or `python rag_pipeline/app.py` for CLI mode

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI + Uvicorn |
| Knowledge Graph | Neo4j (py2neo + neo4j driver) |
| Vector Search | FAISS + sentence-transformers |
| Local LLM | Mistral-7B via llama-cpp-python |
| NLP | spaCy, Transformers (BERT) |
| Frontend | React 18 + TypeScript + Vite |
| UI Components | shadcn/ui + Tailwind CSS |
| Data Extraction | pdfplumber, python-docx, BeautifulSoup |

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | (required) |
| `N_GPU_LAYERS` | GPU layers for LLM | `0` (CPU only) |
| `POPPLER_PATH` | Path to poppler binaries | system default |

## Status

**Working:**
- Chat interface with real backend integration
- Web crawler for MOSDAC portal
- Document processing (PDF, DOCX, HTML)
- Text normalization and Hindi OCR cleaning
- Entity extraction (spaCy)
- Knowledge graph construction (Neo4j)
- Hybrid retrieval (vector + graph)
- Local LLM response generation
- Sidebar templates → chat integration

**In Progress:**
- Dashboard and catalog API integration (currently using sample data)
- BERT relationship classifier fine-tuning
- Training data quality improvement

## Author

**Rupesh Bharambe** — [GitHub](https://github.com/rupeshbharambe24)

Built for ISRO's MOSDAC portal as part of the SentinelX team project.
