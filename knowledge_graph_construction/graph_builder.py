from py2neo import Graph, Node, Relationship
from pathlib import Path
import json
import logging
from tqdm import tqdm
from typing import Dict, Any, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoCoordinateParser:
    @staticmethod
    def parse_coordinate(coord_str: str) -> dict:
        """Parse various coordinate formats into decimal degrees"""
        try:
            # Handle degree-minute format: "12°34'N, 45°67'E"
            if "," in coord_str and "°" in coord_str:
                lat_part, lon_part = coord_str.split(",")
                return {
                    "lat": GeoCoordinateParser._parse_single_coord(lat_part.strip()),
                    "lon": GeoCoordinateParser._parse_single_coord(lon_part.strip()),
                    "type": "point"
                }
            
            # Handle range format: "10°N-15°N, 75°E-80°E"
            elif "-" in coord_str and "," in coord_str:
                lat_range, lon_range = coord_str.split(",")
                lat_min, lat_max = map(GeoCoordinateParser._parse_single_coord, lat_range.split("-"))
                lon_min, lon_max = map(GeoCoordinateParser._parse_single_coord, lon_range.split("-"))
                return {
                    "lat_min": lat_min,
                    "lat_max": lat_max,
                    "lon_min": lon_min,
                    "lon_max": lon_max,
                    "type": "bounding_box"
                }
            
            # Handle simple coordinate: "12.5°N"
            elif "°" in coord_str:
                return {
                    "value": GeoCoordinateParser._parse_single_coord(coord_str),
                    "type": "single_coord"
                }
            
            return None
            
        except Exception:
            return None

    @staticmethod
    def _parse_single_coord(coord: str) -> float:
        """Parse single coordinate like '12.5°N' into decimal degrees"""
        num_part, direction = coord.split("°")
        value = float(num_part)
        if direction in ["S", "W"]:
            value *= -1
        return value

