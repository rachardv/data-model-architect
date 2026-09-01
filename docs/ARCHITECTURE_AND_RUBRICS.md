# 🏛️ Data Model Architect Studio: Architecture & Evaluation Rubrics

> Comprehensive Architectural Specification, Multi-Agent Fleet Hierarchy, Phase 0 Intake Squad, Strict 100% Information Completeness Hard Gate, Standardized 5-Section STTM Matrix, and Industry Benchmark Verification Scores.

---

## 📑 Table of Contents
1. [System Architecture: The 8-Micro-Agent Fleet](#1-system-architecture-the-8-micro-agent-fleet)
2. [Phase 0 Intake Squad & Strict 100% Information Gate](#2-phase-0-intake-squad--strict-100-information-gate)
3. [The Unified Mandatory Audit Funnel with Human-in-the-Loop (HITL) Gates](#3-the-unified-mandatory-audit-funnel-with-human-in-the-loop-hitl-gates)
4. [Standardized 5-Section Source-to-Target Mapping (STTM) Specification](#4-standardized-5-section-source-to-target-mapping-sttm-specification)
5. [Industry Benchmark Verification Scores (37/37 Tests - 100% Pass)](#5-industry-benchmark-verification-scores)

---

## 1. System Architecture: The 8-Micro-Agent Fleet

The Studio operates on a **Decoupled Multi-Agent Fleet Architecture** where each micro-agent possesses a strictly isolated cognitive scope, eliminating context drift and token bloat:

```mermaid
flowchart TD
    CAPTAIN["⭐ Captain Orchestrator<br/><i>(Master Workflow & State Bus)</i>"]

    subgraph PHASE0["1️⃣ Phase 0: The Intake Squad (Discovery)"]
        S1["🔍 <code>semantic_scribe_agent</code><br/><i>Sanity Filter & DDD Noun-Verb Grammar</i>"]
        S2["⚖️ <code>completeness_auditor_agent</code><br/><i>5-Vector Math Scoring & Strict 100% Gate</i>"]
        S3["💬 <code>business_interviewer_agent</code><br/><i>Natural Consultative Business Dialogue</i>"]
    end

    subgraph PHASE1["2️⃣ Phase 1: Lead Modeler"]
        D1["📐 <code>data_model_architect_agent</code><br/><i>Target Schema & SCD2 Authoring</i>"]
    end

    subgraph PHASE2["3️⃣ Phase 2: Core 4 Risk Review Council"]
        R1["💰 <code>financial_risk_reviewer</code><br/><i>(Grain, Decimals & Formulas)</i>"]
        R2["⏳ <code>temporal_risk_reviewer</code><br/><i>(SCD2 Sentinels & Range Joins)</i>"]
        R3["🔗 <code>relational_risk_reviewer</code><br/><i>(3NF Normalization & Bridges)</i>"]
        R4["🏗️ <code>refactor_risk_reviewer</code><br/><i>(Table Width & Outriggers)</i>"]
    end

    subgraph PHASE6["4️⃣ Phase 6: Compilation & Handover"]
        C1["🗺️ <code>STTMGenerator</code> (5-Section Mapping)"]
        C2["🏗️ <code>ANSISQLGenerator</code> (ANSI DDL)"]
        C3["📜 <code>DataContractCompiler</code> (ODCS v3.0.0)"]
        C4["🌊 <code>MedallionPipelineGenerator</code> (Bronze/Silver/Gold)"]
        C5["🦆 <code>DuckDBPipelineRunner</code> (In-Memory Verification)"]
    end

    CAPTAIN --> PHASE0
    PHASE0 --> PHASE1
    PHASE1 --> PHASE2
    PHASE2 --> PHASE6
```

---

## 2. Phase 0 Intake Squad & Strict 100% Information Gate

The Intake Phase is governed by **3 specialized micro-agents** enforcing a mathematical **Strict 100% Information Completeness Invariant**:

$$\text{Information Completeness Score} = \sum_{i=1}^5 (\text{Resolved Vector}_i \times 20\%) = 100.0\%$$

```mermaid
flowchart LR
    INPUT["📝 Business Narrative"] --> SCRIBE
    
    subgraph SQUAD["🧭 The Intake Squad Relay"]
        SCRIBE["🔍 <code>semantic_scribe_agent</code><br/>• Word Count Check (≥ 4)<br/>• Gibberish Filter ('asdf')<br/>• Contradiction Check<br/>• DDD Noun-Verb Extraction"]
        
        AUDITOR["⚖️ <code>completeness_auditor_agent</code><br/>• Workload Intent (20%)<br/>• Entity Grain (20%)<br/>• Temporal Policy (20%)<br/>• Lifecycle Funnel (20%)<br/>• Relationship Multiplicity (20%)"]
        
        INTERVIEWER["💬 <code>business_interviewer_agent</code><br/>• 100% Plain English Dialogue<br/>• Consultative Business Discovery<br/>• Zero Database Jargon"]
    end

    SCRIBE --> AUDITOR
    AUDITOR -- "Score < 100% (Hard Block)" --> INTERVIEWER
    INTERVIEWER --> |User Answers| SCRIBE
    AUDITOR -- "Score == 100%" --> PASS["🚀 CERTIFIED READY<br/>(Handoff to Modeler)"]
```

### 📋 The 5 Information Vectors & Natural Discovery Questions:
1. **Workload Intent (20%):** *"How will your team or end-users primarily interact with this system?"* (Dashboards/BI vs Live App/EHR vs Real-time Stream).
2. **Entity Grain (20%):** *"What does your company primarily sell or provide, and what is the primary activity to measure?"* (Product lines vs Subscription renewals vs Clinical care vs Loans).
3. **Temporal Policy (20%):** *"When a customer, store, or patient updates their profile, how should past reports behave?"* (SCD2 History vs In-place Overwrite vs SOX Audit).
4. **Lifecycle Funnel (20%):** *"Does this business workflow involve tracking turnaround time across multiple sequential stages?"* (Multi-stage funnel vs Single event vs Monthly snapshot).
5. **Relationship Multiplicity (20%):** *"In your day-to-day operations, do multiple people share accounts, or can an order involve multiple owners?"* (1:1 / 1:N Standard vs Shared Co-ownership).

---

## 3. The Unified Mandatory Audit Funnel with Human-in-the-Loop (HITL) Gates

Regardless of the entry branch (`NEW_MODEL`, `FEATURE_EVOLUTION`, or `BUG_REMEDIATION`), **every change converges into the exact same Mandatory Audit & Verification Funnel with explicit Human Validation Gates**:

```mermaid
flowchart TD
    subgraph INTAKE["📥 1. Intake Triggers & Human Input"]
        W1["1️⃣ New Data Model<br/>(Business Story Narrative)"]
        W2["2️⃣ New Feature Evolution<br/>(Upstream Codebase / Gap Scan)"]
        W3["3️⃣ Bug / Quality Incident<br/>(Quarantine Alert / Data Drift)"]
    end

    subgraph TRIAGE_DISCOVERY["🔎 2. Triage & Discovery"]
        W1 --> T1["Requirements Triage & 21-Q Classification"]
        W2 --> T2["Folder Scanner & Semantic Gap Matrix"]
        W3 --> T3["Quarantine Diagnostics & Root Cause Analysis"]
        
        T1 --> H1{{"👤 HUMAN GATE 1<br/><b>Business Scope Validation</b><br/><i>(Stakeholder aligns on 21-Q & domain boundaries)</i>"}}
        T2 --> H2{{"👤 HUMAN GATE 2<br/><b>Capability Gap Sign-Off</b><br/><i>(Source engineer confirms missing field backlogs)</i>"}}
        T3 --> H3{{"👤 HUMAN GATE 3<br/><b>Incident Severity Approval</b><br/><i>(Data owner confirms quarantine root-cause)</i>"}}
        
        H1 --> S1["Draft Target Schema & Invariant Contract Spec<br/><i>(Mockup Mode: [AI-GENERATED] tags)</i>"]
        H2 --> S1
        H3 --> S1
    end

    subgraph CONCEPT_REVIEW["🎨 3. Conceptual Design Review"]
        S1 --> H4{{"👤 HUMAN GATE 4<br/><b>Visual ERD & Mockup Review</b><br/><i>(Business user validates Mermaid ERD & formulas)</i>"}}
    end

    subgraph UNIFIED_AUDIT["🛡️ 4. THE MANDATORY UNIFIED AUDIT BLOCK (Zero-Bypass)"]
        H4 --> AC["🧭 Core 4 Risk Review Council (ISO/IEC 25012)<br/>• Financial & Grain Integrity Reviewer<br/>• Temporal & Time-Travel History Reviewer<br/>• Relational Integrity & Decoupling Reviewer<br/>• Refactorability & Conformed Marts Reviewer"]
        
        AC --> H5{{"👤 HUMAN GATE 5<br/><b>Phase 5c Architect Sign-Off</b><br/><i>(Lead Architect signs disposition matrix)</i>"}}
        H5 -- Reject / Needs Refactor --> REF["Architect Refactoring Loop"]
        REF --> AC
        
        H5 -- Certified Approved --> DUCK["🦆 In-Memory DuckDB Pipeline Execution Engine<br/>• Bronze DDL & Seed Verification<br/>• Silver Staging & Quarantine Isolation Proof<br/>• Gold SCD2 Merge & Active View Validation"]
    end

    subgraph PRODUCTION["🚀 5. Production Hand-off"]
        DUCK --> H6{{"👤 HUMAN GATE 6<br/><b>Data Contract Final Signing</b><br/><i>(Data Platform & Business sign SLA contract)</i>"}}
        H6 --> OUT["📦 Production Certified Deliverables<br/>(Visual ERD + ANSI DDL + ODCS Contract + 5-Section STTM + Medallion SQL)"]
    end

    style H1 fill:#fff3cd,stroke:#d39e00,stroke-width:2px
    style H2 fill:#fff3cd,stroke:#d39e00,stroke-width:2px
    style H3 fill:#fff3cd,stroke:#d39e00,stroke-width:2px
    style H4 fill:#fff3cd,stroke:#d39e00,stroke-width:2px
    style H5 fill:#ffc107,stroke:#b27b00,stroke-width:3px
    style H6 fill:#d4edda,stroke:#28a745,stroke-width:2px
```

---

## 4. Standardized 5-Section Source-to-Target Mapping (STTM) Specification

Every generated data model includes a standardized **5-Section STTM Document** ([`docs/SOURCE_TO_TARGET_MAPPING.md`](file:///C:/Coding/VSCode/data-model-architect/docs/SOURCE_TO_TARGET_MAPPING.md)):

```text
## 🏛️ [Table Name] (e.g. dim_customer_scd2 / fact_omnichannel_sales_lines)

### 1. Short Description
Concise plain-English explanation of what this table represents, its business purpose, and its grain.

### 2. Source Tables
List of upstream Bronze raw tables and Silver staging models.

### 3. Destination Table
Gold target table name, target layer, and primary key definition.

### 4. Raw SQL
Production CTE transformation query extracting, transforming, and loading the target table.

### 5. Column Mapping & Business Logic Matrix
| Column Name | Data Type | Nullable? | Plain-English Description | SQL Expression / Transformation Logic |
```

---

## 5. Industry Benchmark Verification Scores

| Test Suite | Coverage | Status | Latency |
| :--- | :--- | :---: | :---: |
| **Full Pytest Suite (`tests/`)** | 37 Unit Tests across all micro-agents, intake scorers, STTM generators, and DuckDB runner | 🟢 **37/37 PASSED (100.0%)** | `0.55s` |
| **DuckDB In-Memory Execution Battery** | Bronze → Silver Quarantine → Gold SCD2 Merges | 🟢 **100% PASSED** | `0.08s` |
| **Strict 100% Hard Gate Tests** | Gibberish rejection, contradiction detection, 20%-80% hard blocks | 🟢 **100% PASSED** | `0.02s` |
