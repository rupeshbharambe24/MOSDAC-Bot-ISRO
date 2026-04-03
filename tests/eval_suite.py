"""
MOSDAC Help Bot — Evaluation Suite
====================================
Evaluates four pipeline components without requiring the full ML stack:

  1. Entity Extraction   — satellite / parameter / region detection
  2. Query Expansion     — synonym injection
  3. Retrieval Quality   — keyword precision against live /query API
  4. Response Quality    — completeness / hallucination guard

Run modes:
  python tests/eval_suite.py                  # full suite (needs API on port 8001)
  python tests/eval_suite.py --offline        # skip live API tests
  python tests/eval_suite.py --api-url URL    # custom API base URL

Results saved to eval_results.json (consumed by the admin dashboard).
"""

import sys
import json
import re
import time
import argparse
import datetime
import requests
from pathlib import Path
from typing import List, Dict

RESULTS_PATH = Path(__file__).parent.parent / "eval_results.json"

# ════════════════════════════════════════════════════════════════════════════
# INLINE ENTITY / EXPANSION LOGIC (mirrors retriever.py — no torch needed)
# ════════════════════════════════════════════════════════════════════════════

SATELLITE_NAMES = [
    "INSAT-3D", "INSAT-3DR", "INSAT-3A", "INSAT",
    "SCATSAT-1", "SCATSAT", "Oceansat-2", "Oceansat",
    "Megha-Tropiques", "SARAL", "Kalpana-1", "Kalpana",
]

PARAMETERS = [
    "SST", "sea surface temperature", "rainfall", "wind",
    "humidity", "TPW", "total precipitable water",
    "OLR", "outgoing longwave radiation", "cyclone",
    "temperature", "cloud", "snow", "ice", "chlorophyll",
]

REGIONS = [
    "India", "Bay of Bengal", "Arabian Sea", "Himalayas",
    "Indian Ocean", "Kerala", "Gujarat",
]

EXPANSIONS = {
    "sst": ["sea surface temperature", "ocean temperature", "thermal infrared"],
    "tpw": ["total precipitable water", "water vapor", "humidity"],
    "olr": ["outgoing longwave radiation", "thermal radiation", "earth energy"],
    "qpe": ["quantitative precipitation estimation", "rainfall"],
    "mosdac": ["MOSDAC satellite data meteorological oceanographic archival centre ISRO"],
    "india": ["Indian region", "South Asia", "Indian Ocean"],
    "cyclone": ["tropical cyclone", "hurricane", "storm", "weather"],
    "wind": ["wind speed", "wind vectors", "ocean wind", "scatterometer"],
    "rain": ["rainfall", "precipitation", "monsoon"],
    "oceansat": ["ocean color monitor", "ocean observation", "chlorophyll"],
    "altimetry": ["sea surface height", "wave height", "altika", "saral"],
    "register": ["signup", "registration", "account", "access data"],
    "instrument": ["payload", "sensor", "imager", "sounder"],
}


def extract_entity(text: str, candidates: List[str]) -> str:
    text_lower = text.lower()
    for candidate in candidates:
        if re.search(r"\b" + re.escape(candidate.lower()) + r"\b", text_lower):
            return candidate
    return ""


def expand_query(query: str) -> str:
    expanded = query.lower()
    for term, synonyms in EXPANSIONS.items():
        if term in expanded:
            expanded += " " + " ".join(synonyms)
    return expanded


# ════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ════════════════════════════════════════════════════════════════════════════

