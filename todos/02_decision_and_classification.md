# 02 - Decision Engine & Architectural Classification

Focus: Kimball Dimensional Models, 3NF OLTP Relational Schemas, Bi-Temporal Engines, Closure Tables, and Chasm Trap Elimination.

---

## Active Tasks & Known Issues

- [x] **Kimball Star Schema Patterns Implementation**
  - Core decision branches for `KIMBALL_STAR_SCD1`, `KIMBALL_STAR_SCD2`, `ACCUMULATING_SNAPSHOT_FACT`, and `PERIODIC_SNAPSHOT_FACT`.

- [x] **Recursive Closure Tables & Multi-Currency Triads**
  - Transitive closure table generation for org charts/BOM and multi-currency fact triad calculation (`amount_tx`, `amount_base`, `amount_usd`).

- [ ] **[Architecture] Multi-Process Bus Matrix Explosion: Global Conformed Dimension Registry**
  - **Problem:** When a user provides a complex enterprise narrative spanning multiple departments (e.g., ordering $\rightarrow$ fulfillment $\rightarrow$ billing $\rightarrow$ customer service refunds), compiling individual marts in isolation leads to fractured dimensions. The decision engine must enforce a global Conformed Dimension Registry across compilation passes, ensuring `dim_customer`, `dim_product`, `dim_location`, and `dim_date` retain identical surrogate key algorithms, natural keys, and SCD policies across independent fact builds.
  - **Proposed Architectural Solution:**
    1. **Global Conformed Dimension Registry (`ConformedDimensionRegistry`):** A centralized stateful registry that stores and governs canonical dimension schemas, hash algorithms (e.g. `MD5(natural_key || valid_from)`), attribute types, and SCD policies across all workflow passes.
    2. **Bus Matrix Graph Decomposition:** When an intake narrative spans multiple operational processes, automatically decompose the enterprise model into distinct fact tables (`fact_orders`, `fact_fulfillment`, `fact_billing`, `fact_refunds`) linked directly to the canonical dimensions in the registry.
    3. **Drill-Across Contract Consistency:** Guarantee that all fact tables reference the exact same conformed foreign surrogate keys (`customer_sk`, `date_sk`), enabling seamless, multi-mart drill-across queries without key mismatches or join fan-out.
    4. **Registry Collision & Schema Drift Linter:** Halt compilation if an independent mart attempts to redefine an existing conformed dimension with conflicting data types, differing natural keys, or altered SCD policies.
  - **Priority:** High / Critical

- [ ] **Dedicated OLTP 3NF Physical Schema Generator**
  - **Problem:** When `workload_intent` classifies as `OLTP_3NF_RELATIONAL`, the engine currently outputs standard relational tables, but could benefit from explicit PostgreSQL/MySQL foreign key constraints, unique indexes, and audit trigger DDL.
  - **Proposed Solution:** Build a dedicated `OltpRelationalGenerator` that outputs production-grade 3NF normalized DDL with B-tree indexes, cascade rules, and check constraints.
  - **Priority:** High

- [ ] **Automated Chasm Trap & Fan-Out Detector on Generated SQL**
  - **Problem:** When joining two 1-to-many child tables (e.g. `order_items` and `order_payments`) to a shared parent (`orders`), query plans without CTE pre-aggregation cause metric multiplication.
  - **Proposed Solution:** The decision engine should automatically flag any multi-fact drill-across query that lacks CTE pre-aggregation and rewrite it with conformed dimension hashing.
  - **Priority:** High

- [ ] **Polymorphic Event / Factless Coverage Matrix Automation**
  - **Problem:** Promotion coverage (tracking which stores ran a promotion even if no sales happened) requires a Factless Fact Table.
  - **Proposed Solution:** Add explicit classification for marketing coverage matrices and school/event attendance.
  - **Priority:** Medium

---

## Add New Items Below
