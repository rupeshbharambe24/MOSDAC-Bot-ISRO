"""
MOSDAC Help Bot — Evaluation Suite
===================================
Evaluates four pipeline components:

  1. Entity Extraction   — satellite / parameter / region detection
  2. Query Expansion     — synonym injection
  3. Retrieval Quality   — keyword precision against live API
  4. Response Quality    — completeness / hallucination guard

Run modes:
  python tests/eval_suite.py                  # full suite (needs API running)
  python tests/eval_suite.py --offline        # skip live API tests
  python tests/eval_suite.py --api-url URL    # custom API base URL

Results saved to eval_results.json (consumed by the admin dashboard).
"""

import sys
import json
import time
import argparse
import datetime
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ── allow running from project root ─────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag_pipeline.retriever import HybridRetriever

RESULTS_PATH = Path(__file__).parent.parent / "eval_results.json"


# ════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ════════════════════════════════════════════════════════════════════════════

ENTITY_TESTS: List[Dict] = [
    # (query, expected_satellite, expected_param, expected_region)
    {"query": "Show me INSAT-3D temperature data",
     "satellite": "INSAT-3D", "param": "", "region": ""},
    {"query": "Sea surface temperature in the Bay of Bengal",
     "satellite": "", "param": "sea surface temperature", "region": "Bay of Bengal"},
    {"query": "Track cyclone using SCATSAT-1",
     "satellite": "SCATSAT-1", "param": "cyclone", "region": ""},
    {"query": "Rainfall data for Kerala",
     "satellite": "", "param": "rainfall", "region": "Kerala"},
    {"query": "Oceansat-2 chlorophyll measurement",
     "satellite": "Oceansat-2", "param": "chlorophyll", "region": ""},
    {"query": "Wind speed over the Arabian Sea",
     "satellite": "", "param": "wind", "region": "Arabian Sea"},
    {"query": "Humidity profile from Megha-Tropiques over India",
     "satellite": "Megha-Tropiques", "param": "humidity", "region": "India"},
    {"query": "Snow cover in the Himalayas",
     "satellite": "", "param": "snow", "region": ""},
    {"query": "OLR data from INSAT-3DR",
     "satellite": "INSAT-3DR", "param": "OLR", "region": ""},
    {"query": "Gujarat flooding rainfall data",
     "satellite": "", "param": "rainfall", "region": "Gujarat"},
]

EXPANSION_TESTS: List[Dict] = [
    {"query": "sst analysis",       "must_contain": ["sea surface temperature"]},
    {"query": "tpw estimation",     "must_contain": ["total precipitable water", "water vapor"]},
    {"query": "olr measurement",    "must_contain": ["outgoing longwave radiation"]},
    {"query": "mosdac portal data", "must_contain": ["MOSDAC"]},
    {"query": "cyclone tracking",   "must_contain": ["tropical cyclone"]},
    {"query": "wind vectors",       "must_contain": ["wind speed"]},
    {"query": "rain rate qpe",      "must_contain": ["rainfall", "precipitation"]},
    {"query": "altimetry data",     "must_contain": ["sea surface height"]},
]

RETRIEVAL_TESTS: List[Dict] = [
    {"query": "What data does INSAT-3D provide?",
     "expected_keywords": ["INSAT-3D", "temperature", "data"]},
    {"query": "Sea surface temperature products",
     "expected_keywords": ["temperature", "SST", "sea"]},
    {"query": "SCATSAT-1 wind data",
     "expected_keywords": ["SCATSAT", "wind"]},
    {"query": "Which satellites are available on MOSDAC?",
     "expected_keywords": ["satellite", "INSAT", "MOSDAC"]},
    {"query": "Bay of Bengal cyclone monitoring",
     "expected_keywords": ["cyclone", "Bay of Bengal"]},
    {"query": "Oceansat chlorophyll ocean color",
     "expected_keywords": ["chlorophyll", "ocean", "Oceansat"]},
    {"query": "What is MOSDAC?",
     "expected_keywords": ["MOSDAC", "satellite", "data"]},
    {"query": "Rainfall estimation INSAT",
     "expected_keywords": ["rainfall", "INSAT"]},
]

RESPONSE_QUALITY_TESTS: List[Dict] = [
    {"query": "What satellites are on MOSDAC?",
     "min_length": 80, "forbidden": ["I don't know", "cannot answer"]},
    {"query": "How do I access sea surface temperature data?",
     "min_length": 60, "forbidden": ["LLM not configured"]},
    {"query": "Tell me about INSAT-3D instruments",
     "min_length": 80, "forbidden": ["error", "failed"]},
    {"query": "What is the coverage area of SCATSAT-1?",
     "min_length": 50, "forbidden": ["LLM not configured", "cannot answer"]},
]


