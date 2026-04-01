from typing import List, Dict, Any
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

        # Common terms in MOSDAC data
        self.satellite_names = [
            "INSAT-3D", "INSAT-3DR", "SCATSAT-1", "Oceansat-2",
            "Megha-Tropiques", "SARAL", "Kalpana-1",
            "INSAT", "SCATSAT", "Oceansat",
        ]
        self.parameters = [
            "SST", "sea surface temperature", "rainfall", "wind",
            "humidity", "TPW", "total precipitable water",
            "OLR", "outgoing longwave radiation", "cyclone",
        ]
        self.regions = [
            "India", "Bay of Bengal", "Arabian Sea", "Himalayas",
            "Indian Ocean", "Kerala", "Gujarat",
        ]

    def index_documents(self):
        """Index knowledge graph data into the vector store."""
        docs = []

        # Index satellites with instruments
        try:
            with self.graph.driver.session() as session:
                result = session.run("""
                    MATCH (s:SATELLITE)-[:HAS_INSTRUMENT]->(i:INSTRUMENT)
                    OPTIONAL MATCH (i)-[:MEASURES]->(p:PARAMETER)
                    WITH s, i, COLLECT(DISTINCT p.name) AS parameters
                    RETURN {
                        id: elementId(s),
                        text: 'Satellite ' + s.name + ' carries ' + i.name + ' instrument' +
                              CASE WHEN size(parameters) > 0
                                   THEN ' which measures ' +
                                        REDUCE(s = '', p IN parameters | s +
                                        CASE WHEN s = '' THEN '' ELSE ', ' END + p)
                                   ELSE ''
                              END,
                        type: 'satellite',
                        satellite: s.name,
                        instrument: i.name,
                        parameters: parameters
                    } AS doc
                """)
                docs.extend([record["doc"] for record in result])
        except Exception as e:
            logger.warning(f"Failed to index satellites: {e}")

        # Index data products
        try:
            with self.graph.driver.session() as session:
                result = session.run("""
                    MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                    OPTIONAL MATCH (d)-[:COVERS]->(r:REGION)
                    WITH s, d, COLLECT(r.name) AS regions
                    RETURN {
                        id: elementId(d),
                        text: 'Data product ' + d.name + ' from ' + s.name +
                              CASE WHEN size(regions) > 0
                                   THEN ' covering ' +
                                        REDUCE(s = '', r IN regions | s +
                                        CASE WHEN s = '' THEN '' ELSE ', ' END + r)
                                   ELSE ''
                              END,
                        type: 'data_product',
                        product: d.name,
                        satellite: s.name,
                        regions: regions
                    } AS doc
                """)
                docs.extend([record["doc"] for record in result])
        except Exception as e:
            logger.warning(f"Failed to index data products: {e}")

        self.documents = docs
        if docs:
            self.vector_store.add_documents(docs)
            logger.info(f"Indexed {len(docs)} documents from knowledge graph.")
        else:
            logger.warning("No documents found in knowledge graph to index.")

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Hybrid retrieval combining vector similarity and graph pattern matching."""
        logger.info(f"Query: {query}")

        # Vector search with expanded query
        expanded_query = self._expand_query(query)
        vector_indices = self.vector_store.search(expanded_query)
        vector_results = [
            self.documents[idx]
            for idx in vector_indices
            if idx < len(self.documents)
        ]
        logger.info(f"Vector search returned {len(vector_results)} results")

        # Graph search for precise matches
        graph_results = self._graph_search(query)
        logger.info(f"Graph search returned {len(graph_results)} results")

        # Combine and rank results
        combined = self._combine_results(vector_results, graph_results)
        return combined[: Config.TOP_K]

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        expansions = {
            "sst": ["sea surface temperature", "ocean temperature"],
            "tpw": ["total precipitable water", "water vapor"],
            "olr": ["outgoing longwave radiation"],
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
        """Precise graph pattern matching."""
        results = []

        satellite = self._extract_entity(query, self.satellite_names)
        parameter = self._extract_entity(query, self.parameters)
        region = self._extract_entity(query, self.regions)

        if satellite and parameter:
            results.extend(self.graph.get_data_by_satellite_param(satellite, parameter))
        elif region and parameter:
            results.extend(self.graph.get_data_by_region_param(region, parameter))
        elif parameter:
            results.extend(self.graph.get_data_by_parameter(parameter))

        return results

    def _extract_entity(self, text: str, candidates: List[str]) -> str:
        """Extract entity from text via case-insensitive word boundary matching."""
        text_lower = text.lower()
        for candidate in candidates:
            if re.search(r"\b" + re.escape(candidate.lower()) + r"\b", text_lower):
                return candidate
        return ""

    def _combine_results(self, vector_results: List, graph_results: List) -> List:
        """Combine and deduplicate results with priority to graph matches."""
        seen = set()
        combined = []

        # Graph results first (higher precision)
        for res in graph_results:
            identifier = res.get("id") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 1.0
                combined.append(res)

        # Vector results second
        for res in vector_results:
            identifier = res.get("id") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 0.7
                combined.append(res)

        return sorted(combined, key=lambda x: x.get("score", 0), reverse=True)