class KnowledgeGraphBuilder:
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "mosdacisro"):
        """Initialize the graph builder with Neo4j connection details"""
        self.uri = uri
        self.user = user
        self.password = password
        self.graph = self._connect_to_neo4j()
        self.geolocator = Nominatim(user_agent="mosdac_geo_enricher")
        
    def _connect_to_neo4j(self) -> Graph:
        """Establish connection to Neo4j with error handling"""
        try:
            graph = Graph(
                self.uri,
                auth=(self.user, self.password),
                secure=False
            )
            # Test connection
            graph.run("RETURN 1")
            logger.info("Successfully connected to Neo4j")
            return graph
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise ConnectionError("Could not connect to Neo4j database")

    def clear_database(self) -> None:
        """Clear existing data in the graph"""
        try:
            self.graph.delete_all()
            logger.info("Cleared existing graph data")
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            raise

    def _get_coordinates(self, location_name: str) -> dict:
        """Convert location names to coordinates using geopy"""
        try:
            # Handle MOSDAC-specific patterns first
            if "Arabian Sea" in location_name:
                return {"lat": 14.5133, "lon": 65.0369, "type": "marine"}
            elif "Bay of Bengal" in location_name:
                return {"lat": 15.0000, "lon": 88.0000, "type": "marine"}
            
            # Handle coordinate patterns
            if re.search(r"\d+°[NSEW]", location_name):
                coords = GeoCoordinateParser.parse_coordinate(location_name)
                if coords:
                    return coords
            
            # Fall back to geopy for other locations
            location = self.geolocator.geocode(location_name, timeout=10)
            if location:
                return {"lat": location.latitude, "lon": location.longitude}
            return None
            
        except GeocoderTimedOut:
            time.sleep(1)
            return self._get_coordinates(location_name)
        except Exception:
            return None

    def _ensure_label_consistency(self, entity: Dict) -> str:
        """Ensure MOSDAC entities get proper labels"""
        text = entity["text"]
        label = entity["label"]
        
        # Convert ORG to SATELLITE when appropriate
        if label == "ORG" and any(sat in text for sat in ["INSAT", "SCATSAT", "Oceansat"]):
            return "SATELLITE"
        
        # Convert PRODUCT to DATA_PRODUCT for known products
        if label == "PRODUCT" and any(prod in text for prod in ["Temperature", "Wind", "Rain"]):
            return "DATA_PRODUCT"
            
        return label

    def _create_or_get_node(self, label: str, properties: Dict[str, Any]) -> Node:
        """Create node or return existing one with geospatial data"""
        # Ensure label consistency
        label = self._ensure_label_consistency({"text": properties["name"], "label": label})
        
        # Add geospatial data for regions
        if label == "REGION":
            coords = self._get_coordinates(properties["name"])
            if coords:
                properties.update(coords)
                logger.debug(f"Added coordinates to REGION node: {properties['name']}")
        
        primary_key = "name"
        node = self.graph.nodes.match(label, **{primary_key: properties[primary_key]}).first()
        
        if not node:
            node = Node(label, **properties)
            self.graph.create(node)
            logger.debug(f"Created new {label} node: {properties[primary_key]}")
        else:
            logger.debug(f"Found existing {label} node: {properties[primary_key]}")
            
        return node

    def _create_relationship(self, node1: Node, rel_type: str, node2: Node, 
                           properties: Optional[Dict] = None) -> None:
        """Create relationship between nodes if it doesn't exist"""
        if properties is None:
            properties = {}
            
        # Check if relationship already exists
        rel_exists = self.graph.relationships.match(
            nodes=(node1, node2),
            r_type=rel_type
        ).exists()
        
        if not rel_exists:
            rel = Relationship(node1, rel_type, node2, **properties)
            self.graph.create(rel)
            logger.debug(f"Created relationship: {node1['name']} -[{rel_type}]-> {node2['name']}")
        else:
            logger.debug(f"Relationship already exists: {node1['name']} -[{rel_type}]-> {node2['name']}")

    def build_graph(self, entity_dir: Path, relation_dir: Path) -> None:
        """Build the knowledge graph from extracted data"""
        self.clear_database()
        node_map = {}
        
        logger.info("Starting graph construction...")
        
        # First pass: Create all nodes with consistent labeling
        logger.info("Creating nodes...")
        for entity_file in tqdm(list(entity_dir.rglob("*.json")), desc="Processing entity files"):
            try:
                with open(entity_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for entity in data["text_entities"] + data["metadata_entities"]:
                    # Ensure we have the correct label
                    final_label = self._ensure_label_consistency(entity)
                    node_key = f"{final_label}_{entity['text']}"
                    
                    if node_key not in node_map:
                        node = self._create_or_get_node(
                            label=final_label,
                            properties={
                                "name": entity["text"],
                                "source": data["source"],
                                "type": entity.get("label", ""),
                                "text": entity.get("text", "")
                            }
                        )
                        node_map[node_key] = node
                        
            except Exception as e:
                logger.warning(f"Error processing {entity_file}: {str(e)}")
                continue
        
        # Second pass: Create relationships
        logger.info("Creating relationships...")
        for rel_file in tqdm(list(relation_dir.rglob("*.json")), desc="Processing relation files"):
            try:
                with open(rel_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for rel in data["relations"]:
                    # Ensure consistent labels for relationship nodes
                    head_label = self._ensure_label_consistency({"text": rel["head"], "label": rel["head_type"]})
                    tail_label = self._ensure_label_consistency({"text": rel["tail"], "label": rel["tail_type"]})
                    
                    head_key = f"{head_label}_{rel['head']}"
                    tail_key = f"{tail_label}_{rel['tail']}"
                    
                    if head_key in node_map and tail_key in node_map:
                        self._create_relationship(
                            node1=node_map[head_key],
                            rel_type=rel["type"],
                            node2=node_map[tail_key],
                            properties={
                                "source": data["source"],
                                "evidence": rel.get("evidence", ""),
                                "confidence": rel.get("confidence", 1.0)
                            }
                        )
                        
            except Exception as e:
                logger.warning(f"Error processing {rel_file}: {str(e)}")
                continue
        
        logger.info(f"Graph construction complete. Created {len(node_map)} nodes.")
        self._add_graph_statistics()

    def _add_graph_statistics(self) -> None:
        """Add summary statistics to the graph"""
        try:
            stats = {
                "node_count": self.graph.run("MATCH (n) RETURN count(n) AS count").data()[0]["count"],
                "relation_count": self.graph.run("MATCH ()-[r]->() RETURN count(r) AS count").data()[0]["count"],
                "timestamp": str(datetime.datetime.now())
            }
            
            stats_node = Node("Statistics", **stats)
            self.graph.create(stats_node)
            logger.info(f"Added graph statistics: {stats}")
            
            # Add verification queries
            self._verify_graph_structure()
            
        except Exception as e:
            logger.error(f"Could not add statistics: {str(e)}")

    def _verify_graph_structure(self) -> None:
        """Run verification queries to ensure graph quality"""
        logger.info("Running graph verification...")
        
        # Existing verification queries
        satellites = self.graph.run("MATCH (s:SATELLITE) RETURN s.name LIMIT 10").data()
        logger.info(f"Sample SATELLITE nodes: {satellites}")
        
        regions = self.graph.run("""
            MATCH (r:REGION) 
            WHERE r.lat IS NOT NULL AND r.lon IS NOT NULL
            RETURN r.name, r.lat, r.lon 
            LIMIT 10
        """).data()
        logger.info(f"REGION nodes with coordinates: {regions}")
        
        provides_rels = self.graph.run("""
            MATCH (s:SATELLITE)-[r:PROVIDES]->(d:DATA_PRODUCT)
            RETURN s.name AS satellite, d.name AS product, r.evidence AS context
            LIMIT 10
        """).data()
        logger.info(f"PROVIDES relationships: {provides_rels}")

        # ===== ADD THESE NEW RELATIONSHIP ENHANCEMENTS =====
        logger.info("Enhancing parameter and region relationships...")
        
        try:
            # Add Sea Surface Temperature relationships
            self.graph.run("""
                MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
                WHERE d.name CONTAINS "SST" OR d.description CONTAINS "sea surface temperature"
                MERGE (p:PARAMETER {name: "Sea Surface Temperature"})
                MERGE (d)-[:MEASURES]->(p)
                RETURN count(p) AS relationships_created
            """)
            
            # Add Bay of Bengal region relationships
            self.graph.run("""
                MATCH (d:DATA_PRODUCT)
                WHERE d.name CONTAINS "Bay of Bengal" OR d.coverage CONTAINS "India"
                MERGE (r:REGION {name: "Bay of Bengal"})
                MERGE (d)-[:COVERS]->(r)
                RETURN count(r) AS regions_linked
            """)
            
            # Add common parameters
            self.graph.run("""
                UNWIND ["Wind Speed", "Rainfall", "Humidity", "Cyclone"] AS param
                MERGE (p:PARAMETER {name: param})
                WITH p
                MATCH (d:DATA_PRODUCT)
                WHERE d.name CONTAINS p.name OR d.description CONTAINS p.name
                MERGE (d)-[:MEASURES]->(p)
                RETURN count(p) AS parameters_linked
            """)
            
            logger.info("Completed relationship enhancements")
            
        except Exception as e:
            logger.error(f"Failed to enhance relationships: {str(e)}")

if __name__ == "__main__":
    try:
        builder = KnowledgeGraphBuilder()
        builder.clear_database()
        entity_dir = Path("entities")
        relation_dir = Path("relations")
        
        if not entity_dir.exists() or not relation_dir.exists():
            raise FileNotFoundError("Entity or relation directory not found")
        
        builder.build_graph(entity_dir, relation_dir)
        logger.info("Knowledge graph construction completed successfully!")
                # Additional manual enhancements
        builder.graph.run("""
            MATCH (s:SATELLITE)-[:PROVIDES]->(d:DATA_PRODUCT)
            WHERE s.name IN ["INSAT-3D", "INSAT-3DR"]
            MERGE (p:PARAMETER {name: "Humidity"})
            MERGE (d)-[:MEASURES]->(p)
        """)
        
        logger.info("Knowledge graph construction completed successfully!")
    except Exception as e:
        logger.error(f"Graph construction failed: {str(e)}")
        raise