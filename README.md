# 🏛️ Data Model Architect Studio

> Autonomous Multi-Agent AI System for Designing, Reviewing, and Certifying Enterprise Database Schemas, OpenDataContracts (ODCS v3.0.0), Standardized 5-Section STTM Documents, and Medallion SQL Pipelines.

---

## 📑 Table of Contents
1. [🚀 Quickstart](#-quickstart)
2. [🧭 How to Use the Studio](#-how-to-use-the-studio)
   - [🟢 Workflow 1: Create New Data Model (Day 0)](#1-workflow-1-create-new-data-model-day-0)
   - [🔵 Workflow 2: Evolve & Add Business Rules (Day 2+)](#2-workflow-2-evolve--add-business-rules-day-2)
3. [🛡️ The 8-Micro-Agent Fleet & Architecture](#️-the-8-micro-agent-fleet--architecture)
4. [📦 Deliverable Artifacts Specification](#-deliverable-artifacts-specification)
5. [🧪 Automated Testing & In-Memory DuckDB Verification](#-automated-testing--in-memory-duckdb-verification)
6. [🌐 Synchronized Repositories](#-synchronized-repositories)

---

## 🚀 Quickstart

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/rachardv/data-model-architect.git
cd data-model-architect

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or: .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run 1-Click Verification Suite (118/118 Passing Tests)
```bash
# Windows
.\verify.ps1

# Linux / MacOS
./verify.sh

# Or directly via Pytest
python -m pytest tests/ -v
```

---

## 🧭 Two Distinct Operating Workflows: 🎨 Studio vs. 🛠️ Forge

The repository enforces a strict, enterprise-grade separation between **domain modeling** and **engine development**:

```mermaid
flowchart TD
    UserReq["Incoming Task"] --> Choice{"What are you working on?"}

    %% ------------------------------------------------------------------------
    %% WORKFLOW 1: STUDIO FLOW
    %% ------------------------------------------------------------------------
    Choice -->|Building a Domain Model| Studio["🎨 <b>STUDIO WORKFLOW (Domain Modeling)</b>"]
    
    subgraph StudioFlow["Studio Workflow Scope"]
        direction TB
        S1["1. Input Narrative & Rules (e.g. retail, healthcare, fintech)"]
        S2["2. Layer 1: Pre-Flight Gate 0 (5 Vectors & Contradictions)"]
        S3["3. Autonomous Schema Synthesis (Kimball Star / 3NF / Bridges)"]
        S4["4. Layer 2: Model Dual-Gate (4 Reviewers + DuckDB Math Verification)"]
        S5["5. Export Deliverables (STTM, DDL, dbt, Transpiled SQL)"]
        S1 --> S2 --> S3 --> S4 --> S5
    end

    Studio --> StudioFlow
    S5 --> StudioOut["📦 Outputs: docs/pipelines/<domain>/<br>🚫 Master docs untouched! Zero industry suites!"]

    %% ------------------------------------------------------------------------
    %% WORKFLOW 2: FORGE FLOW
    %% ------------------------------------------------------------------------
    Choice -->|Upgrading the Modeler Engine| Forge["🛠️ <b>FORGE WORKFLOW (Engine Evolution & Certification)</b>"]
    
    subgraph ForgeFlow["Forge Workflow Scope"]
        direction TB
        F1["1. Modify Engine Logic in src/ (transpiler, risk tiers, etc.)"]
        F2["2. Run 118-Test Regression Suite (py -3.14 -m pytest)"]
        F3["3. Layer 3: Predefined Benchmark Gate (--benchmark-gate)"]
        F4["4. 🏛️ <b>Industry Standards Benchmark Gate</b><br>(TPC-DI, TPC-H, SSB, TPC-DS, BIRD-SQL, Spider)"]
        F5["5. Synchronize Master Architecture Docs (README, ARCHITECTURE)"]
        F1 --> F2 --> F3 --> F4 --> F5
    end

    Forge --> ForgeFlow
    F5 --> ForgeOut["🚀 Outputs: src/, tests/, docs/ARCHITECTURE_AND_RUBRICS.md<br>✅ Master docs updated!"]
```

| Dimension | 🎨 **Studio Workflow** *(Data Modeling)* | 🛠️ **Forge Workflow** *(Engine Evolution)* |
| :--- | :--- | :--- |
| **Who uses it** | Data Engineers, Analytics Engineers, Business Architects | Core Platform Engineers, AI Developers |
| **Objective** | Build a specific domain data model (e.g. Retail, Healthcare, Lending). | Modify or extend the modeling engine itself in `src/`. |
| **Validation Gates** | **Layer 1** (Intake Gate) & **Layer 2** (Model Dual-Gate). | **Layer 3** (Predefined Gate 1-by-1) + **Industry Standards Gate** (TPC-DI, TPC-H, SSB, TPC-DS, BIRD-SQL, Spider) + 118-Test Suite. |
| **Industry Benchmarks?** | 🚫 **NEVER** (Isolated to Forge; keeps domain modeling fast & lean). | ✅ **MANDATORY** (Runs 200+ physical checks before engine release). |
| **Master Docs Touched?** | 🚫 **NEVER** (Only writes to `docs/pipelines/<domain>/`). | ✅ **MANDATORY** (`README.md`, `ARCHITECTURE_AND_RUBRICS.md` updated). |
| **Primary CLI Command** | `py src/cli.py --story "..." --domain <name>` | `py src/cli.py --forge` |


---

### 1. Workflow 1: Create New Data Model (Day 0)
Use this workflow when you are starting from scratch with a new business idea, PRD, or user story.

#### Step A: Provide your raw business narrative in Python:
```python
from src.orchestration.captain import CaptainOrchestrator

captain = CaptainOrchestrator(output_dir="docs")

payload = {
    "domain": "ecommerce_retail",
    "narrative": "Customers visit our online store and purchase physical products using credit card or PayPal. We want to build executive dashboards to track daily gross revenue and top selling products over time."
}

result = captain.execute_workflow(payload)
```

#### Step B: The Phase 0 Intake Squad Evaluates Completeness:
1. 🔍 **`semantic_scribe_agent`:** Checks for sanity (no gibberish) and parses nouns & verbs.
2. ⚖️ **`completeness_auditor_agent`:** Evaluates the **5-Vector Metric** (Workload, Grain, History, Funnel, Multiplicity).
3. 🛑 **Strict 100% Hard Gate:** If score $< 100\%$, it **halts and returns targeted plain-English questions**:
   ```python
   if result["status"] == "INTAKE_INCOMPLETE_BLOCKED":
       print("Score:", result["completeness_score"])
       for q in result["questions"]:
           print(q["question"])
           print(q["options"])
   ```

#### Step C: Supply the Business Answers to Reach 100% Certification:
```python
payload["business_answers"] = [
    "Historical reports should preserve original customer address at time of purchase (SCD Type 2)."
]

# Re-run: Reaches 100.0% Completeness and automatically compiles all deliverables!
certified_result = captain.execute_workflow(payload)
print("Status:", certified_result["status"])  # CERTIFIED_PRODUCTION_READY
print("Architecture Pattern:", certified_result["architecture_pattern"])  # KIMBALL_STAR_SCD2
```

---

### 2. Workflow 2: Evolve & Add Business Rules (Day 2+)
Use this workflow when you **already have an existing schema** (`docs/schema.sql` or a dbt project) and want to:
* Layer on new validation rules (e.g. *"Premiums must be $\ge \$50.00$"*).
* Introduce new business entities (e.g. *"Assign orders to Logistics 3PL Carriers"*).
* Change a fact table to enable multi-stage lifecycle history (Accumulating Snapshot).

#### Step A: Submit your existing schema + new business rules:
```python
payload = {
    "branch": "ADD_BUSINESS_RULES",
    "domain": "ecommerce_retail",
    "existing_schema_path": "docs/schema.sql",
    "rules": [
        {
            "name": "min_order_threshold",
            "description": "Order total must be greater than zero",
            "definition": "order_amount_usd > 0.00",
            "action": "QUARANTINE"
        },
        {
            "name": "carrier_assignment",
            "description": "Every order must be assigned to a 3PL Logistics Carrier",
            "rule_text": "Assign each order to a Logistics Carrier entity with standard 1:1 carrier per order and SCD2 history."
        }
    ]
}

result = captain.execute_workflow(payload)
```

#### Step B: What the Agent Does Automatically:
1. **Kimball Entity Delta Detection:** Detects `carrier` is an unreferenced entity, creates `dim_carrier_scd2`, and adds `carrier_sk` to `fact_orders`.
2. **Hardens DDL:** Appends `CHECK (order_amount_usd > 0.00)` to `docs/schema.sql`.
3. **Generates Silver Quarantine View:** Generates `v_quarantine_orders` so invalid records in production are isolated without crashing downstream BI pipelines.
4. **Updates STTM:** Synchronizes [`docs/SOURCE_TO_TARGET_MAPPING.md`](docs/SOURCE_TO_TARGET_MAPPING.md) with the new carrier joins and rules.

---

## 🛡️ The 8-Micro-Agent Fleet & Architecture

```mermaid
flowchart TD
    CAPTAIN["⭐ Captain Orchestrator<br/><i>(Master Workflow & State Bus)</i>"]

    subgraph PHASE0["1️⃣ Phase 0: The Intake Squad (Discovery)"]
        S1["🔍 <code>semantic_scribe_agent</code> (Sanity & DDD Grammar)"]
        S2["⚖️ <code>completeness_auditor_agent</code> (Strict 100% Gate)"]
        S3["💬 <code>business_interviewer_agent</code> (Natural Dialogue)"]
    end

    subgraph PHASE1["2️⃣ Phase 1: Lead Modeler"]
        D1["📐 <code>data_model_architect_agent</code> (Schema & SCD2 Design)"]
    end

    subgraph PHASE2["3️⃣ Phase 2: Core 4 Risk Review Council"]
        R1["💰 <code>financial_risk_reviewer</code> (Decimals & Formulas)"]
        R2["⏳ <code>temporal_risk_reviewer</code> (SCD2 '9999-12-31' Sentinels)"]
        R3["🔗 <code>relational_risk_reviewer</code> (3NF & Decoupled Bridges)"]
        R4["🏗️ <code>refactor_risk_reviewer</code> (Mini-Dimensions & Outriggers)"]
    end

    subgraph PHASE6["4️⃣ Phase 6: Compilation & Handover"]
        C1["🗺️ <code>STTMGenerator</code> (5-Section Mapping)"]
        C2["🏗️ <code>ANSISQLGenerator</code> (ANSI DDL)"]
        C3["📜 <code>DataContractCompiler</code> (ODCS v3.0.0)"]
        C4["🌊 <code>MedallionPipelineGenerator</code> (Bronze/Silver/Gold)"]
        C5["🦆 <code>DuckDBPipelineRunner</code> (In-Memory Verification)"]
    end

    CAPTAIN --> PHASE0 --> PHASE1 --> PHASE2 --> PHASE6
```

---

## 📦 Deliverable Artifacts Specification

Every certified run automatically generates **5 enterprise-grade production deliverables**:

### 1. 🗺️ Standardized 5-Section STTM ([`docs/SOURCE_TO_TARGET_MAPPING.md`](docs/SOURCE_TO_TARGET_MAPPING.md))
* **Section 1: Short Description** (Business role and atomic grain).
* **Section 2: Source Tables** (Bronze landing tables and Silver staging models).
* **Section 3: Destination Table** (Gold target table and primary surrogate key).
* **Section 4: Raw SQL** (Production CTE transformation query).
* **Section 5: Column Mapping & Business Logic Matrix** (Column name, data type, nullable, plain-English description, and SQL transformation expression).

### 2. 🏗️ Clean ANSI SQL DDL ([`docs/schema.sql`](docs/schema.sql))
* 100% portable `CREATE TABLE` DDL scripts with primary keys, foreign keys, and hard database `CHECK` constraints.

### 3. 📜 OpenDataContract Standard v3.0.0 ([`docs/contract.yaml`](docs/contract.yaml))
* Industry-standard data contract specifying schema invariants, SLA freshness, and automated quarantine rules.

### 4. 🌊 Full Medallion Pipeline SQL ([`docs/pipelines/`](docs/pipelines/))
* **Bronze Layer:** Raw landing DDL with ingest audit timestamps.
* **Silver Layer:** Window deduplication CTEs and `v_quarantine_*` error views.
* **Gold Layer:** Incremental SCD2 merge queries and dimensional fact aggregations.

### 5. 🎨 Interactive Visual Mermaid ERD ([`docs/data_models/erd.md`](docs/data_models/erd.md))
* Rich, embedded Mermaid entity-relationship diagrams rendered directly in Markdown.

### 6. 🌐 Multi-Dialect SQL Transpilation ([`src/transpiler.py`](src/transpiler.py))
* Compiles Medallion models across **DuckDB, Snowflake, BigQuery, Postgres, and Databricks** via SQLGlot AST transpilation.

### 7. 🎯 Predefined Benchmark Gate & Traceability ([`docs/benchmarks/traces/`](docs/benchmarks/traces/))
* Evaluates enterprise test cases **1-by-1** sequentially in isolated DuckDB databases.
* Generates auditable `<case_id>_trace.json` and human-readable `<case_id>_trace.md` reports with clean overwrite semantics upon redeployment.

---

## 💻 Command-Line Interface (CLI)

```bash
# 1. Execute the full Forge Engine Certification Battery (Predefined Gate + Industry Standards)
py src/cli.py --forge

# 2. Run the Predefined Benchmark Validation Gate alone (1-by-1 Sequential Battery)
py src/cli.py --benchmark-gate

# 3. Run the Industry Standards Benchmark Suite alone (TPC-DI, TPC-H, SSB, TPC-DS, BIRD-SQL, Spider)
py src/cli.py --industry-benchmark

# 4. Run Studio Workflow: Generate a domain data model
py src/cli.py --story "Customers buy products" --domain retail --medallion --dialect all
```

---

## 🧪 Automated Testing & In-Memory DuckDB Verification

The entire repository includes a comprehensive 118-test automated verification suite:

```bash
python -m pytest tests/ -v
```

### Test Coverage Highlights (118 Passing Tests across 5 Domains):
* 🧪 **Layer 1 Intake & Guardrails (21 tests):** Tests 5 Information Vectors, low-entropy gibberish rejection (`"asdf"`), and vector conflict / contradiction traps.
* 🧪 **Layer 2A Static Reviewers & dbt-evaluator (17 tests):** Tests 4-tier risk profiling, DFS cycle detection, chasm trap static linter, and staging bypass.
* 🧪 **Layer 2B Physical In-Memory Proofs (9 tests):** Asserts the 4 physical laws in DuckDB (Metric Conservation to $0.0000, SCD2 temporal causality, referential integrity, and EXPLAIN hash joins).
* 🧪 **Layer 3 Predefined Benchmark Gate (5 tests):** Validates 1-by-1 isolated DuckDB execution, intentional trap defense verification, and DecisionTracer overwrite mechanics.
* 🧪 **Multi-Dialect Transpiler (7 tests):** Transpiles Medallion models across DuckDB, Snowflake, BigQuery, Postgres, and Databricks.
* 🧪 **Industry Standards (34 tests):** Executes full 3-batch TPC-DI data integration, TPC-H fanout benchmarks, Star Schema Benchmark (SSB), and BIRD-SQL/Spider semantic evaluations.

---

## 🌐 Synchronized Repositories

* 🏢 **Organization Repo:** [https://github.com/synology-dev-projects/data-modeling-agent-system](https://github.com/synology-dev-projects/data-modeling-agent-system)
* 👤 **Personal Repo:** [https://github.com/rachardv/data-model-architect](https://github.com/rachardv/data-model-architect)
