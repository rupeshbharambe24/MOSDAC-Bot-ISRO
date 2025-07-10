# 🚀 ISRO SatQuery

**A Knowledge Graph + LLM Powered Conversational Assistant for Satellite Data Querying**  
🔗 Website & Demo: [ISRO SatQuery](https://www.mosdac.gov.in/)

![MOSDAC Logo](https://www.mosdac.gov.in/assets/images/logo.png)

---

## 📚 Table of Contents

- [🔍 Project Overview](#-project-overview)
- [🧠 Backend Architecture](#-backend-architecture)
- [🛰️ Knowledge Graph Construction](#-knowledge-graph-construction)
- [🧪 Retrieval-Augmented Generation (RAG) Pipeline](#-retrieval-augmented-generation-rag-pipeline)
- [🧩 API Server & Endpoints](#-api-server--endpoints)
- [⚙️ Installation](#️-installation)
- [🔧 Configuration](#-configuration)
- [🚀 Usage Guide](#-usage-guide)
- [🧪 Testing](#-testing)
- [☁️ Deployment](#-deployment)
- [💻 Frontend Interface](#-frontend-interface)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)

---

## 🔍 Project Overview

**ISRO SatQuery** is an AI-based Help Bot system designed to simplify access to ISRO's scientific and satellite datasets hosted on the [MOSDAC portal](https://www.mosdac.gov.in). The platform allows users to interact through natural language and get instant, precise answers about satellite missions, instruments, parameters, geospatial data, and more.

### 🔑 Key Features

- 🚀 LLM + Graph-powered hybrid answering
- 🧠 Knowledge Graph built from PDFs, DOCX, XLSX, and website content
- 🌐 Geospatial query support
- ⚙️ Local or remote model inference (e.g., Mistral, Phi-3)
- 💡 Modular and scalable architecture

---

## 🧠 Backend Architecture

```mermaid
graph TD
    A[User Query] --> B[API Server]
    B --> C[Hybrid Retriever]
    C --> D[Neo4j Graph DB]
    C --> E[Vector Store - FAISS / ChromaDB]
    D --> F[Graph Results]
    E --> G[Vector Results]
    F --> H[LLM-based Answer Generator]
    G --> H
    H --> I[Final Response - Text / Voice]
````

---

## 🛰️ Knowledge Graph Construction

### 📐 Graph Schema (Neo4j)

```cypher
(:SATELLITE {name, launch_date})
(:INSTRUMENT {name, type})
(:DATA_PRODUCT {name, resolution})
(:PARAMETER {name, unit})
(:REGION {name, lat, lon})

(:SATELLITE)-[:HAS_INSTRUMENT]->(:INSTRUMENT)
(:SATELLITE)-[:PROVIDES]->(:DATA_PRODUCT)
(:INSTRUMENT)-[:MEASURES]->(:PARAMETER)
(:DATA_PRODUCT)-[:COVERS]->(:REGION)
```

### 🔧 Graph Components

| File                        | Purpose                               |
| --------------------------- | ------------------------------------- |
| `graph_builder.py`          | Constructs the full graph in Neo4j    |
| `entity_extractor.py`       | Named Entity Recognition using spaCy  |
| `relationship_extractor.py` | BERT-based relationship mapping       |
| `geo_utils.py`              | Geospatial parsing and region tagging |

### 🧾 Sample Output

```json
{
  "text": "INSAT-3D carries VHRR and SAPHIR instruments",
  "entities": [
    {"text": "INSAT-3D", "label": "SATELLITE"},
    {"text": "VHRR", "label": "INSTRUMENT"},
    {"text": "SAPHIR", "label": "INSTRUMENT"}
  ],
  "relations": [
    {"head": "INSAT-3D", "tail": "VHRR", "type": "HAS_INSTRUMENT"},
    {"head": "INSAT-3D", "tail": "SAPHIR", "type": "HAS_INSTRUMENT"}
  ]
}
```

---

## 🧪 Retrieval-Augmented Generation (RAG) Pipeline

### 📥 Retriever (`retriever.py`)

* Vector-based semantic retrieval using `all-mpnet-base-v2`
* Graph-based Cypher query generation
* Entity linking from user queries

### 🤖 Generator (`generator.py`)

* Uses **Mistral 7B** or **Phi-3** via GGUF/HuggingFace
* Formats answers with citations and confidence scores

### 📦 Vector Store (`vector_store.py`)

* Embedding generation via `SentenceTransformers`
* FAISS/ChromaDB for indexing and retrieval
* Supports batch document ingestion

---

## 🧩 API Server & Endpoints

Built using **FastAPI** for async web serving.

### 🚀 Endpoints

| Method | Endpoint      | Description                       |
| ------ | ------------- | --------------------------------- |
| POST   | `/query`      | Query answering interface         |
| GET    | `/stats`      | Basic knowledge graph statistics  |
| GET    | `/satellites` | Returns list of parsed satellites |

### 🔁 Sample Request

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question":"Which satellite provides SST data for India?"}'
```

---

## ⚙️ Installation

### ✅ Prerequisites

* Python 3.9+
* Neo4j 5.x (with Bloom plugin)
* CUDA-compatible GPU (for local LLM inference)

### 🧰 Steps

```bash
# Clone repository
git clone https://github.com/<your-org>/ISRO-SatQuery.git
cd ISRO-SatQuery

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Download models
python download_models.py
```

---

## 🔧 Configuration

Create a `.env` file in the root directory:

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

EMBEDDING_MODEL=all-mpnet-base-v2
LLM_MODEL=mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

---

## 🚀 Usage Guide

### 🛠️ Build the Knowledge Graph

```bash
python build_graph.py --entities ./data/entities --relations ./data/relations
```

### 🧠 Run the API Server

```bash
uvicorn api_server:app --reload
```

### 📡 Sample Python Query

```python
from client import SatQueryClient

client = SatQueryClient()
response = client.query("List all instruments on INSAT-3D")
print(response)
```

---

## 🧪 Testing

Run the test suite and check coverage:

```bash
pytest tests/ --cov=.
```

### ✔️ Tests Cover

* Entity & relation extraction
* Graph structure validation
* API behavior & edge cases
* LLM answer formatting

---

## ☁️ Deployment

### 🐳 Docker

```bash
docker-compose up -d
```

### ☸️ Kubernetes

```bash
kubectl apply -f k8s/
```

---

## 💻 Frontend Interface

> The ISRO SatQuery frontend provides an intuitive chat interface for interacting with the satellite knowledge system.

### 🌐 Core Features

* Conversational UI with chat memory
* Answer explanation with source links and confidence
* Prebuilt query templates
* Fully mobile-responsive design
* Accessibility compliant (WCAG 2.1)

### 🛠️ Tech Stack

* **React.js + TypeScript**
* **Tailwind CSS + ShadCN UI**
* **Context API** for state management
* **Axios** for backend integration
* **Vite** for fast build setup

### 🔗 API Integration

* `POST /query` – LLM question answering
* `GET /satellites` – Lists available data
* Optional JWT authentication layer

### 🧱 UI Components

* Chat bubbles + loading animation
* Source/reference panel
* Suggested queries
* Feedback (👍 / 👎)

### 📱 Mobile Features

* Touch-friendly controls
* Offline-first mode with service workers
* Low-bandwidth optimization

---

## 🤝 Contributing

We welcome community contributions! 🚀

```bash
# Fork the repo
# Create your branch
git checkout -b feature/awesome-feature

# Commit your changes
git commit -am "Added awesome feature"

# Push and create PR
git push origin feature/awesome-feature
```

---

## 📝 License

This project is licensed under the **GNU General Public License v3.0**.
See the [LICENSE](./LICENSE) file for details.

---

> © 2025 — Team SentinelX | Hackathon Finalist | ISRO SatQuery 🌍🛰️
