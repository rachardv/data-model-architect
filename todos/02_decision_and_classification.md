# 02 - Decision Engine & Architectural Classification

Focus: Kimball Dimensional Models, 3NF OLTP Relational Schemas, Bi-Temporal Engines, Closure Tables, and Chasm Trap Elimination.

---

## Active Tasks & Known Issues

- [x] **Kimball Star Schema Patterns Implementation**
  - Core decision branches for `KIMBALL_STAR_SCD1`, `KIMBALL_STAR_SCD2`, `ACCUMULATING_SNAPSHOT_FACT`, and `PERIODIC_SNAPSHOT_FACT`.

- [x] **Recursive Closure Tables & Multi-Currency Triads**
  - Transitive closure table generation for org charts/BOM and multi-currency fact triad calculation (`amount_tx`, `amount_base`, `amount_usd`).

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