ENTITY_TESTS = [
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

EXPANSION_TESTS = [
    {"query": "sst analysis",        "must_contain": ["sea surface temperature"]},
    {"query": "tpw estimation",      "must_contain": ["total precipitable water", "water vapor"]},
    {"query": "olr measurement",     "must_contain": ["outgoing longwave radiation"]},
    {"query": "mosdac portal data",  "must_contain": ["MOSDAC"]},
    {"query": "cyclone tracking",    "must_contain": ["tropical cyclone"]},
    {"query": "wind vectors",        "must_contain": ["wind speed"]},
    {"query": "rain rate qpe",       "must_contain": ["rainfall", "precipitation"]},
    {"query": "altimetry data",      "must_contain": ["sea surface height"]},
]

RETRIEVAL_TESTS = [
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

RESPONSE_QUALITY_TESTS = [
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

def eval_entity_extraction() -> Dict:
    results = []
    correct = 0
    for tc in ENTITY_TESTS:
        q = tc["query"]
        got_sat = extract_entity(q, SATELLITE_NAMES)
        got_par = extract_entity(q, PARAMETERS)
        got_reg = extract_entity(q, REGIONS)

        sat_ok = (not tc["satellite"]) or (tc["satellite"].lower() in got_sat.lower())
        par_ok = (not tc["param"])     or (tc["param"].lower() in got_par.lower())
        reg_ok = (not tc["region"])    or (tc["region"].lower() in got_reg.lower())

        passed = sat_ok and par_ok and reg_ok
        if passed:
            correct += 1
        results.append({
            "query": q, "passed": passed,
            "expected": {"satellite": tc["satellite"], "param": tc["param"], "region": tc["region"]},
            "got":      {"satellite": got_sat,         "param": got_par,     "region": got_reg},
        })

    score = round(correct / len(ENTITY_TESTS) * 100, 1)
    return {"metric": "Entity Extraction", "score": score,
            "passed": correct, "total": len(ENTITY_TESTS), "details": results}


def eval_query_expansion() -> Dict:
    results = []
    correct = 0
    for tc in EXPANSION_TESTS:
        expanded = expand_query(tc["query"])
        hits    = [kw for kw in tc["must_contain"] if kw.lower() in expanded.lower()]
        missing = [kw for kw in tc["must_contain"] if kw.lower() not in expanded.lower()]
        passed  = len(hits) == len(tc["must_contain"])
        if passed:
            correct += 1
        results.append({"query": tc["query"], "passed": passed,
                         "expected": tc["must_contain"], "found": hits, "missing": missing})

    score = round(correct / len(EXPANSION_TESTS) * 100, 1)
    return {"metric": "Query Expansion", "score": score,
            "passed": correct, "total": len(EXPANSION_TESTS), "details": results}


def eval_retrieval_quality(api_url: str) -> Dict:
    results = []
    correct = 0
    for tc in RETRIEVAL_TESTS:
        try:
            resp = requests.post(f"{api_url}/query",
                                 json={"message": tc["query"], "history": []},
                                 timeout=30)
            if resp.status_code != 200:
                results.append({"query": tc["query"], "passed": False,
                                 "error": f"HTTP {resp.status_code}"})
                continue
            data = resp.json()
            combined = (data.get("response", "") + " " + " ".join(
                f"{s.get('satellite','')} {s.get('dataset','')}"
                for s in data.get("sources", [])
            )).lower()

            hits    = [kw for kw in tc["expected_keywords"] if kw.lower() in combined]
            missing = [kw for kw in tc["expected_keywords"] if kw.lower() not in combined]
            passed  = len(hits) >= max(1, len(tc["expected_keywords"]) // 2)
            if passed:
                correct += 1
            results.append({"query": tc["query"], "passed": passed,
                             "expected_keywords": tc["expected_keywords"],
                             "found": hits, "missing": missing})
        except requests.exceptions.ConnectionError:
            results.append({"query": tc["query"], "passed": False,
                             "error": "Connection refused — is the API running on port 8001?"})
        except Exception as e:
            results.append({"query": tc["query"], "passed": False, "error": str(e)})

    score = round(correct / len(RETRIEVAL_TESTS) * 100, 1)
    return {"metric": "Retrieval Quality", "score": score,
            "passed": correct, "total": len(RETRIEVAL_TESTS), "details": results}


def eval_response_quality(api_url: str) -> Dict:
    results = []
    correct = 0
    for tc in RESPONSE_QUALITY_TESTS:
        try:
            resp = requests.post(f"{api_url}/query",
                                 json={"message": tc["query"], "history": []},
                                 timeout=30)
            if resp.status_code != 200:
                results.append({"query": tc["query"], "passed": False,
                                 "error": f"HTTP {resp.status_code}"})
                continue
            response = resp.json().get("response", "")
            length_ok       = len(response) >= tc["min_length"]
            forbidden_found = [f for f in tc["forbidden"] if f.lower() in response.lower()]
            passed = length_ok and not forbidden_found and bool(response.strip())
            if passed:
                correct += 1
            results.append({
                "query": tc["query"], "passed": passed,
                "response_length": len(response), "min_length": tc["min_length"],
                "length_ok": length_ok, "forbidden_found": forbidden_found,
                "response_preview": response[:120] + "..." if len(response) > 120 else response,
            })
        except requests.exceptions.ConnectionError:
            results.append({"query": tc["query"], "passed": False,
                             "error": "Connection refused"})
        except Exception as e:
            results.append({"query": tc["query"], "passed": False, "error": str(e)})

    score = round(correct / len(RESPONSE_QUALITY_TESTS) * 100, 1)
    return {"metric": "Response Quality", "score": score,
            "passed": correct, "total": len(RESPONSE_QUALITY_TESTS), "details": results}


# ════════════════════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════════════════════

def run(api_url: str = "http://localhost:8001", offline: bool = False) -> Dict:
    print("=" * 60)
    print("MOSDAC Help Bot - Evaluation Suite")
    print("=" * 60)
    started = time.time()

    print("\n[1/4] Entity Extraction...")
    entity_result = eval_entity_extraction()
    _print_result(entity_result)

    print("\n[2/4] Query Expansion...")
    expansion_result = eval_query_expansion()
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
        print(f"\n[3/4] Retrieval Quality (API: {api_url})...")
        retrieval_result = eval_retrieval_quality(api_url)
        _print_result(retrieval_result)
        metrics.append(retrieval_result)

        print(f"\n[4/4] Response Quality (API: {api_url})...")
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
    if r.get("skipped"):
        print(f"  {r['metric']}: SKIPPED")
        return
    icon = "PASS" if r["score"] >= 70 else "FAIL"
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
