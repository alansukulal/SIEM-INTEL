# 🧠 SIEM-INTEL
## Agentic SIEM Alert Investigation Platform

**Python · FastAPI · LangGraph · LangChain · Microsoft Sentinel · KQL · PostgreSQL · RAG · LLMs**

SIEM-INTEL is an AI-powered security investigation platform designed to assist SOC analysts throughout the SIEM alert investigation lifecycle.

Instead of relying on a single LLM response, SIEM-INTEL uses a stateful agentic workflow to interpret security alerts, plan investigations, generate and validate SIEM queries, collect evidence, evaluate investigation results, and produce analyst-oriented findings.

The long-term goal is to evolve SIEM-INTEL into a multi-tenant, multi-SIEM investigation platform combining agentic AI, security knowledge retrieval, threat intelligence, event correlation, ticketing, and controlled response automation.

**🚧 Status: Active Development**

The core investigation workflow and Microsoft Sentinel integration have been developed. Multi-turn investigation support and broader platform capabilities are being developed incrementally.

---

# 🎯 The Problem

SIEM analysts often spend significant time performing repetitive investigation tasks:

- Understanding an incoming security alert
- Identifying relevant log sources
- Determining the correct SIEM tables
- Writing investigation queries
- Validating and executing those queries
- Collecting security evidence
- Correlating events
- Reviewing documentation and runbooks
- Determining whether sufficient evidence exists
- Writing investigation findings
- Creating or updating incident tickets

These tasks frequently require switching between SIEM platforms, documentation, threat intelligence sources, scripts, and ticketing systems.

SIEM-INTEL introduces an AI-driven investigation orchestration layer between the security analyst and the underlying security platforms.

---

# 🧩 Core Design

SIEM-INTEL is designed around five principles:

### 🧠 Agentic Investigation

Investigation is performed through multiple controlled workflow stages rather than a single LLM prompt.

### 🔎 Evidence-Driven Reasoning

Investigation conclusions should be based on retrieved SIEM evidence rather than unsupported model assumptions.

### 🛡️ Controlled Tool Execution

The LLM participates in planning and reasoning, while SIEM execution is performed through controlled application tools.

### 💾 Stateful Investigation

Investigation state, conversation history, and workflow checkpoints can persist across interactions.

### 👤 Analyst Oversight

AI assists the investigation process while critical security decisions remain under analyst control.

---
# 🗺️ System Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/de3e9ba1-f8dd-4550-9da5-b503fd1807b7" />

---

# 🚀 Current Capabilities

## 1. Agentic Investigation Workflow

LangGraph orchestrates the investigation lifecycle using specialized workflow components.

The workflow is designed to:

1. Interpret the incoming alert
2. Determine the investigation objective
3. Create an investigation plan
4. Identify relevant SIEM tables
5. Generate investigation queries
6. Validate generated queries
7. Execute approved queries
8. Retrieve security evidence
9. Evaluate evidence sufficiency
10. Determine whether further investigation is needed
11. Generate analyst-oriented findings

Conditional routing allows the workflow to continue investigating when additional evidence is required.

Execution is bounded to prevent uncontrolled agent loops.

## 2. Microsoft Sentinel Integration

Microsoft Sentinel is the currently implemented SIEM integration.

SIEM-INTEL uses Azure authentication and Azure Monitor query capabilities to:

- Connect to the Sentinel environment
- Execute KQL queries
- Retrieve security telemetry
- Return evidence to the investigation workflow

---

# 🔮 Future Development

The platform is intended to evolve incrementally toward:

- Multi-turn conversational investigations
- Persistent investigation memory
- Multi-SIEM integrations
- Security knowledge retrieval
- Threat intelligence enrichment
- Event correlation and analysis
- Ticketing integrations
- Controlled response automation
- Multi-tenant architecture

---

# 🏗️ Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Framework | LangChain |
| AI | Large Language Models |
| Retrieval | RAG, Semantic Search |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Database | PostgreSQL |
| SIEM | Microsoft Sentinel |
| Query Language | KQL |
| Validation | Pydantic |

---

# 💡 Engineering Philosophy

> Build AI systems that don't just generate responses, but plan, reason, retrieve evidence, interact with tools, and execute controlled workflows.

**SIEM-INTEL — Bringing Agentic AI into Security Operations.** 🧠
