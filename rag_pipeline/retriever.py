from typing import List, Dict, Any
from rag_pipeline.graph_connector import GraphConnector
from rag_pipeline.vector_store import VectorStore
from rag_pipeline.config import Config
import re

class HybridRetriever:
    def __init__(self):
        self.graph = GraphConnector()
        self.vector_store = VectorStore()
        self.documents = []
        
        # Common terms in MOSDAC data
        self.satellite_names = ["INSAT", "SCATSAT", "Oceansat", "Megha-Tropiques"]
        self.parameters = ["SST", "sea surface temperature", "rainfall", "wind", "humidity"]
        self.regions = ["India", "Bay of Bengal", "Arabian Sea", "Himalayas"]

    def index_documents(self):
        """Improved document indexing with better text representation"""
        docs = []
        
        # Index satellites with enhanced descriptions
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

        # Index data products with more context
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

        self.documents = docs
        self.vector_store.add_documents(docs)

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        print(f"\n=== Received query: {query} ===")
        """Enhanced hybrid retrieval with better query understanding"""
        # Normalize query
        query_lower = query.lower()
        print("Searching vector store...")
        # Vector search with expanded query
        expanded_query = self._expand_query(query)
        vector_results = []
        print(f"Vector results: {vector_results}")
        vector_indices = self.vector_store.search(expanded_query)
        vector_results = [self.documents[idx] for idx in vector_indices if idx < len(self.documents)]
        print("Searching graph database...")
        # Graph search for precise matches
        graph_results = self._graph_search(query)
        print(f"Graph results: {graph_results}")
        
        # Combine and rank results
        combined = self._combine_results(vector_results, graph_results)
        return combined[:Config.TOP_K]

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms"""
        expansions = {
            "sst": ["sea surface temperature", "ocean temperature"],
            "india": ["Indian region", "South Asia"],
            "data": ["dataset", "product", "observation"]
        }
        
        expanded = query.lower()
        for term, synonyms in expansions.items():
            if term in expanded:
                expanded += " " + " ".join(synonyms)
        return expanded

    def _graph_search(self, query: str) -> List[Dict]:
        """Precise graph pattern matching"""
        results = []
        
        # Extract entities from query
        satellite = self._extract_entity(query, self.satellite_names)
        parameter = self._extract_entity(query, self.parameters)
        region = self._extract_entity(query, self.regions)
        
        # Case 1: Satellite + Parameter query
        if satellite and parameter:
            results.extend(self.graph.get_data_by_satellite_param(satellite, parameter))
            
        # Case 2: Region + Parameter query
        elif region and parameter:
            results.extend(self.graph.get_data_by_region_param(region, parameter))
            
        # Case 3: General parameter query
        elif parameter:
            results.extend(self.graph.get_data_by_parameter(parameter))
            
        return results

    def _extract_entity(self, text: str, candidates: List[str]) -> str:
        """Advanced entity extraction with fuzzy matching"""
        text_lower = text.lower()
        for candidate in candidates:
            if re.search(r'\b' + re.escape(candidate.lower()) + r'\b', text_lower):
                return candidate
        return ""

    def _combine_results(self, vector_results: List, graph_results: List) -> List:
        """Combine and deduplicate results with priority to graph matches"""
        seen = set()
        combined = []
        
        # Add graph results first (higher precision)
        for res in graph_results:
            identifier = res.get("id") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 1.0  # High confidence
                combined.append(res)
        
        # Add vector results
        for res in vector_results:
            identifier = res.get("id") or str(res)
            if identifier not in seen:
                seen.add(identifier)
                res["score"] = 0.7  # Lower confidence
                combined.append(res)
        
        # Sort by score descending
        return sorted(combined, key=lambda x: x.get("score", 0), reverse=True)