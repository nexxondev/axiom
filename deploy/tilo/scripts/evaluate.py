"""
AXIOM TILO Evaluation Script
Nexxon National | Unclassified

Automated capability demonstration for TILO sandbox evaluation.
Run this script to walk through every AXIOM capability
in sequence with pass/fail reporting.

Usage: python3 deploy/tilo/scripts/evaluate.py
"""

import asyncio
import httpx
import json
import sys
import time
import uuid
from datetime import datetime, timezone


BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
MISSION_ID = str(uuid.uuid4())

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


def header(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check(label: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {label}")
    if detail:
        print(f"         {detail}")
    return condition


results = []


def record(label: str, passed: bool):
    results.append((label, passed))
    return passed


async def run_evaluation():
    print()
    print("AXIOM TILO SANDBOX EVALUATION")
    print("Nexxon National | Unclassified")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mission ID: {MISSION_ID}")

    # ── MODULE 1: HEALTH CHECK ────────────────────────────
    header("M01 — SYSTEM HEALTH")
    try:
        r = httpx.get(f"{API}/health", timeout=5)
        data = r.json()
        record("Health endpoint responsive", check(
            "API responding", r.status_code == 200, f"Status: {r.status_code}"))
        record("Correct app name", check(
            "App name: AXIOM", data.get("app") == "AXIOM"))
        record("Classification present", check(
            "Classification declared", "classification" in data,
            f"Value: {data.get('classification')}"))
    except Exception as e:
        record("Health check", False)
        print(f"  {FAIL} Cannot reach server: {e}")
        print("  Ensure: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    # ── MODULE 2: AUTHENTICATION ──────────────────────────
    header("M02 — AUTHENTICATION + RBAC")
    sys.path.insert(0, ".")
    from app.core.security import create_access_token, Role

    token = create_access_token(subject="EVAL-COMMANDER", role=Role.COMMANDER)
    op_token = create_access_token(
        subject="EVAL-OPERATOR", role=Role.OPERATOR, mission_ids=[MISSION_ID])

    headers = {"Authorization": f"Bearer {token}"}
    op_headers = {"Authorization": f"Bearer {op_token}"}

    r = httpx.get(f"{API}/missions/", headers=headers, follow_redirects=True)
    record("JWT authentication", check(
        "Commander token accepted", r.status_code == 200))

    r = httpx.get(f"{API}/missions/", follow_redirects=True)
    record("Unauthenticated rejected", check(
        "Unauthenticated request rejected", r.status_code == 403))

    # ── MODULE 3: MISSION CRUD ────────────────────────────
    header("M03 — MISSION MANAGEMENT")
    r = httpx.post(f"{API}/missions/",
        headers=headers,
        json={"name": "EVAL-OP-NIGHTFALL",
              "mission_type": "direct_action",
              "description": "TILO evaluation mission"},
        follow_redirects=True)
    record("Mission creation", check(
        "Mission created", r.status_code == 201,
        f"ID: {r.json().get('id', 'N/A')[:8]}..."))

    # ── MODULE 4: AI REPLANNING ───────────────────────────
    header("M04 — AI REPLANNING ENGINE")
    start = time.perf_counter()
    r = httpx.post(f"{API}/ai/replan",
        headers=headers,
        json={"mission_id": MISSION_ID},
        follow_redirects=True, timeout=15)
    elapsed = (time.perf_counter() - start) * 1000
    data = r.json()
    record("Replan endpoint", check(
        "Replan triggered", r.status_code == 200 and data.get("replan_triggered")))
    record("COAs generated", check(
        f"COAs generated: {len(data.get('coas', []))}",
        len(data.get("coas", [])) >= 2))
    record("Recommendation present", check(
        "Recommendation provided", bool(data.get("recommended_coa")),
        f"Recommended: {data.get('recommended_coa', 'N/A')}"))
    record("Processing speed", check(
        f"Processing time: {elapsed:.1f}ms",
        elapsed < 5000, "Target: <5000ms"))

    # ── MODULE 5: GEOSPATIAL ──────────────────────────────
    header("M05 — GEOSPATIAL INTELLIGENCE")
    r = httpx.get(f"{API}/geo/mission/{MISSION_ID}/map",
        headers=headers, follow_redirects=True)
    data = r.json()
    record("Map package", check(
        "Map package served", r.status_code == 200))
    record("All 4 layers present", check(
        f"Layers: {list(data.get('layers', {}).keys())}",
        len(data.get("layers", {})) == 4))
    record("Threat overlays", check(
        f"Threats: {data.get('threat_count', 0)} active",
        data.get("threat_count", 0) > 0))
    record("Operational distance", check(
        f"Distance: {data.get('operational_distance', {}).get('total_km')}km",
        data.get("operational_distance", {}).get("total_km", 0) > 0))

    # ── MODULE 6: TARGET MANAGEMENT ──────────────────────
    header("M06 — TARGET MANAGEMENT + ROE")
    r = httpx.get(f"{API}/targets/prioritize?mission_id={MISSION_ID}",
        headers=headers, follow_redirects=True)
    data = r.json()
    record("Target prioritization", check(
        "Targets ranked", r.status_code == 200))
    record("ROE evaluation", check(
        f"Engageable: {data.get('engageable_count')} / Restricted: {data.get('restricted_count')}",
        data.get("restricted_count", 0) > 0,
        "ROE engine correctly restricting low-confidence targets"))

    # ── MODULE 7: DISPLAY ADAPTERS ────────────────────────
    header("M07 — DISPLAY ADAPTER SYSTEM")
    for ff, expected_size in [("tablet", "full"), ("hud", "minimal"), ("wrist", "micro")]:
        r = httpx.get(f"{API}/display/{ff}/mission/{MISSION_ID}",
            headers=headers, follow_redirects=True)
        data = r.json()
        record(f"{ff.upper()} adapter", check(
            f"{ff.upper()}: payload_size={data.get('payload_size')}",
            data.get("payload_size") == expected_size))

    # ── MODULE 8: ENCRYPTION ──────────────────────────────
    header("M08 — ENCRYPTION + COMMS")
    r = httpx.post(f"{API}/comms/encrypt/test",
        headers=headers,
        json={"mission_id": MISSION_ID,
              "plaintext": "TILO evaluation encryption test",
              "additional_data": "eval:tilo"},
        follow_redirects=True)
    data = r.json()
    record("Encryption roundtrip", check(
        "AES-256-GCM roundtrip verified",
        data.get("roundtrip_verified") == True))
    record("Signature verification", check(
        "HMAC-SHA256 signature verified",
        data.get("signature_verified") == True))
    record("FIPS compliance", check(
        "FIPS 140-2 patterns confirmed",
        data.get("fips_compliant") == True))
    record("Encryption speed", check(
        f"Encryption time: {data.get('processing_ms')}ms",
        data.get("processing_ms", 999) < 50))

    # ── MODULE 9: TACTICAL UI ────────────────────────────
    header("M09 — TACTICAL INTERFACE")
    r = httpx.get(f"{BASE_URL}/", follow_redirects=True)
    record("Tactical UI serving", check(
        "AXIOM UI accessible",
        r.status_code == 200 and "AXIOM" in r.text,
        f"Size: {len(r.content)} bytes"))

    # ── SUMMARY ───────────────────────────────────────────
    header("EVALUATION SUMMARY")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    pct = (passed / total * 100) if total else 0

    for label, p in results:
        print(f"  {'[PASS]' if p else '[FAIL]'} {label}")

    print()
    print(f"  RESULT: {passed}/{total} checks passed ({pct:.0f}%)")
    print()

    if pct >= 90:
        print("  EVALUATION STATUS: READY FOR TILO SANDBOX")
    elif pct >= 75:
        print("  EVALUATION STATUS: CONDITIONAL — ADDRESS FAILURES")
    else:
        print("  EVALUATION STATUS: NOT READY — REVIEW REQUIRED")

    print()
    print("  Nexxon National | Unclassified")
    print("  AXIOM v0.1.0 | github.com/nexxondev/axiom")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
