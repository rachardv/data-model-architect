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