# ════════════════════════════════════════════════════════════════════════════
# EVALUATORS
# ════════════════════════════════════════════════════════════════════════════

def eval_entity_extraction(retriever: HybridRetriever) -> Dict:
    """Test _extract_entity against known satellite/param/region queries."""
    results = []
    correct = 0

    for tc in ENTITY_TESTS:
        q = tc["query"]
        exp_sat = tc["satellite"]
        exp_par = tc["param"]
        exp_reg = tc["region"]

        got_sat = retriever._extract_entity(q, retriever.satellite_names)
        got_par = retriever._extract_entity(q, retriever.parameters)
        got_reg = retriever._extract_entity(q, retriever.regions)

        sat_ok = (not exp_sat) or (exp_sat.lower() in got_sat.lower())
        par_ok = (not exp_par) or (exp_par.lower() in got_par.lower())
        reg_ok = (not exp_reg) or (exp_reg.lower() in got_reg.lower())

        passed = sat_ok and par_ok and reg_ok
        if passed:
            correct += 1

        results.append({
            "query": q,
            "passed": passed,
            "expected": {"satellite": exp_sat, "param": exp_par, "region": exp_reg},
            "got":      {"satellite": got_sat,  "param": got_par,  "region": got_reg},
        })

    score = round(correct / len(ENTITY_TESTS) * 100, 1)
    return {
        "metric": "Entity Extraction",
        "score": score,
        "passed": correct,
        "total": len(ENTITY_TESTS),
        "details": results,
    }


def eval_query_expansion(retriever: HybridRetriever) -> Dict:
    """Test _expand_query for expected synonym injection."""
    results = []
    correct = 0

    for tc in EXPANSION_TESTS:
        expanded = retriever._expand_query(tc["query"])
        hits = [kw for kw in tc["must_contain"] if kw.lower() in expanded.lower()]
        passed = len(hits) == len(tc["must_contain"])
        if passed:
            correct += 1
        results.append({
            "query": tc["query"],
            "passed": passed,
            "expected": tc["must_contain"],
            "found": hits,
            "missing": [k for k in tc["must_contain"] if k not in hits],
        })

    score = round(correct / len(EXPANSION_TESTS) * 100, 1)
    return {
        "metric": "Query Expansion",
        "score": score,
        "passed": correct,
        "total": len(EXPANSION_TESTS),
        "details": results,
    }


