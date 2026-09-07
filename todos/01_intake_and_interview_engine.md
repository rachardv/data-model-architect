# 01 - Intake & Discovery Interview Engine

Focus: Natural Language Processing (NLP), Semantic Role Labeling (SRL), 5-Vector Completeness, and Stakeholder Discovery Questions.

---

## Active Tasks & Known Issues

- [x] **Dynamic Domain Role Extraction (SRL)**
  - Replaced hardcoded e-commerce/retail templates with deterministic role extraction (`primary_event`, `primary_actor`, `resource_location`, `child_entity`).
  - Added filter for inanimate `-er` nouns (*number*, *buffer*, *tier*).

- [x] **Dynamic Multiple-Choice Options for All 5 Vectors**
  - Generated domain-specific questions and options for `workload_intent`, `entity_grain`, `temporal_policy`, `lifecycle_funnel`, and `relationship_multiplicity`.
  - Added automatic **Kimball Multi-Fact Bus Matrix** recommendation when multiple event nouns exist (*appointments + fees*).

- [ ] **[Architecture] Ambiguous Business Truth: Multi-Stakeholder Semantic Conflict Resolution**
  - **Problem:** Human stakeholders from sales, finance, and product routinely give mutually conflicting definitions for simple metrics (e.g., when an account officially becomes "active": Sales says *"contract signed"*, Product says *"user logged into dashboard"*, Finance says *"first invoice payment cleared"*). The agent cannot compile an unambiguous schema when the underlying business rules contradict one another.
  - **Proposed Architectural Solution:**
    1. **Multi-Perspective Semantic Tagging:** Prevent column overloading. Instead of a single ambiguous `is_active` boolean, sprout explicit namespace columns (e.g. `is_contract_signed`, `is_platform_active`, `is_financially_active`).
    2. **Contradiction Interceptor & Reconciliation Flow:** When contradictory rule sets are parsed during intake, halt execution with `STATUS: AMBIGUOUS_BUSINESS_TRUTH`. Present the conflicting definitions side-by-side and prompt the user to choose:
       - *Option A:* Decouple into separate explicit status timestamps/flags.
       - *Option B:* Designate one department's definition as the primary enterprise standard and others as departmental outriggers.
    3. **Semantic Layer Decoupling:** Auto-generate decoupled metric YAML definitions in dbt Semantic Layer / MetricFlow with explicit `business_owner: sales|finance|product` tags.
  - **Priority:** High / Critical

- [ ] **[Architecture] The Grain Trap: Atomic Enforcement & Proactive User Pushback**
  - **Problem:** Business users frequently state they need high-level aggregated numbers (e.g., *"We track monthly store revenue"*). If an agent models the fact table at the monthly grain, it permanently destroys drill-down capabilities when users inevitably ask to slice by item, customer, or hour. Kimball guidelines explicitly demand modeling at the lowest atomic grain possible, requiring the agent to push back against user answers.
  - **Proposed Architectural Solution:**
    1. **Proactive "Kimball Atomic Grain Pushback" Engine:** When a user requests an aggregated grain (monthly, weekly, or summary rollup), the interviewer intercepts and proactively pushes back:
       > *"You requested a monthly summary grain. Under Kimball design laws, capturing data only at the monthly level permanently prevents drilling into daily, hourly, or product-level details. We recommend modeling the atomic transaction grain, and generating a materialized aggregate rollup view on top."*
    2. **Automated Two-Tier Architecture (Atomic Fact + Aggregate Mart):** Automatically generate:
       - *Base Atomic Fact:* `fact_orders` / `fact_transactions` (lowest atomic operational grain).
       - *Gold Aggregate Rollup Mart:* `agg_monthly_store_revenue` (pre-computed summary for executive dashboards).
    3. **Down-Drill Audit Guardrail:** Reject any data contract or model spec that attempts to place atomic dimensions on a pre-aggregated fact table without an atomic base.
  - **Priority:** High / Critical

- [ ] **Typo & Levenshtein Distance Tolerance for Intake Keywords**
  - **Problem:** Common user typos like `'analzye'` instead of `'analyze'` currently fail keyword detection in `IntakeCompletenessScorer`, artificially lowering completeness scores.
  - **Proposed Solution:** Implement fuzzy keyword matching (Levenshtein distance <= 2) for core intent keywords (`analyze`, `reporting`, `dashboard`, `checkout`).
  - **Priority:** High

- [ ] **Entity Grain Header vs. Summary Disambiguation**
  - **Problem:** A prompt mentioning "appointment slots for offices" can mean either atomic slots (Transaction Fact) or a daily availability summary per office (Periodic Snapshot).
  - **Proposed Solution:** Ensure the `lifecycle_funnel` or `entity_grain` follow-up explicitly clarifies whether the primary reporting unit is the individual slot event or daily office rollup.
  - **Priority:** High

- [ ] **Extract Numerical Business Rules (SLAs, Retries, Cooldowns)**
  - **Problem:** Rules like "applicants can reschedule after 14 days" are recognized generally, but the exact scalar value `14 days` is not structured into the contract or metadata.
  - **Proposed Solution:** Add regex/pattern extractors for temporal constraints (*N days*, *N hours*, *N retries*) to output into `data_contracts`.
  - **Priority:** Medium

---

## Add New Items Below
