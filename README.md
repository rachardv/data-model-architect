# 🏛️ Data Model Architect Studio

> Autonomous Multi-Agent System for Designing, Reviewing, and Certifying Enterprise Database Schemas, Visual Mermaid ERDs, and Data Contracts.

---

## 🚀 Quickstart (Ready Out of the Box)

### 1. Clone & Setup
```bash
git clone https://github.com/rachardv/data-model-architect.git
cd data-model-architect
python -m venv .venv
source .venv/bin/activate  # Or: .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run 1-Click Verification Suite (22/22 Verified Tests)
```bash
# Windows
.\verify.ps1

# Linux / MacOS
./verify.sh
```

---

## 🌟 Key Capabilities

1. **Zero-Jargon "21 Questions" Intake:** Translates plain-English business stories into optimal database patterns (Kimball Star Schema, 3NF, SCD2, Accumulating Snapshot).
2. **Recursive Folder Schema Auto-Scanner:** Ingests upstream schemas from `.sql`, `.json`, `.csv`, `.py`, `.ts`, `.prisma`, and `.yaml` files to discover capability gaps.
3. **Transparent Mockup Mode:** Automatically tags all AI-assumed columns with `[AI-GENERATED]` to eliminate silent hallucinations.
4. **Pure Deliverables Standard:**
   - 🎨 **Visual Interactive Mermaid ERD:** Embedded diagrams rendered in markdown (`docs/data_models/`).
   - 📜 **Clean Standard ANSI SQL DDL:** 100% portable `CREATE TABLE` scripts with constraints.
   - 📋 **Formal Data Contract Specification:** Business invariants, freshness SLAs, and data quality rules (`docs/data_contracts/`).
   - ⚡ **Full Medallion Pipeline (Bronze → Silver → Gold):** Strict ANSI SQL scripts (`docs/pipelines/<domain>/`) with raw landing DDL, window deduplication CTEs, invariant quarantine views, and SCD2 merge queries.
5. **In-Memory DuckDB SQL Execution Engine:** 1-Click test execution validating that generated Bronze, Silver staging, and Gold SCD2 merges run end-to-end against a real database instance.
6. **The Core 4 Risk Review Council:** Evaluates models against official **ISO/IEC 25012** & **Moody-Shanks** data model quality standards.
7. **Phase 5c Architect Sign-Off Gate:** Guarantees zero unacknowledged reviewer findings.

---

## 📁 Repository Structure

```
data-model-architect/
├── .agents/
│   ├── rules/
│   │   └── data-modeling-protocol.md          # Master Multi-Agent Protocol
│   └── agents/
│       ├── captain_orchestrator/              # Master Orchestration Subagent
│       ├── requirements_architect_agent/      # Intake Triage Agent Definition
│       ├── data_model_architect_agent/        # Lead Architect Agent Definition
│       ├── financial_risk_reviewer/           # Grain & Double-Counting Auditor
│       ├── temporal_risk_reviewer/            # Time-Travel & Interval Auditor
│       ├── relational_risk_reviewer/          # Decoupling & Cardinality Auditor
│       └── refactor_risk_reviewer/            # Conformed Mart Sprouting Auditor
├── src/
│   ├── orchestration/
│   │   ├── captain.py                         # Master Factory Orchestrator
│   │   ├── spawner.py                         # Subagent Fleet Spawner
│   │   └── reviewer_council.py                # Core 4 ISO/IEC 25012 Audits
│   ├── decision_engine.py                     # 21 Questions Adaptive Decision Tree
│   ├── noun_verb_parser.py                    # DDD Semantic Parser
│   ├── folder_scanner.py                      # Recursive Upstream Schema Ingestion
│   ├── erd_generator.py                       # Visual Mermaid ERD Generator
│   ├── ddl_generator.py                       # Standard ANSI SQL DDL Generator
│   ├── contract_compiler.py                   # Data Contract Invariant Compiler
│   ├── medallion_generator.py                 # Bronze -> Silver -> Gold SQL Pipeline
│   ├── sql_runner.py                          # In-Memory DuckDB Pipeline Execution Engine
│   └── cli.py                                 # Command Line Interface
├── tests/
│   ├── test_benchmark_10_scenarios.py         # 10 Canonical TPC-DS/Kimball Benchmarks
│   ├── test_factory_full_capabilities.py      # Scanner, ERD, Contract Factory Tests
│   ├── test_multi_agent_orchestration.py      # Captain & Reviewer Council Tests
│   ├── test_medallion_pipeline.py             # Bronze, Silver, Gold Pipeline Tests
│   └── test_duckdb_execution.py               # In-Memory DuckDB Execution Tests
├── docs/
│   ├── data_models/                           # Destination for Visual Mermaid ERDs
│   ├── data_contracts/                        # Destination for Data Contracts
│   └── pipelines/                             # Destination for Layered Medallion SQL
└── examples/                                  # Ready-to-use domain templates
```

---

## 🧪 Benchmark Proof
Validated against **TPC-DS**, **TPC-H**, and the **Kimball Lifecycle Group** canonical industry scenarios with **22/22 Passing Tests (100% Accuracy)**.
