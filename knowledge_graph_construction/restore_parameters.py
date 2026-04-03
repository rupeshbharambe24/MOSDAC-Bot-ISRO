"""
Restore PARAMETER nodes and create proper INSTRUMENT -[:MEASURES]-> PARAMETER
relationships. Run once after rebuild_graph.py --execute.
"""

import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv

load_dotenv()

PARAMETERS = [
    "Sea Surface Temperature",
    "Wind Speed",
    "Rainfall",
    "Humidity",
    "Outgoing Longwave Radiation",
    "Total Precipitable Water",
    "Significant Wave Height",
    "Ocean Color",
    "Chlorophyll Concentration",
    "Sea Surface Height",
    "MJO",
    "Cyclone",
    "Soil Moisture",
]

# Known real instrument→parameter mappings from MOSDAC domain knowledge
INSTRUMENT_MEASURES = [
    ("SAPHIR",       "Humidity"),
    ("SAPHIR",       "Rainfall"),
    ("VHRR",         "Sea Surface Temperature"),
    ("VHRR",         "Wind Speed"),
    ("Imager",       "Sea Surface Temperature"),
    ("Imager",       "Outgoing Longwave Radiation"),
    ("Sounder",      "Humidity"),
    ("Sounder",      "Total Precipitable Water"),
    ("MADRAS",       "Rainfall"),
    ("ScaRaB",       "Outgoing Longwave Radiation"),
    ("AltiKa",       "Sea Surface Height"),
    ("AltiKa",       "Significant Wave Height"),
    ("OCM",          "Ocean Color"),
    ("OCM",          "Chlorophyll Concentration"),
    ("SSTM",         "Sea Surface Temperature"),
    ("Scatterometer","Wind Speed"),
    ("Scatterometer","Soil Moisture"),
    ("DWR",          "Rainfall"),
]

def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password), encrypted=False)

    with driver.session() as session:
        # 1. Create PARAMETER nodes
        print("Creating PARAMETER nodes...")
        for param in PARAMETERS:
            session.run(
                "MERGE (p:PARAMETER {name: $name})",
                name=param
            )
        print(f"  Created/merged {len(PARAMETERS)} parameters")

        # 2. Get existing INSTRUMENT nodes
        result = session.run("MATCH (i:INSTRUMENT) RETURN i.name AS name")
        instruments_in_graph = {r["name"] for r in result}
        print(f"  Instruments in graph: {instruments_in_graph}")

        # 3. Create INSTRUMENT -[:MEASURES]-> PARAMETER edges for known instruments
        created = 0
        skipped = 0
        for instrument, parameter in INSTRUMENT_MEASURES:
            if instrument in instruments_in_graph:
                session.run(
                    """
                    MATCH (i:INSTRUMENT {name: $instrument})
                    MERGE (p:PARAMETER {name: $parameter})
                    MERGE (i)-[:MEASURES]->(p)
                    """,
                    instrument=instrument, parameter=parameter
                )
                created += 1
            else:
                # Create the INSTRUMENT node if it's a real instrument
                if instrument in {"SAPHIR", "VHRR", "Imager", "Sounder", "MADRAS",
                                   "ScaRaB", "AltiKa", "OCM", "SSTM", "Scatterometer", "DWR"}:
                    session.run(
                        """
                        MERGE (i:INSTRUMENT {name: $instrument})
                        MERGE (p:PARAMETER {name: $parameter})
                        MERGE (i)-[:MEASURES]->(p)
                        """,
                        instrument=instrument, parameter=parameter
                    )
                    created += 1
                else:
                    skipped += 1

        print(f"  Created {created} MEASURES relationships, skipped {skipped}")

        # 4. Report final state
        result = session.run("MATCH (p:PARAMETER) RETURN p.name AS name ORDER BY p.name")
        params = [r["name"] for r in result]
        print(f"\nFinal PARAMETER nodes ({len(params)}): {params}")

        result = session.run("MATCH ()-[r:MEASURES]->() RETURN count(r) AS c")
        measures_count = result.single()["c"]
        print(f"Final MEASURES relationships: {measures_count}")

        result = session.run("MATCH (i:INSTRUMENT) RETURN count(i) AS c")
        instrument_count = result.single()["c"]
        print(f"Final INSTRUMENT nodes: {instrument_count}")

    driver.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
