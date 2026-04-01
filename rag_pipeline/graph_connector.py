from neo4j import GraphDatabase
from rag_pipeline.config import Config
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GraphConnector:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=Config.NEO4J_AUTH,
            encrypted=False,
        )

    def get_data_by_satellite(self, satellite: str) -> List[Dict[str, Any]]:
        """Get data products provided by a satellite."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                WHERE s.name CONTAINS $satellite OR $satellite CONTAINS s.name
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    source: d.source,
                    type: 'data_product'
                } AS result
                LIMIT 10
            """, satellite=satellite)
            return [record["result"] for record in result]

    def get_data_by_satellite_param(self, satellite: str, parameter: str) -> List[Dict[str, Any]]:
        """Get data products by satellite, filtered by parameter name."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                WHERE (s.name CONTAINS $satellite OR $satellite CONTAINS s.name)
                  AND (d.name CONTAINS $parameter OR $parameter CONTAINS d.name)
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    source: d.source,
                    type: 'data_product'
                } AS result
                LIMIT 10
            """, satellite=satellite, parameter=parameter)
            return [record["result"] for record in result]

    def get_data_by_region_param(self, region: str, parameter: str) -> List[Dict[str, Any]]:
        """Get data products by region and parameter."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:REGION)<-[:COVERS]-(d:DATA_PRODUCT)<-[:PROVIDES]-(s:SATELLITE)
                WHERE (r.name CONTAINS $region OR $region CONTAINS r.name)
                  AND (d.name CONTAINS $parameter OR $parameter CONTAINS d.name)
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    region: r.name,
                    source: d.source,
                    type: 'data_product'
                } AS result
                LIMIT 10
            """, region=region, parameter=parameter)
            return [record["result"] for record in result]

    def get_data_by_parameter(self, parameter: str) -> List[Dict[str, Any]]:
        """Get data products matching a parameter/keyword."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                WHERE d.name CONTAINS $parameter OR $parameter CONTAINS d.name
                RETURN {
                    product: d.name,
                    satellite: s.name,
                    source: d.source,
                    type: 'data_product'
                } AS result
                ORDER BY d.name
                LIMIT 10
            """, parameter=parameter)
            return [record["result"] for record in result]

    def search_all(self, keyword: str) -> List[Dict[str, Any]]:
        """Broad search across all node types by name."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL AND (n.name CONTAINS $keyword OR $keyword CONTAINS n.name)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN {
                    name: n.name,
                    type: labels(n)[0],
                    source: n.source,
                    related: COLLECT(DISTINCT {name: m.name, type: labels(m)[0], rel: type(r)})[..5]
                } AS result
                LIMIT 10
            """, keyword=keyword)
            return [record["result"] for record in result]

    def close(self):
        self.driver.close()
