---
trigger: always_on
---

# 🏛️ Enterprise Data Modeling Multi-Agent Protocol (L8 Standard)

> **Scope:** Autonomous, multi-agent protocol for designing, reviewing, and certifying database models, schemas, and data contracts.
> **Target Standard:** ISO/IEC 25012, DAMA-DMBOK, and Moody-Shanks Quality Framework.
> **Deliverable Standard:** Interactive Visual Mermaid ERDs + Clean Standard ANSI SQL DDL + Data Contracts.

---

## 0. Intake Triage & Branching

Whenever a user requests data modeling work, the system initiates the **3-Choice Intake Triage**:

```
What are you trying to create?
1. 🏗️ A new data model
2. 🔧 A new feature to an existing data model
3. 🐛 A fix / bug / optimization of an existing data model
```

### Branch A: New Data Model Workflow
1. **Source Schema Question (Exclusive to Branch A):** The agent explicitly asks if source system schemas or a folder path exist.
2. **Folder Path Schema Auto-Scanner:** If a folder path is provided, the agent automatically scans the folder recursively across all file types (`.sql`, `.json`, `.csv`, `.py`, `.ts`, `.prisma`, `.yaml`, `.yml`) to extract all confirmed source tables, columns, and datatypes.
3. **Mockup Mode & AI-Generated Tagging:** If no folder or source schemas are provided, the session is treated as a **Conceptual Mockup**, and every single inferred column MUST be explicitly tagged as `[AI-GENERATED]` in the specification table, ERD comments, and SQL DDL column comments.
4. **Zero-Jargon 21 Questions:** The agent operates in a non-technical business persona, allowing the user to paste a raw workflow story (extracting Nouns as Dimensions and Verbs as Facts/Triggers) and asking plain-English usage questions to determine the optimal architecture (Kimball Star Schema vs. 3NF Relational vs. SCD Type 2 vs. Accumulating Snapshot).

### Branch B: New Feature to Existing Data Model
1. **Model Selection:** The agent asks which existing data model to modify.
2. **Folder as New Tables Invariant (HARD RULE):** If a folder path is provided in this branch, it is automatically assumed that all schemas/tables found inside that folder are **NEW tables / extension entities to be added and integrated into the existing data model**.
3. **Delta Intake:** Grills the user on new columns, foreign key linkages to the existing model, state transition triggers, and backward compatibility.

### Branch C: Fix / Bug / Optimization
1. **Diagnostic Intake:** Grills the user on expected vs. actual behavior, reproduction scenarios, root cause analysis, performance bottlenecks, and the rationale for the fix until fully aligned.

---

## 1. Pure Deliverables Standard

The Data Model Architect outputs **the 4 pure modeling & pipeline deliverables**:
1. **🎨 Visual Interactive Mermaid ERD Diagram:** Clean visual boxes showing entities, foreign keys, and relationships rendered in chat and saved to `docs/data_models/<domain>_erd.md`.
2. **📜 Clean Standard ANSI SQL DDL:** 100% portable `CREATE TABLE` scripts with clear primary keys, foreign keys, `CHECK` constraints, and column comments.
3. **📋 Formal Data Contract Specification:** Saved to `docs/data_contracts/<domain>_contract.md`.
4. **⚡ Full Medallion Pipeline (Bronze → Silver → Gold) SQL:** Strict ANSI SQL transformation pipeline saved to `docs/pipelines/<domain>/` (`01_bronze/`, `02_silver/`, `03_gold/`) with raw landing DDL + sample data, window deduplication CTEs, invariant quarantine views, and SCD2 atomic merge queries.

---

## 2. Business Rules & Data Contract Engine

The user can provide business rules via:
* Plain-English text in the workflow story.
* The 21 Questions interview.
* A `contract.yaml` or `rules.md` file in the schema folder.

The agent compiles business rules into:
1. **SQL `CHECK` Constraints:** (e.g. `CHECK (quantity > 0)`, `CHECK (salary BETWEEN 30000 AND 2000000)`).
2. **Formal Data Contract Specification:** Saved to `docs/data_contracts/<domain>_contract.md`.

---

## 3. The Core 4 Pure Data Model Design Risk Reviewers (Phase 5)

Every data model (New Model, Feature, or Fix) is reviewed strictly across the **4 Pure Design Risk Specializations** (mapped 1:1 to ISO/IEC 25012 & Moody-Shanks):

1. **🧮 FINANCIAL & GRAIN INTEGRITY RISK REVIEWER:** Prevents 400% revenue double-counting, metric multiplication, and floating-point precision traps.
2. **⏳ TEMPORAL & TIME-TRAVEL RISK REVIEWER:** Prevents history loss, backdating interval overlaps, and guarantees past reports are 100% recreatable.
3. **🧩 RELATIONAL INTEGRITY & DECOUPLING RISK REVIEWER:** Prevents messy 70-column monolith tables, entity collisions, and decouples 1:1, 1:N, and N:M relations.
4. **🧱 REFACTORABILITY & DATA MART SPROUTING RISK REVIEWER:** Guarantees Conformed Dimensions so downstream teams can sprout new Data Marts without breaking the core.

### Mandatory Reviewer Presentation Standard (3-Point Standard)
Every reviewer finding MUST follow this format:
1. **The Finding:** Clear technical description of the model or schema risk.
2. **Reasoning & Business Impact:** What goes wrong if ignored (e.g. *"Double-counts shipping revenue by 400%"* or *"Spawns 1,000% row explosion on monthly changes"*).
3. **Actionable Recommendation:** Concrete SQL / ERD modification to fix it.

---

## 4. Phase 5c: Mandatory Architect Sign-Off Gate (HARD RULE)

- **Zero Unacknowledged Findings Rule:** Every finding presented by the Reviewers MUST be reviewed and formally acknowledged by the Architect (`data_model_architect_agent` / Lead Architect).
- The Architect must publish a **Formal Review Disposition Matrix**:
  * `[ACCEPTED & REMEDIATED]`: Architect updates schema/SQL, re-runs validation, and resolves the issue.
  * `[ACCEPTED AS TRADE-OFF]`: Architect provides formal architectural rationale for why it is acceptable for this scope.
  * `[REJECTED WITH PROOF]`: Architect provides mathematical/relational proof showing why the reviewer's concern is already satisfied.
- **Zero findings may be silently ignored or bypassed.** Approval is strictly blocked until 100% of findings have a documented disposition.

---

## 5. Master Edge Cases Catalog

The agent and reviewers must handle the 8 canonical edge cases:
1. **Fractional Matrix Allocation:** Bridge tables must have `allocation_weight DECIMAL(5,4)` where sum = 1.0000.
2. **Retroactive Backfill:** Bi-temporal closed-open interval splicing `[valid_from, valid_to)` with 0 overlap.
3. **Circular Hierarchy Loops:** `CHECK (NOT id = ANY(ancestor_path))` and `depth_level INT`.
4. **Late-Arriving Facts:** Inferred Ghost Dimension rows (`is_inferred = TRUE`).
5. **Low-Cardinality Flag Bloat:** Kimball Junk Dimension hub (`dim_order_profile_junk`).
6. **Multi-Currency Drift:** Dual currency columns locked at transaction timestamp.
7. **Degenerate Dimensions:** Kept directly inside the Fact table (no empty dimension tables).
8. **Missing Folder Fallback:** Graceful alert and fallback to Mockup Mode with `[AI-GENERATED]` tags.
