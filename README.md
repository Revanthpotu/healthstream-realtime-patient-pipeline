# HealthStream v2 — Real-Time Patient Data Integration Platform

A production-grade real-time data integration platform demonstrating **3 integration methods**, **ksqlDB stream processing**, **AI-powered operational intelligence**, and **Kafka security** — all in the healthcare domain.

Inspired by Confluent's **Real-Time Context Engine** pattern.

## Quick Start

```bash
bash scripts/start_all.sh
# Then in separate terminals:
python producer/csv_producer.py --max-records 5000
python context-engine/context_materializer.py
python monitoring/health_monitor.py
export OPENAI_API_KEY='sk-...' && python agent/agent.py
```

## Service Ports

| Service | Port | Health Check |
|---------|------|--------------|
| Kafka Broker 1 | 9092 | — |
| Kafka Broker 2 | 9093 | — |
| Kafka Broker 3 | 9094 | — |
| Schema Registry | 8081 | http://localhost:8081/subjects |
| Kafka Connect | 8083 | http://localhost:8083/connectors |
| ksqlDB | 8088 | http://localhost:8088/info |
| PostgreSQL | 5432 | — |
| MySQL | 3306 | — |
| Redis | 6379 | — |



# 🏥 HealthStream — Real-Time Patient Data Integration Pipeline

> 3 data sources → Apache Kafka → ksqlDB → Redis → 3 AI Agents (GPT-4o) → Doctor Dashboard

![Architecture](architecture/HealthStream-Architecture.png)

---

## What This Project Does

HealthStream unifies patient data from **3 heterogeneous healthcare systems** into a 
single real-time view, powered by event-driven stream processing and AI-driven 
operational automation.

| Source | Database | Ingestion Method | Why This Method |
|--------|----------|-----------------|-----------------|
| Lab Results | CSV Files | Python Producer | No DB backing → custom ingestion |
| EHR / Diagnoses | PostgreSQL | JDBC Connector | Moderate latency acceptable |
| Pharmacy / Meds | MySQL | Debezium CDC | Must capture DELETEs (discontinued meds) |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Messaging | Apache Kafka (3-broker) | Event backbone, durable commit log |
| Serialization | Apache Avro + Schema Registry | Schema-on-write enforcement |
| Stream Processing | ksqlDB | SQL-on-streams, windowed joins |
| Caching | Redis | Materialized patient view, 24-hr TTL |
| Error Handling | Dead Letter Queue | Quarantine + metadata for failed messages |
| AI Agents | GPT-4o + Function Calling | 3 agents, 18 tools total |
| Dashboard | Python Flask + HTML/JS | Real-time UI with AI chat |
| Containerization | Docker Compose | Full stack in one command |

---

## 3 AI Agents — Not Chatbots

These agents automate **real Kafka operational work**, not just Q&A.

### 🩺 Clinical Agent (Consumer Layer)
Doctor-facing NLP queries over unified patient data.
6 tools: patient lookup, triage assessment, pipeline health, 
dependency impact analysis, patient list, source impact.

### 🔌 Integration Agent (Ingestion Layer)  
Automates onboarding new data sources into Kafka.
6 tools: connector recommendation, config generation, 
producer scripting, deployment, status checks, listing.

### 🔍 Monitor Agent (Monitoring Layer)
Automated DLQ triage with root cause analysis.
6 tools: DLQ scan, error pattern detection, root cause diagnosis, 
connector health, schema validation, alert report generation.

---

## Quick Start
```bash
git clone https://github.com/YOUR_USERNAME/healthstream-realtime-patient-pipeline.git
cd healthstream-realtime-patient-pipeline
cp .env.example .env        # add your OpenAI key
docker-compose up -d
# Dashboard → http://localhost:5050
```

---

## Production Mapping (AWS)

| Demo (Docker) | Production (AWS) |
|---------------|-----------------|
| Apache Kafka | Amazon MSK |
| ksqlDB | Amazon Managed Flink |
| Redis | Amazon ElastiCache |
| Python Agents | ECS / Lambda |
| Schema Registry | Glue Schema Registry |

Security: TLS in-transit, KMS at-rest, IAM + ACLs, VPC isolation.

---

## Architecture Deep Dive

**Data Flow:**
CSV/PostgreSQL/MySQL → Producers/Connectors → Kafka (Avro + Schema Registry) 
→ ksqlDB (stream joins + enrichment) → Redis (materialized views, <1ms reads) 
→ Clinical Agent + Dashboard

**Error Flow:**
Failed messages → Dead Letter Queue → Monitor Agent (auto-triage) → Email/Slack alerts

**Key Design Decisions:**
- Debezium CDC for pharmacy because JDBC doesn't capture DELETEs
- Avro over JSON for compact binary serialization + schema enforcement
- Redis TTL (24h) auto-evicts discharged patients, keeps working set small
- Replication factor 3 for zero data loss on broker failure

---

## Dashboard Preview

![Dashboard](architecture/dashboard-preview.png)

---

## Author

**Revanth** — Data Engineering
- Focused on real-time streaming, event-driven architecture, and AI-augmented data ops
```

---

**Step 4 — GitHub profile-level things**

- **Add topics** to the repo: `apache-kafka`, `data-engineering`, `real-time`, `ksqldb`, `redis`, `ai-agents`, `healthcare`, `stream-processing`, `python`, `docker`
- **Pin this repo** to your GitHub profile (Settings → pinned repositories)
- **Take a screenshot** of the dashboard running and add it as `architecture/dashboard-preview.png`
- **Take a screenshot** of the architecture diagram and add as `architecture/HealthStream-Architecture.png`
- **Add the `.drawio` file** so people can see the architecture is yours, not a random image

---

**Step 5 — Commit history matters**

Don't push everything in one commit. Break it into logical commits:
```
git add docker-compose.yml schemas/
git commit -m "feat: kafka cluster config + avro schemas for 3 patient data domains"

git add producers/
git commit -m "feat: 3 ingestion methods - python producer, JDBC, debezium CDC"

git add ksqldb/
git commit -m "feat: ksqlDB stream processing - joins, enrichment, materialized views"

git add agent/
git commit -m "feat: 3 CareAssist AI agents with GPT-4o function calling (18 tools)"

git add dashboard/
git commit -m "feat: real-time dashboard with AI chat interface"

git add docs/ presentation/ architecture/
git commit -m "docs: architecture diagrams, setup guide, production mapping"