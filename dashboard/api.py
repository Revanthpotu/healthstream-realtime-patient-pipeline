"""
============================================================================
HealthStream v2 — Dashboard Server
============================================================================
Serves the dashboard UI at http://localhost:5050
REST API at http://localhost:5050/api/*

Redis keys used (matching context_materializer.py + health_monitor.py):
  patient:{id}       → patient context JSON
  patients:all       → set of all patient IDs
  source:health      → source health JSON  {csv_lab_export: {count, status, last_seen}, ...}
  stats:global       → stats JSON  {vitals_processed, conditions_processed, ...}
  stats:total_patients → total patient count
  health:latest      → health report JSON  {connectors, schema_registry, ksqldb, ...}
  dlq:recent_errors  → JSON array of DLQ errors
============================================================================
"""

import json, os, sys, time
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def sj(data):
    """Safe JSON parse."""
    if not data:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


# ── Serve Dashboard ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


# ── System Overview ─────────────────────────────────────────────────────
@app.route("/api/health")
def api_health():
    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    health = sj(r.get("health:latest")) or {}
    stats = sj(r.get("stats:global")) or {}
    source_health = sj(r.get("source:health")) or {}
    patient_count = r.scard("patients:all")

    return jsonify({
        "status": health.get("overall_status", "healthy" if redis_ok else "degraded"),
        "redis_connected": redis_ok,
        "patient_count": patient_count,
        "stats": stats,
        "source_health": source_health,
        "infrastructure": {
            "schema_registry": health.get("schema_registry", {}),
            "ksqldb": health.get("ksqldb", {}),
            "connectors": health.get("connectors", {}),
        },
        "topics": health.get("topics", {}),
    })


# ── Pipeline Sources ────────────────────────────────────────────────────
@app.route("/api/pipeline")
def api_pipeline():
    source_health = sj(r.get("source:health")) or {}
    stats = sj(r.get("stats:global")) or {}
    health = sj(r.get("health:latest")) or {}

    source_meta = {
        "csv_lab_export": {"label": "CSV Lab Export", "icon": "vitals", "topic": "patient-vitals",
                           "method": "Custom Python Producer", "stat_key": "vitals_processed"},
        "jdbc_postgres": {"label": "PostgreSQL EHR", "icon": "conditions", "topic": "patient-conditions",
                          "method": "JDBC Source Connector", "stat_key": "conditions_processed"},
        "debezium_mysql": {"label": "MySQL Pharmacy", "icon": "medications", "topic": "patient-medications",
                           "method": "Debezium CDC", "stat_key": "medications_processed"},
    }

    sources = []
    for key, meta in source_meta.items():
        sh = source_health.get(key, {})
        sources.append({
            "key": key,
            "label": meta["label"],
            "icon": meta["icon"],
            "topic": meta["topic"],
            "method": meta["method"],
            "status": sh.get("status", "unknown"),
            "messages_processed": stats.get(meta["stat_key"], sh.get("count", 0)),
            "last_seen": sh.get("last_seen"),
            "gap_seconds": sh.get("gap_seconds"),
        })

    return jsonify({
        "sources": sources,
        "connectors": health.get("connectors", {}),
        "stats": stats,
        "infrastructure": {
            "schema_registry": health.get("schema_registry", {}),
            "ksqldb": health.get("ksqldb", {}),
        },
    })


# ── Patient List ────────────────────────────────────────────────────────
@app.route("/api/patients")
def api_patients():
    patient_ids = r.smembers("patients:all")
    results = []

    for pid in sorted(patient_ids):
        raw = r.get(f"patient:{pid}")
        d = sj(raw)
        if not d:
            continue

        vitals_summary = {}
        for vname, vdata in d.get("vitals", {}).items():
            vitals_summary[vname] = {
                "value": vdata.get("value"),
                "units": vdata.get("units", ""),
                "trend": vdata.get("trend", {}).get("direction", "stable"),
                "pct_change": vdata.get("trend", {}).get("pct_change", 0),
            }

        results.append({
            "patient_id": pid,
            "age": d.get("patient_age", "?"),
            "gender": d.get("patient_gender", "?"),
            "vitals": vitals_summary,
            "conditions": [
                c.get("name", c) if isinstance(c, dict) else c
                for c in d.get("conditions", [])
            ],
            "medications": [
                m.get("name", m) if isinstance(m, dict) else m
                for m in d.get("medications", [])
            ],
            "condition_count": len(d.get("conditions", [])),
            "medication_count": len(d.get("medications", [])),
            "last_updated": d.get("last_updated", ""),
        })

    return jsonify({"patients": results, "total": len(results)})


# ── Patient Detail ──────────────────────────────────────────────────────
@app.route("/api/patients/<path:pid>")
def api_patient_detail(pid):
    d = sj(r.get(f"patient:{pid}"))
    if not d:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify(d)