def eval_retrieval_quality(api_url: str) -> Dict:
    """
    Call /query endpoint and check that retrieved context (returned as sources
    or visible in response text) contains expected keywords.
    """
    results = []
    correct = 0

    for tc in RETRIEVAL_TESTS:
        try:
            resp = requests.post(
                f"{api_url}/query",
                json={"message": tc["query"], "history": []},
                timeout=30,
            )
            if resp.status_code != 200:
                results.append({"query": tc["query"], "passed": False,
                                 "error": f"HTTP {resp.status_code}"})
                continue

            data = resp.json()
            # Check response text + source satellite/dataset fields
            response_text = data.get("response", "").lower()
            sources_text = " ".join(
                f"{s.get('satellite','')} {s.get('dataset','')}"
                for s in data.get("sources", [])
            ).lower()
            combined = response_text + " " + sources_text

            hits = [kw for kw in tc["expected_keywords"]
                    if kw.lower() in combined]
            # Pass if at least half the expected keywords appear
            threshold = max(1, len(tc["expected_keywords"]) // 2)
            passed = len(hits) >= threshold
            if passed:
                correct += 1

            results.append({
                "query": tc["query"],
                "passed": passed,
                "expected_keywords": tc["expected_keywords"],
                "found": hits,
                "missing": [k for k in tc["expected_keywords"] if k.lower() not in combined],
            })
        except requests.exceptions.ConnectionError:
            results.append({"query": tc["query"], "passed": False,
                             "error": "Connection refused — is the API running?"})
        except Exception as e:
            results.append({"query": tc["query"], "passed": False, "error": str(e)})

    score = round(correct / len(RETRIEVAL_TESTS) * 100, 1)
    return {
        "metric": "Retrieval Quality",
        "score": score,
        "passed": correct,
        "total": len(RETRIEVAL_TESTS),
        "details": results,
    }


def eval_response_quality(api_url: str) -> Dict:
    """
    Call /query and check response length, absence of error strings,
    and general completeness.
    """
    results = []
    correct = 0

    for tc in RESPONSE_QUALITY_TESTS:
        try:
            resp = requests.post(
                f"{api_url}/query",
                json={"message": tc["query"], "history": []},
                timeout=30,
            )
            if resp.status_code != 200:
                results.append({"query": tc["query"], "passed": False,
                                 "error": f"HTTP {resp.status_code}"})
                continue

            response = resp.json().get("response", "")
            length_ok = len(response) >= tc["min_length"]
            forbidden_found = [f for f in tc["forbidden"]
                               if f.lower() in response.lower()]
            not_empty = bool(response.strip())
            passed = length_ok and not forbidden_found and not_empty
            if passed:
                correct += 1

            results.append({
                "query": tc["query"],
                "passed": passed,
                "response_length": len(response),
                "min_length": tc["min_length"],
                "length_ok": length_ok,
                "forbidden_found": forbidden_found,
                "response_preview": response[:120] + "..." if len(response) > 120 else response,
            })
        except requests.exceptions.ConnectionError:
            results.append({"query": tc["query"], "passed": False,
                             "error": "Connection refused"})
        except Exception as e:
            results.append({"query": tc["query"], "passed": False, "error": str(e)})

    score = round(correct / len(RESPONSE_QUALITY_TESTS) * 100, 1)
    return {
        "metric": "Response Quality",
        "score": score,
        "passed": correct,
        "total": len(RESPONSE_QUALITY_TESTS),
        "details": results,
    }


# ════════════════════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════════════════════

def run(api_url: str = "http://localhost:8001", offline: bool = False) -> Dict:
    print("=" * 60)
    print("MOSDAC Help Bot — Evaluation Suite")
    print("=" * 60)
    started = time.time()

    # Initialise retriever for offline tests (no Neo4j required — just uses
    # the entity/expansion methods which are pure Python).
    print("\n[1/4] Entity Extraction …")
    retriever = HybridRetriever()
    entity_result = eval_entity_extraction(retriever)
    _print_result(entity_result)

    print("\n[2/4] Query Expansion …")
    expansion_result = eval_query_expansion(retriever)
    _print_result(expansion_result)

    metrics = [entity_result, expansion_result]

    if offline:
        print("\n[3/4] Retrieval Quality — SKIPPED (--offline)")
        print("[4/4] Response Quality  — SKIPPED (--offline)")
        metrics += [
            {"metric": "Retrieval Quality", "score": None, "passed": 0,
             "total": len(RETRIEVAL_TESTS), "skipped": True, "details": []},
            {"metric": "Response Quality",  "score": None, "passed": 0,
             "total": len(RESPONSE_QUALITY_TESTS), "skipped": True, "details": []},
        ]
    else:
        print(f"\n[3/4] Retrieval Quality (API: {api_url}) …")
        retrieval_result = eval_retrieval_quality(api_url)
        _print_result(retrieval_result)
        metrics.append(retrieval_result)

        print(f"\n[4/4] Response Quality (API: {api_url}) …")
        quality_result = eval_response_quality(api_url)
        _print_result(quality_result)
        metrics.append(quality_result)

    elapsed = round(time.time() - started, 1)
    live_scores = [m["score"] for m in metrics if m.get("score") is not None]
    overall = round(sum(live_scores) / len(live_scores), 1) if live_scores else None

    output = {
        "timestamp": datetime.datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "overall_score": overall,
        "offline": offline,
        "metrics": metrics,
    }

    RESULTS_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"Overall score : {overall}%")
    print(f"Elapsed       : {elapsed}s")
    print(f"Results saved : {RESULTS_PATH}")
    print("=" * 60)
    return output


def _print_result(r: Dict):
    skipped = r.get("skipped", False)
    if skipped:
        print(f"  {r['metric']}: SKIPPED")
        return
    icon = "✓" if r["score"] >= 70 else "✗"
    print(f"  {icon} {r['metric']}: {r['score']}%  ({r['passed']}/{r['total']} passed)")
    for d in r.get("details", []):
        status = "  PASS" if d.get("passed") else "  FAIL"
        err = f" [{d['error']}]" if "error" in d else ""
        print(f"    {status}  {d['query'][:70]}{err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MOSDAC eval suite")
    parser.add_argument("--offline", action="store_true",
                        help="Skip live API tests (entity/expansion only)")
    parser.add_argument("--api-url", default="http://localhost:8001",
                        help="Base URL of the running API server")
    args = parser.parse_args()
    run(api_url=args.api_url, offline=args.offline)
