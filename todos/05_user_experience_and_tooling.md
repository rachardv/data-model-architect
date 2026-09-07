# 05 - User Experience, Visualizations & Developer Tooling

Focus: Non-Technical Business UI/CLI, Visual Entity-Relationship Diagrams (ERD), Bus Matrix Visualizers, and Export Tools.

---

## Active Tasks & Known Issues

- [x] **Mermaid ERD Generator**
  - Automated visual ERD generation depicting Star Schemas, Foreign Keys, and Snowflake dimensions.

- [ ] **Interactive Terminal Discovery CLI (Interactive Interview Loop)**
  - **Problem:** Currently, when an intake returns `NEEDS_CLARIFICATION`, the user has to programmatically pass `business_answers: [...]` back into the payload.
  - **Proposed Solution:** Build a rich terminal CLI (`python -m src.cli interview`) that renders interactive prompts, selectable checkboxes/radio buttons, and lets a user talk naturally with the intake engine.
  - **Priority:** High

- [ ] **Enterprise Bus Matrix Grid Visualizer**
  - **Problem:** Business stakeholders love Kimball Bus Matrices (Rows = Business Processes/Facts, Columns = Conformed Dimensions).
  - **Proposed Solution:** Generate a Markdown/HTML table depicting the enterprise bus matrix (which fact tables share which dimensions) as an artifact in every workflow run.
  - **Priority:** High

- [ ] **Web UI / Microservice REST API**
  - **Problem:** Non-developers need a web browser interface to type their prompt and view generated diagrams.
  - **Proposed Solution:** Build a lightweight FastAPI backend + Streamlit or React web UI to expose the model architect engine.
  - **Priority:** Low

---

## Add New Items Below
