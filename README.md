# 🏥 HealthStream — Real-Time Patient Data Integration Pipeline

A production-grade real-time data integration platform demonstrating **3 integration methods**, **ksqlDB stream processing**, **AI-powered operational intelligence**, and **Kafka security** — all in the healthcare domain.

Inspired by Confluent's **Real-Time Context Engine** pattern.A production-grade real-time data integration platform demonstrating **3 integration methods**, **ksqlDB stream processing**, **AI-powered operational intelligence**, and **Kafka security** — all in the healthcare domain.

Inspired by Confluent's **Real-Time Context Engine** pattern.

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
