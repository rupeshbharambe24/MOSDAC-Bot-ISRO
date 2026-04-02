from typing import List, Dict, Any
from pathlib import Path
import json
from rag_pipeline.graph_connector import GraphConnector
from rag_pipeline.vector_store import VectorStore
from rag_pipeline.config import Config
import re
import logging

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self):
        self.graph = GraphConnector()
        self.vector_store = VectorStore()
        self.documents = []

        self.satellite_names = [
            "INSAT-3D", "INSAT-3DR", "INSAT-3A", "INSAT",
            "SCATSAT-1", "SCATSAT", "Oceansat-2", "Oceansat",
            "Megha-Tropiques", "SARAL", "Kalpana-1", "Kalpana",
        ]
        self.parameters = [
            "SST", "sea surface temperature", "rainfall", "wind",
            "humidity", "TPW", "total precipitable water",
            "OLR", "outgoing longwave radiation", "cyclone",
            "temperature", "cloud", "snow", "ice", "chlorophyll",
        ]
        self.regions = [
            "India", "Bay of Bengal", "Arabian Sea", "Himalayas",
            "Indian Ocean", "Kerala", "Gujarat",
        ]

    def index_documents(self):
        """Index knowledge graph data into the vector store."""
        docs = []

        # Index satellites with their products (uses PROVIDES, not HAS_INSTRUMENT)
        try:
            with self.graph.driver.session() as session:
                result = session.run("""
                    MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                    WITH s, COLLECT(DISTINCT d.name)[..10] AS products
                    RETURN {
                        id: elementId(s),
                        text: 'Satellite ' + s.name + ' provides data products: ' +
                              REDUCE(acc = '', p IN products | acc +
                              CASE WHEN acc = '' THEN '' ELSE ', ' END + p),
                        type: 'satellite',
                        satellite: s.name,
                        products: products
                    } AS doc
                """)
                satellite_docs = [record["doc"] for record in result]
                docs.extend(satellite_docs)
                logger.info(f"Indexed {len(satellite_docs)} satellites")
        except Exception as e:
            logger.warning(f"Failed to index satellites: {e}")

        # Index data products individually (top 200 to keep index manageable)
        try:
            with self.graph.driver.session() as session:
                result = session.run("""
                    MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                    OPTIONAL MATCH (d)-[:COVERS]->(r:REGION)
                    WITH s, d, COLLECT(DISTINCT r.name)[..5] AS regions
                    RETURN {
                        id: elementId(d),
                        text: 'Data product ' + d.name + ' from satellite ' + s.name +
                              CASE WHEN size(regions) > 0
                                   THEN ' covering ' +
                                        REDUCE(acc = '', r IN regions | acc +
                                        CASE WHEN acc = '' THEN '' ELSE ', ' END + r)
                                   ELSE ''
                              END,
                        type: 'data_product',
                        product: d.name,
                        satellite: s.name,
                        regions: regions
                    } AS doc
                    LIMIT 200
                """)
                product_docs = [record["doc"] for record in result]
                docs.extend(product_docs)
                logger.info(f"Indexed {len(product_docs)} data products")
        except Exception as e:
            logger.warning(f"Failed to index data products: {e}")

        # Index parameters
        try:
            with self.graph.driver.session() as session:
                result = session.run("""
                    MATCH (p:PARAMETER)
                    OPTIONAL MATCH (d:DATA_PRODUCT)-[:MEASURES]->(p)
                    WITH p, COLLECT(DISTINCT d.name)[..5] AS measured_by
                    RETURN {
                        id: elementId(p),
                        text: 'Parameter ' + p.name +
                              CASE WHEN size(measured_by) > 0
                                   THEN ' measured by ' +
                                        REDUCE(acc = '', d IN measured_by | acc +
                                        CASE WHEN acc = '' THEN '' ELSE ', ' END + d)
                                   ELSE ''
                              END,
                        type: 'parameter',
                        name: p.name
                    } AS doc
                """)
                param_docs = [record["doc"] for record in result]
                docs.extend(param_docs)
                logger.info(f"Indexed {len(param_docs)} parameters")
        except Exception as e:
            logger.warning(f"Failed to index parameters: {e}")

        # Index curated knowledge base (highest quality, added first)
        curated_docs = self._load_curated_knowledge()
        docs.extend(curated_docs)

        # Index crawled web pages for general knowledge queries
        crawled_docs = self._load_crawled_documents()
        docs.extend(crawled_docs)

        self.documents = docs
        graph_count = len(docs) - len(crawled_docs) - len(curated_docs)
        if docs:
            self.vector_store.add_documents(docs)
            logger.info(
                f"Total indexed: {len(docs)} documents "
                f"({graph_count} graph + {len(curated_docs)} curated + {len(crawled_docs)} crawled)"
            )
        else:
            logger.warning("No documents found to index.")

    def _load_curated_knowledge(self) -> List[Dict]:
        """Load hand-curated MOSDAC knowledge base."""
        kb_path = Path(__file__).parent / "mosdac_knowledge.json"
        if not kb_path.exists():
            logger.warning("Curated knowledge base not found")
            return []
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                docs = json.load(f)
            logger.info(f"Loaded {len(docs)} curated knowledge entries")
            return docs
        except Exception as e:
            logger.warning(f"Failed to load curated knowledge: {e}")
            return []

    def _load_crawled_documents(self) -> List[Dict]:
        """Load crawled documents with proper text chunking.

        Loads from both raw crawled dir and processed output dir,
        deduplicating by source_url (preferring processed versions).
        Long documents are split into ~800-char chunks with ~100-char overlap.
        """
        base_dir = Path(Config.BASE_DIR)
        raw_dir = base_dir / "data_collection" / "data" / "mosdac" / "processed"
        processed_dir = base_dir / "data_processing" / "processed_output"

        # Collect JSON files keyed by source_url (processed overwrites raw)
        source_map: Dict[str, Dict] = {}
        for data_dir in [raw_dir, processed_dir]:
            if not data_dir.exists():
                continue
            for json_file in data_dir.rglob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    text = data.get("text", "")
                    if not text or len(text) < 50:
                        continue
                    source_url = data.get("source_url", str(json_file.stem))
                    source_map[source_url] = {
                        "text": text,
                        "source_url": source_url,
                        "content_type": data.get("content_type", "html"),
                        "stem": json_file.stem,
                    }
                except Exception:
                    continue

        # Chunk documents
        docs = []
        page_count = 0
        for entry in source_map.values():
            page_count += 1
            chunks = self._chunk_text(entry["text"], chunk_size=800, overlap=100)
            for i, chunk in enumerate(chunks):
                docs.append({
                    "id": f"crawled_{entry['stem']}_c{i}",
                    "text": chunk,
                    "type": "crawled_page",
                    "source_url": entry["source_url"],
                    "content_type": entry["content_type"],
                    "chunk_index": i,
                })

        logger.info(f"Loaded {len(docs)} chunks from {page_count} crawled pages")
        return docs

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split text into chunks on sentence boundaries with overlap."""
        text = text.strip()
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]

        sentences = re.split(r'(?<=\. )|(?<=\n)', text)
        sentences = [s for s in sentences if s]

        chunks: List[str] = []
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) > chunk_size:
                chunks.append(current.strip())
                # Start next chunk with overlap
                tail = current[-overlap:] if len(current) >= overlap else current
                space = tail.find(" ")
                if space != -1:
                    tail = tail[space + 1:]
                current = tail + sentence
            else:
                current += sentence
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Hybrid retrieval combining vector similarity and graph pattern matching."""
        logger.info(f"Query: {query}")

        # Vector search
        expanded_query = self._expand_query(query)
        vector_indices = self.vector_store.search(expanded_query)
        vector_results = [
            self.documents[idx]
            for idx in vector_indices
            if idx < len(self.documents)
        ]
        logger.info(f"Vector search returned {len(vector_results)} results")

        # Graph search
        graph_results = self._graph_search(query)
        logger.info(f"Graph search returned {len(graph_results)} results")

        # Combine and rank
        combined = self._combine_results(vector_results, graph_results)
        return combined[: Config.TOP_K]

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms."""
        expansions = {
            "sst": ["sea surface temperature", "ocean temperature"],
            "tpw": ["total precipitable water", "water vapor"],
            "olr": ["outgoing longwave radiation"],
            "mosdac": ["MOSDAC satellite data meteorological oceanographic"],
            "india": ["Indian region", "South Asia"],
            "data": ["dataset", "product", "observation"],
            "cyclone": ["tropical cyclone", "hurricane", "storm"],
            "wind": ["wind speed", "wind vectors", "ocean wind"],
            "rain": ["rainfall", "precipitation"],
        }
        expanded = query.lower()
        for term, synonyms in expansions.items():
            if term in expanded:
                expanded += " " + " ".join(synonyms)
        return expanded

    def _graph_search(self, query: str) -> List[Dict]:
        """Graph pattern matching based on extracted entities."""
        results = []

        satellite = self._extract_entity(query, self.satellite_names)
        parameter = self._extract_entity(query, self.parameters)
        region = self._extract_entity(query, self.regions)

        if satellite and parameter:
            results.extend(self.graph.get_data_by_satellite_param(satellite, parameter))
        elif satellite:
            results.extend(self.graph.get_data_by_satellite(satellite))
        elif region and parameter:
            results.extend(self.graph.get_data_by_region_param(region, parameter))
        elif parameter:
            results.extend(self.graph.get_data_by_parameter(parameter))

        # Fallback: broad search if no structured match
        if not results:
            # Try searching for any keyword from the query
            keywords = [w for w in query.split() if len(w) > 3]
            for kw in keywords[:3]:
                results.extend(self.graph.search_all(kw))
                if results:
                    break

        return results

    def _extract_entity(self, text: str, candidates: List[str]) -> str:
        """Extract entity from text via case-insensitive word boundary matching."""
        text_lower = text.lower()
        for candidate in candidates:
            if re.search(r"\b" + re.escape(candidate.lower()) + r"\b", text_lower):
                return candidate
        return ""

    def _combine_results(self, vector_results: List, graph_results: List) -> List:
        """Combine and deduplicate results. Curated > crawled > graph."""
        seen = set()
        combined = []

        # Score by source quality: curated > crawled pages > graph data
        for res in vector_results:
            identifier = res.get("id") or res.get("name") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                doc_type = res.get("type", "")
                if doc_type == "curated":
                    res["score"] = 1.5  # Highest priority
                elif doc_type == "crawled_page":
                    res["score"] = 0.9
                else:
                    res["score"] = 0.7
                combined.append(res)

        for res in graph_results:
            identifier = res.get("id") or res.get("name") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 0.6  # Graph data (noisy) gets lower priority
                combined.append(res)

        return sorted(combined, key=lambda x: x.get("score", 0), reverse=True)