# ── Patients Needing Attention ──────────────────────────────────────────
@app.route("/api/alerts")
def api_alerts():
    patient_ids = r.smembers("patients:all")
    concerning = []

    for pid in patient_ids:
        d = sj(r.get(f"patient:{pid}"))
        if not d:
            continue
        reasons = []

        for vn, vd in d.get("vitals", {}).items():
            t = vd.get("trend", {})
            dr = t.get("direction", "stable")
            pct = abs(t.get("pct_change", 0))
            v = vd.get("value", 0)

            if vn == "heart_rate" and v and v > 100:
                reasons.append({"type": "critical", "msg": f"Elevated heart rate: {v:.0f} bpm"})
            if vn == "heart_rate" and dr == "rising" and pct > 10:
                reasons.append({"type": "warning", "msg": f"Heart rate rising {pct:.1f}%"})
            if vn == "oxygen_saturation" and v and v < 94:
                reasons.append({"type": "critical", "msg": f"Low oxygen saturation: {v:.1f}%"})
            if vn == "oxygen_saturation" and dr == "falling" and pct > 3:
                reasons.append({"type": "warning", "msg": f"Oxygen falling {pct:.1f}%"})
            if vn == "systolic_bp" and v and v > 160:
                reasons.append({"type": "warning", "msg": f"High systolic BP: {v:.0f} mmHg"})
            if vn == "systolic_bp" and v and v < 90:
                reasons.append({"type": "warning", "msg": f"Low systolic BP: {v:.0f} mmHg"})
            if vn == "temperature" and v and v > 100.4:
                reasons.append({"type": "critical", "msg": f"Fever: {v:.1f}°F"})
            if vn == "respiratory_rate" and v and v > 25:
                reasons.append({"type": "warning", "msg": f"High respiratory rate: {v:.0f}/min"})

        if reasons:
            concerning.append({
                "patient_id": pid,
                "age": d.get("patient_age", "?"),
                "gender": d.get("patient_gender", "?"),
                "conditions": [
                    c.get("name", c) if isinstance(c, dict) else c
                    for c in d.get("conditions", [])
                ],
                "reasons": reasons,
                "severity": "critical" if any(rr["type"] == "critical" for rr in reasons) else "warning",
            })

    concerning.sort(key=lambda x: (-len(x["reasons"]), x["severity"] != "critical"))
    return jsonify({"patients": concerning, "total": len(concerning)})


# ── DLQ Analysis ────────────────────────────────────────────────────────
@app.route("/api/dlq")
def api_dlq():
    raw = r.get("dlq:recent_errors")
    errors = sj(raw) or []
    categories = {}
    for err in errors:
        reason = err.get("error_reason", "unknown")
        cat = reason.split(":")[0] if ":" in reason else reason
        categories[cat] = categories.get(cat, 0) + 1

    return jsonify({
        "total": len(errors),
        "categories": categories,
        "recent": errors[-5:] if errors else [],
    })


# ── AI Chat ─────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "Set OPENAI_API_KEY in your .env file to use the AI Agent."}), 500

    from openai import OpenAI
    from agent.tools.agent_tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

    client = OpenAI(api_key=api_key)
    user_msg = request.json.get("message", "")

    system = (
        "You are the HealthStream AI Agent — an expert assistant that monitors a real-time "
        "patient data integration pipeline.\n\n"
        "You have access to live data from 3 hospital systems flowing through Apache Kafka:\n"
        "• Source A (CSV Lab Export): Vital signs via a custom Python Avro producer\n"
        "• Source B (PostgreSQL EHR): Conditions/diagnoses via Kafka Connect JDBC\n"
        "• Source C (MySQL Pharmacy): Medications via Debezium CDC\n\n"
        "Architecture: Sources → Kafka (3 brokers, Schema Registry, Avro) → ksqlDB → Redis → AI Agent (you)\n\n"
        "Answer concisely and use markdown formatting. Be specific with numbers."
    )

    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_msg}]
    resp = client.chat.completions.create(model="gpt-4o", messages=messages, tools=TOOL_DEFINITIONS, tool_choice="auto")
    msg = resp.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for tc in msg.tool_calls:
            fn = TOOL_FUNCTIONS.get(tc.function.name)
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            result = fn(**args) if fn else json.dumps({"error": "Unknown tool"})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        resp = client.chat.completions.create(model="gpt-4o", messages=messages)
        msg = resp.choices[0].message

    return jsonify({"response": msg.content})


# ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   HealthStream v2 — Dashboard Server         ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║   Dashboard → http://localhost:5050           ║")
    print(f"  ║   Redis     → {REDIS_HOST}:{REDIS_PORT}                  ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    app.run(host="0.0.0.0", port=5050, debug=False)
