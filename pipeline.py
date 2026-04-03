"""
SatSage — Automation Pipeline
One-click: scrape → process → graph → train → reindex
Writes step-by-step progress to pipeline_status.json (polled by the API).

Usage:
    python pipeline.py                    # run all steps
    python pipeline.py --from-step 4     # resume from a specific step
    python pipeline.py --skip-train      # skip slow BERT training
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
STATUS_FILE = BASE / "pipeline_status.json"

STEPS = [
    {
        "id": 1,
        "name": "Scrape MOSDAC Data",
        "desc": "Crawl MOSDAC portal, extract PDFs and web content",
        "cmd": [sys.executable, "main.py"],
        "cwd": str(BASE / "data_collection"),
        "timeout": 600,
    },
    {
        "id": 2,
        "name": "Process & Clean Text",
        "desc": "Normalize text, detect language, enrich metadata",
        "cmd": [sys.executable, "-m", "data_processing.main"],
        "cwd": str(BASE),
        "timeout": 300,
    },
    {
        "id": 3,
        "name": "Build Knowledge Graph",
        "desc": "Extract entities + relationships, populate Neo4j",
        "cmd": [sys.executable, "-m", "knowledge_graph_construction.graph_builder"],
        "cwd": str(BASE),
        "timeout": 600,
    },
    {
        "id": 4,
        "name": "Generate Training Data",
        "desc": "Query Neo4j to create positive/negative training examples",
        "cmd": [sys.executable, "-m", "knowledge_graph_construction.training_data"],
        "cwd": str(BASE),
        "timeout": 180,
    },
    {
        "id": 5,
        "name": "Train Relationship Classifier",
        "desc": "Fine-tune BERT on entity-relationship pairs (slow — ~10-30 min)",
        "cmd": [sys.executable, "train_classifier.py"],
        "cwd": str(BASE / "knowledge_graph_construction"),
        "timeout": 3600,
    },
    {
        "id": 6,
        "name": "Rebuild & Clean Graph",
        "desc": "Re-validate relationships with trained classifier, remove noise",
        "cmd": [sys.executable, "rebuild_graph.py", "--execute"],
        "cwd": str(BASE / "knowledge_graph_construction"),
        "timeout": 600,
    },
    {
        "id": 7,
        "name": "Reindex FAISS Embeddings",
        "desc": "Re-embed all documents and rebuild the vector search index",
        "cmd": [
            sys.executable, "-c",
            "import sys; sys.path.insert(0, '.'); "
            "from rag_pipeline.retriever import HybridRetriever; "
            "r = HybridRetriever(); r.index_documents(); "
            "print('Reindex complete:', len(r.documents), 'documents indexed')",
        ],
        "cwd": str(BASE),
        "timeout": 300,
    },
]


def _now() -> str:
    return datetime.datetime.now().isoformat()


def _write_status(status: dict):
    STATUS_FILE.write_text(json.dumps(status, indent=2), encoding="utf-8")


def _make_initial_status(skip_ids: set) -> dict:
    return {
        "running": True,
        "started_at": _now(),
        "finished_at": None,
        "error": None,
        "steps": [
            {
                "id": s["id"],
                "name": s["name"],
                "desc": s["desc"],
                "status": "skipped" if s["id"] in skip_ids else "pending",
                "started_at": None,
                "finished_at": None,
                "log": "Skipped by user" if s["id"] in skip_ids else "",
            }
            for s in STEPS
        ],
    }


def run_pipeline(from_step: int = 1, skip_train: bool = False):
    skip_ids = {5} if skip_train else set()
    skip_ids |= {s["id"] for s in STEPS if s["id"] < from_step}

    status = _make_initial_status(skip_ids)
    _write_status(status)
    print(f"[Pipeline] Started — {len(STEPS) - len(skip_ids)} steps to run")

    for i, step in enumerate(STEPS):
        if step["id"] in skip_ids:
            print(f"[Step {step['id']}/{len(STEPS)}] {step['name']} — SKIPPED")
            continue

        step_status = status["steps"][i]
        step_status["status"] = "running"
        step_status["started_at"] = _now()
        _write_status(status)
        print(f"\n[Step {step['id']}/{len(STEPS)}] {step['name']} ...")

        try:
            result = subprocess.run(
                step["cmd"],
                cwd=step["cwd"],
                capture_output=True,
                text=True,
                timeout=step["timeout"],
                encoding="utf-8",
                errors="replace",
            )

            # Collect last 2000 chars of stdout + last 1000 of stderr
            log_parts = []
            if result.stdout.strip():
                tail = result.stdout.strip()[-2000:]
                log_parts.append(tail)
            if result.stderr.strip():
                tail = result.stderr.strip()[-1000:]
                log_parts.append("--- stderr ---\n" + tail)

            step_status["log"] = "\n".join(log_parts) if log_parts else "(no output)"

            if result.returncode == 0:
                step_status["status"] = "done"
                print(f"  OK")
            else:
                step_status["status"] = "error"
                step_status["log"] += f"\n--- exit code {result.returncode} ---"
                print(f"  ERROR (exit {result.returncode})")

        except subprocess.TimeoutExpired:
            step_status["status"] = "error"
            step_status["log"] = f"Timed out after {step['timeout']}s"
            print(f"  TIMEOUT after {step['timeout']}s")

        except Exception as exc:
            step_status["status"] = "error"
            step_status["log"] = str(exc)
            print(f"  EXCEPTION: {exc}")

        step_status["finished_at"] = _now()
        _write_status(status)

    status["running"] = False
    status["finished_at"] = _now()
    _write_status(status)

    done = sum(1 for s in status["steps"] if s["status"] == "done")
    errors = sum(1 for s in status["steps"] if s["status"] == "error")
    skipped = sum(1 for s in status["steps"] if s["status"] == "skipped")
    print(f"\n[Pipeline] Finished — {done} done, {errors} errors, {skipped} skipped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SatSage automation pipeline")
    parser.add_argument("--from-step", type=int, default=1, metavar="N",
                        help="Resume from step N (1-7)")
    parser.add_argument("--skip-train", action="store_true",
                        help="Skip BERT training (step 5) — useful for quick reindexing")
    args = parser.parse_args()
    run_pipeline(from_step=args.from_step, skip_train=args.skip_train)
