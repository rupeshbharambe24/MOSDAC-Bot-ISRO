"""
MOSDAC Knowledge Graph Rebuilder
Re-validates all relationships (PROVIDES, COVERS, MEASURES) using the retrained
classifier, removes invalid ones, cleans orphan nodes, and reports statistics.

Usage:
    python rebuild_graph.py                    # Dry run (report only, no deletions)
    python rebuild_graph.py --execute          # Actually delete invalid relationships + orphans
    python rebuild_graph.py --execute --model models/mosdac_relation_classifier
"""

import argparse
import os
import sys
import json
from datetime import datetime

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv

load_dotenv()


def connect_neo4j():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password), encrypted=False)
    with driver.session() as session:
        session.run("RETURN 1").single()
    print("Connected to Neo4j")
    return driver


def get_graph_stats(driver):
    """Get current graph statistics."""
    with driver.session() as session:
        stats = {}
        for label in ["SATELLITE", "DATA_PRODUCT", "REGION", "INSTRUMENT", "PARAMETER", "STATION"]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            stats[label] = result.single()["c"]
        for rel_type in ["PROVIDES", "COVERS", "MEASURES", "LOCATED_IN", "HAS"]:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c")
            stats[rel_type] = result.single()["c"]
    return stats


def classify_relationships(driver, model, tokenizer, device, rel_type="PROVIDES"):
    """Classify all relationships of a given type. Returns lists of valid and invalid."""
    valid = []
    invalid = []

    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (s)-[r:{rel_type}]->(d)
            WHERE s.name IS NOT NULL AND d.name IS NOT NULL
            RETURN s.name AS head, d.name AS tail, labels(s)[0] AS head_type,
                   labels(d)[0] AS tail_type, elementId(r) AS rel_id
            """
        )
        records = [dict(r) for r in result]

    if not records:
        print(f"  No {rel_type} relationships found")
        return valid, invalid

    # Classify in batches
    batch_size = 64
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        texts = [f"{r['head']} {rel_type.lower()} {r['tail']}" for r in batch]

        inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        predictions = outputs.logits.argmax(dim=-1).cpu().tolist()

        for rec, pred in zip(batch, predictions):
            entry = {
                "head": rec["head"],
                "head_type": rec["head_type"],
                "relation": rel_type,
                "tail": rec["tail"],
                "tail_type": rec["tail_type"],
                "rel_id": rec["rel_id"],
            }
            if pred == 1:
                valid.append(entry)
            else:
                invalid.append(entry)

    return valid, invalid


def delete_relationships(driver, invalid_rels):
    """Delete invalid relationships from Neo4j."""
    deleted = 0
    with driver.session() as session:
        for rel in invalid_rels:
            try:
                session.run(
                    "MATCH ()-[r]->() WHERE elementId(r) = $rel_id DELETE r",
                    rel_id=rel["rel_id"],
                )
                deleted += 1
            except Exception as e:
                print(f"  Error deleting {rel['head']} -> {rel['tail']}: {e}")
    return deleted


def find_orphan_nodes(driver):
    """Find nodes with no relationships at all."""
    orphans = {}
    with driver.session() as session:
        for label in ["DATA_PRODUCT", "REGION", "PARAMETER", "STATION"]:
            result = session.run(
                f"""
                MATCH (n:{label})
                WHERE NOT (n)--()
                RETURN n.name AS name, elementId(n) AS node_id
                """
            )
            records = [dict(r) for r in result]
            if records:
                orphans[label] = records
    return orphans


def delete_orphan_nodes(driver, orphans):
    """Delete orphan nodes."""
    deleted = 0
    with driver.session() as session:
        for label, nodes in orphans.items():
            for node in nodes:
                try:
                    session.run(
                        "MATCH (n) WHERE elementId(n) = $node_id DELETE n",
                        node_id=node["node_id"],
                    )
                    deleted += 1
                except Exception as e:
                    print(f"  Error deleting orphan {label}:{node['name']}: {e}")
    return deleted


def print_samples(items, rel_type, label, limit=15):
    """Print sample relationships."""
    if not items:
        return
    print(f"\n--- Sample {label} {rel_type} ({len(items)} total) ---")
    for rel in items[:limit]:
        print(f"  {rel['head']} ({rel['head_type']}) --{rel_type}--> {rel['tail']} ({rel['tail_type']})")
    if len(items) > limit:
        print(f"  ... and {len(items) - limit} more")


def main(args):
    print("=" * 60)
    print("MOSDAC Knowledge Graph - Full Cleanup")
    print("=" * 60)
    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"Mode: {mode}")
    print()

    # Load model
    if not os.path.exists(args.model):
        print(f"Model not found at {args.model}. Run train_classifier.py first.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading model from {args.model} (device: {device})")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model).to(device)
    model.eval()

    # Connect to Neo4j
    driver = connect_neo4j()

    # Before stats
    print("\n--- Graph Statistics (BEFORE) ---")
    before_stats = get_graph_stats(driver)
    for key, val in before_stats.items():
        print(f"  {key}: {val}")

    # ── Phase 1: Classify and clean relationships ──
    all_invalid = []
    report_data = {}

    for rel_type in ["PROVIDES", "COVERS", "MEASURES"]:
        count = before_stats.get(rel_type, 0)
        if count == 0:
            continue
        print(f"\nClassifying {rel_type} relationships ({count})...")
        valid, invalid = classify_relationships(driver, model, tokenizer, device, rel_type)
        print(f"  Valid: {len(valid)} | Invalid: {len(invalid)}")

        print_samples(invalid, rel_type, "INVALID (removing)", limit=10)
        print_samples(valid, rel_type, "VALID (keeping)", limit=5)

        report_data[rel_type] = {
            "valid": len(valid),
            "invalid": len(invalid),
            "invalid_samples": [{"head": r["head"], "tail": r["tail"]} for r in invalid[:30]],
            "valid_samples": [{"head": r["head"], "tail": r["tail"]} for r in valid[:30]],
        }

        if args.execute and invalid:
            deleted = delete_relationships(driver, invalid)
            print(f"  Deleted {deleted}/{len(invalid)} {rel_type} relationships")

        all_invalid.extend(invalid)

    # ── Phase 2: Heuristic cleanup — MEASURES from non-INSTRUMENT heads ──
    # MEASURES should only come from actual instruments (SAPHIR, VHRR, etc.)
    # The entity extractor mislabeled many instruments as DATA_PRODUCT, so
    # DATA_PRODUCT --MEASURES--> PARAMETER relationships are almost always wrong.
    print("\nApplying heuristic: removing MEASURES from DATA_PRODUCT nodes...")
    with driver.session() as session:
        result = session.run(
            """
            MATCH (d:DATA_PRODUCT)-[r:MEASURES]->(p:PARAMETER)
            RETURN count(r) AS c
            """
        )
        junk_measures = result.single()["c"]
        print(f"  DATA_PRODUCT -[:MEASURES]-> PARAMETER: {junk_measures} (removing)")
        if args.execute and junk_measures > 0:
            session.run(
                "MATCH (d:DATA_PRODUCT)-[r:MEASURES]->(p:PARAMETER) DELETE r"
            )
            print(f"  Deleted {junk_measures} invalid MEASURES relationships")

    # ── Phase 3: Clean orphan nodes ──
    print("\nFinding orphan nodes (no relationships)...")
    orphans = find_orphan_nodes(driver)
    total_orphans = sum(len(nodes) for nodes in orphans.values())
    for label, nodes in orphans.items():
        print(f"  {label}: {len(nodes)} orphans")
        for n in nodes[:5]:
            print(f"    - {n['name']}")
        if len(nodes) > 5:
            print(f"    ... and {len(nodes) - 5} more")

    if args.execute and total_orphans > 0:
        deleted = delete_orphan_nodes(driver, orphans)
        print(f"Deleted {deleted}/{total_orphans} orphan nodes")

    # After stats
    if args.execute:
        print("\n--- Graph Statistics (AFTER) ---")
        after_stats = get_graph_stats(driver)
        for key, val in after_stats.items():
            diff = val - before_stats.get(key, 0)
            diff_str = f" ({diff:+d})" if diff != 0 else ""
            print(f"  {key}: {val}{diff_str}")
    else:
        print(f"\nDry run complete. Would remove {len(all_invalid)} relationships + {total_orphans} orphan nodes.")
        print("Run with --execute to apply changes.")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "model": args.model,
        "before_stats": before_stats,
        "relationship_cleanup": report_data,
        "orphan_nodes": {
            label: [n["name"] for n in nodes[:20]]
            for label, nodes in orphans.items()
        },
        "total_invalid_relationships": len(all_invalid),
        "total_orphan_nodes": total_orphans,
    }
    report_path = f"rebuild_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {report_path}")

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild MOSDAC knowledge graph")
    parser.add_argument(
        "--model", default="models/mosdac_relation_classifier",
        help="Path to trained classifier model"
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually delete invalid relationships and orphan nodes (default is dry run)"
    )
    args = parser.parse_args()
    main(args)
