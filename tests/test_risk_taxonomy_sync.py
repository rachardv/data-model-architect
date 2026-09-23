"""
Automated Enforcement Test: Anti-Bloat Risk Taxonomy & Documentation Synchronization

Enforces that:
1. Every registered architectural risk in forge.risk_engine is documented in docs/RISK_TAXONOMY.md.
2. Every curated benchmark case and trap in benchmarks/catalog/curated/ is documented in docs/RISK_TAXONOMY.md.
3. Every documented case ID in docs/RISK_TAXONOMY.md exists as a physical YAML file.
4. Docs are never allowed to drift from code. Any unregistered addition fails CI.
"""

import os
import re
from pathlib import Path
from forge.validation_strategy import RiskRegistry
from forge.catalog_loader import BenchmarkCatalogLoader


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = REPO_ROOT / "docs" / "RISK_TAXONOMY.md"
CURATED_CATALOG_DIR = REPO_ROOT / "benchmarks" / "catalog" / "curated"


def _read_documented_risk_ids() -> set[str]:
    """Parse docs/RISK_TAXONOMY.md and extract all backtick-enclosed identifiers in Section 3 table."""
    assert DOCS_PATH.exists(), f"Critical: {DOCS_PATH} does not exist!"
    content = DOCS_PATH.read_text(encoding="utf-8")
    
    # Extract identifiers from the markdown table (e.g. | `RSK-01` | ... or | `CASE-01` | ...)
    table_rows = re.findall(r"^\|\s*`([A-Z0-9_-]+)`\s*\|", content, re.MULTILINE)
    return set(table_rows)


class TestRiskTaxonomyDocumentationSync:
    """Hard CI Enforcement Gate: Zero Drift Between Code and Documentation."""

    def test_all_registered_risks_are_documented(self):
        """Every @register_risk rule in forge/risk_engine.py MUST appear in docs/RISK_TAXONOMY.md."""
        documented_ids = _read_documented_risk_ids()
        code_risk_ids = set(RiskRegistry.list_risks())
        
        unregistered_in_docs = code_risk_ids - documented_ids
        assert not unregistered_in_docs, (
            f"🚨 UNREGISTERED ARCHITECTURAL RISKS DETECTED IN CODE: {unregistered_in_docs}\n"
            f"Anti-Bloat Invariant Violated: You must document these risk rules in "
            f"`docs/RISK_TAXONOMY.md` (Section 3 Master Registry Table) before merging."
        )

    def test_all_curated_benchmark_cases_are_documented(self):
        """Every YAML case in benchmarks/catalog/curated/ MUST appear in docs/RISK_TAXONOMY.md."""
        documented_ids = _read_documented_risk_ids()
        
        yaml_cases = BenchmarkCatalogLoader.load_from_directory(CURATED_CATALOG_DIR)
        code_case_ids = {c.case_id for c in yaml_cases}
        
        unregistered_in_docs = code_case_ids - documented_ids
        assert not unregistered_in_docs, (
            f"🚨 UNREGISTERED BENCHMARK CASES DETECTED IN CATALOG: {unregistered_in_docs}\n"
            f"Anti-Bloat Invariant Violated: You must document these benchmark cases in "
            f"`docs/RISK_TAXONOMY.md` (Section 3 Master Registry Table) before merging."
        )

    def test_documented_cases_physically_exist(self):
        """Every CASE-XX and TRAP-XX in docs/RISK_TAXONOMY.md must physically exist in catalog."""
        documented_ids = _read_documented_risk_ids()
        yaml_cases = BenchmarkCatalogLoader.load_from_directory(CURATED_CATALOG_DIR)
        code_case_ids = {c.case_id for c in yaml_cases}
        
        documented_benchmark_ids = {i for i in documented_ids if i.startswith("CASE-") or i.startswith("TRAP-")}
        phantom_docs = documented_benchmark_ids - code_case_ids
        assert not phantom_docs, (
            f"🚨 PHANTOM BENCHMARKS IN DOCUMENTATION: {phantom_docs}\n"
            f"These cases are documented in `docs/RISK_TAXONOMY.md` but have no physical YAML file "
            f"in `benchmarks/catalog/curated/`."
        )

    def test_risk_taxonomy_document_structure(self):
        """Ensure docs/RISK_TAXONOMY.md contains all 4 mandatory process sections."""
        content = DOCS_PATH.read_text(encoding="utf-8")
        assert "Category 1: Domain Coverage & Semantic Competence Risk (Process A)" in content
        assert "Category 2: Structural & Architectural Defect Risk (Process B)" in content
        assert "Category 3: Computational & Hardware Stress Risk (Process C)" in content
        assert "Category 4: Universal Mathematical Invariant Risk (Process D)" in content
        assert "2. The Anti-Bloat Intake Decision Matrix" in content
        assert "3. Master Risk Registry & Coverage Matrix" in content
        assert "4. Contributor Anti-Bloat Pre-Flight Checklist" in content
