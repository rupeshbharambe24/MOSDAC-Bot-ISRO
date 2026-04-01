# ISRO SatQuery — MOSDAC Help Bot

An AI-powered Help Bot for querying ISRO's satellite data hosted on the [MOSDAC portal](https://www.mosdac.gov.in). Uses a **Knowledge Graph (Neo4j) + RAG (Retrieval-Augmented Generation)** architecture with FAISS vector search and LLM-powered response generation.

## Architecture

```
User → React Frontend (Vite + shadcn/ui)
         ↓ /api/query
       FastAPI Server
         ↓
       Hybrid Retriever
         ├── FAISS Vector Store (crawled pages + graph data)
         ├── Neo4j Knowledge Graph (satellites, products, regions)
         └── Keyword fallback search
         ↓
       LLM (Groq API: Llama 3.3 70B → local Mistral-7B fallback)
         ↓
       Response + Sources
```

**Data Pipeline:**
```
MOSDAC Website → Web Crawler → Document Processor (PDF/DOCX/HTML)
  → Text Processing (OCR, Hindi, normalization)
  → Entity Extraction (spaCy) → Relationship Extraction (BERT + patterns)
  → Knowledge Graph (Neo4j)
```

## Project Structure

```
├── api_server.py                    # FastAPI backend (4 endpoints)
├── data_collection/                 # Web crawler and document processing
│   ├── config.py                    # Crawler configuration
│   ├── crawler.py                   # Recursive MOSDAC web crawler
│   ├── document_processing.py       # PDF/DOCX/HTML text extraction
│   ├── main.py                      # Crawler entry point
│   └── storage.py                   # SQLite storage handler
├── data_processing/                 # Text processing pipeline
│   ├── main.py                      # Pipeline orchestrator (calls all processors)
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
│   └── query_interface.py           # Simple graph query API
├── rag_pipeline/                    # Retrieval-Augmented Generation
│   ├── config.py                    # All configuration (Neo4j, LLM, paths)
│   ├── retriever.py                 # Hybrid retriever (vector + graph + crawled docs)
│   ├── vector_store.py              # FAISS index with cosine similarity
│   ├── generator.py                 # Groq API + local Mistral-7B fallback
│   ├── graph_connector.py           # Neo4j Cypher queries for RAG
│   ├── app.py                       # CLI / interactive bot entry point
│   └── models/
│       └── model-download.py        # Script to download Mistral-7B GGUF
├── frontend/                        # React + TypeScript + Vite + shadcn/ui
│   └── src/
│       ├── pages/                   # Dashboard, QueryInterface, SatelliteCatalog, Index
│       └── components/              # Chat UI, sidebar, globe, error boundary
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

Run these in order to build the knowledge graph:

```bash
# 1. Crawl MOSDAC website
cd data_collection && python main.py && cd ..

# 2. Process crawled data
python -m data_processing.main

# 3. Extract entities
cd knowledge_graph_construction && python entity_extractor.py

# 4. Extract relationships
python relationship_extractor.py

# 5. Build Neo4j graph
python graph_builder.py && cd ..
```

## API Endpoints

| Method | Endpoint      | Description                          |
|--------|---------------|--------------------------------------|
| POST   | `/query`      | Natural language query with conversation history |
| GET    | `/health`     | Health check                         |
| GET    | `/satellites` | List all satellites from knowledge graph |
| GET    | `/stats`      | Knowledge graph statistics           |

### Example

```bash
curl -X POST http://localhost:8001/query \
     -H "Content-Type: application/json" \
     -d '{"message": "What is MOSDAC?", "history": []}'
```

## Knowledge Graph Schema (Neo4j)

```cypher
(:SATELLITE {name, source})
(:DATA_PRODUCT {name, source})
(:PARAMETER {name})
(:REGION {name, lat, lon})

(:SATELLITE)-[:PROVIDES]->(:DATA_PRODUCT)
(:DATA_PRODUCT)-[:MEASURES]->(:PARAMETER)
(:DATA_PRODUCT)-[:COVERS]->(:REGION)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq API (Llama 3.3 70B) with local Mistral-7B fallback |
| **Backend API** | FastAPI + Uvicorn |
| **Knowledge Graph** | Neo4j (py2neo + neo4j driver) |
| **Vector Search** | FAISS (cosine similarity) + sentence-transformers |
| **NLP** | spaCy, Transformers (BERT) |
| **Frontend** | React 18 + TypeScript + Vite |
| **UI Components** | shadcn/ui + Tailwind CSS |
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
| `POPPLER_PATH` | Path to poppler binaries | system default |

## Features

- **Chat interface** with conversation history persistence (localStorage)
- **Multi-turn conversation** — sends last 6 messages as context to LLM
- **Hybrid retrieval** — combines vector similarity search with knowledge graph queries
- **Crawled document indexing** — 131 MOSDAC web pages indexed for general knowledge queries
- **Dashboard** with live stats from knowledge graph (with fallback defaults)
- **Satellite catalog** with search, filtering, and JSON export
- **Sidebar quick templates** that auto-send queries to the chat
- **Dark/light mode** toggle
- **Error boundary** for crash recovery
- **Sub-second responses** via Groq API

## Sample Queries

```
What is MOSDAC?
What data products does INSAT-3DR provide?
Which satellites provide rainfall data?
What is sea surface temperature data?
How do I access data from MOSDAC?
Tell me about SCATSAT-1
```

## Known Limitations

- Knowledge graph entity quality depends on BERT relationship extractor (not yet fine-tuned on domain data)
- Some graph nodes contain noisy entity names from automated extraction
- Hindi language support is basic (blank spaCy model + pattern matching)
- No authentication — designed for local/demo use

## Author

**Rupesh Bharambe** — [GitHub](https://github.com/rupeshbharambe24)

Built for ISRO's MOSDAC portal as part of the SentinelX team project.
