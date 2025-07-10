from neo4j import GraphDatabase
from rag_pipeline.config import Config
from typing import List, Dict, Any

class GraphConnector:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=Config.NEO4J_AUTH,
            encrypted=False
        )

    def get_data_by_satellite_param(self, satellite: str, parameter: str) -> List[Dict[str, Any]]:
        """Get data products by satellite and parameter"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:SATELLITE {name: $satellite})-[:PROVIDES]->(d:DATA_PRODUCT),
                      (s)-[:HAS_INSTRUMENT]->(i:INSTRUMENT)-[:MEASURES]->(p:PARAMETER)
                WHERE p.name CONTAINS $parameter OR $parameter CONTAINS p.name
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    instrument: i.name,
                    parameter: p.name,
                    type: 'data_product'
                } AS result
                LIMIT 10
                """, satellite=satellite, parameter=parameter)
            return [record["result"] for record in result]

    def get_data_by_region_param(self, region: str, parameter: str) -> List[Dict[str, Any]]:
        """Get data products by region and parameter"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:REGION)<-[:COVERS]-(d:DATA_PRODUCT)<-[:PROVIDES]-(s:SATELLITE),
                      (s)-[:HAS_INSTRUMENT]->(i:INSTRUMENT)-[:MEASURES]->(p:PARAMETER)
                WHERE (r.name CONTAINS $region OR $region CONTAINS r.name)
                  AND (p.name CONTAINS $parameter OR $parameter CONTAINS p.name)
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    instrument: i.name,
                    parameter: p.name,
                    region: r.name,
                    type: 'data_product'
                } AS result
                LIMIT 10
                """, region=region, parameter=parameter)
            return [record["result"] for record in result]

    def get_data_by_parameter(self, parameter: str) -> List[Dict[str, Any]]:
        """Get data products by parameter only"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:DATA_PRODUCT)<-[:PROVIDES]-(s:SATELLITE),
                      (s)-[:HAS_INSTRUMENT]->(i:INSTRUMENT)-[:MEASURES]->(p:PARAMETER)
                WHERE p.name CONTAINS $parameter OR $parameter CONTAINS p.name
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    instrument: i.name,
                    parameter: p.name,
                    type: 'data_product'
                } AS result
                ORDER BY d.name
                LIMIT 10
                """, parameter=parameter)
            return [record["result"] for record in result]

    def close(self):
        self.driver.close()