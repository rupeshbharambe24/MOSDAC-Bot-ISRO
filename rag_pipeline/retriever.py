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

        self.documents = docs
        if docs:
            self.vector_store.add_documents(docs)
            logger.info(f"Total indexed: {len(docs)} documents")
        else:
            logger.warning("No documents found in knowledge graph to index.")

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
        """Combine and deduplicate results with priority to graph matches."""
        seen = set()
        combined = []

        for res in graph_results:
            identifier = res.get("id") or res.get("name") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 1.0
                combined.append(res)

        for res in vector_results:
            identifier = res.get("id") or res.get("name") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 0.7
                combined.append(res)

        return sorted(combined, key=lambda x: x.get("score", 0), reverse=True)
