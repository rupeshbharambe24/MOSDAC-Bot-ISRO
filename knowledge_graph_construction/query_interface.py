import os
from py2neo import Graph
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class MOSDACQueryEngine:
    def __init__(self):
        self.graph = Graph(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
        )

    def query_satellite_products(self, satellite_name: str) -> List[Dict]:
        """Get all data products provided by a satellite"""
        query = """
        MATCH (s:SATELLITE {name: $name})-[:PROVIDES]->(p:DATA_PRODUCT)
        RETURN p.name as product, p.source as source
        """
        return self.graph.run(query, name=satellite_name).data()

    def query_parameter_instruments(self, parameter: str) -> List[Dict]:
        """Get instruments that measure a specific parameter"""
        query = """
        MATCH (p:PARAMETER {name: $param})-[:MEASURED_BY]->(i:INSTRUMENT)
        RETURN i.name as instrument, i.source as source
        """
        return self.graph.run(query, param=parameter).data()

    def find_related_documents(self, entity_name: str) -> List[Dict]:
        """Find all documents mentioning a specific entity"""
        query = """
        MATCH (n {name: $name})
        RETURN DISTINCT n.source as source, labels(n)[0] as type
        """
        return self.graph.run(query, name=entity_name).data()

if __name__ == "__main__":
    engine = MOSDACQueryEngine()
    
    # Example queries
    print("INSAT-3D products:")
    print(engine.query_satellite_products("INSAT-3D"))
    
    print("\nInstruments measuring TPW:")
    print(engine.query_parameter_instruments("TPW"))