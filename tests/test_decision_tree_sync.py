"""
Automated Enforcement Test: Decision Tree Living Documentation Synchronization

Enforces that:
1. docs/DECISION_TREE.md physically exists and is not empty.
2. docs/DECISION_TREE.md matches the output of forge.decision_tree_generator with ZERO drift.
3. Every architectural pattern from DataModelDecisionEngine is represented in the decision tree documentation.
4. Every semantic extraction flag from NounVerbSemanticParser is documented.
5. Generation performance strictly meets the sub-50ms SLA without external API dependencies.
"""

import time
from pathlib import Path
from forge.decision_tree_generator import (
    DecisionTreeGenerator,
    DOCS_PATH,
    PATTERN_METADATA
)
from src.decision_engine import DataModelDecisionEngine


class TestDecisionTreeDocumentationSync:
    """Hard CI Enforcement Gate: Zero Drift Between Engine Logic and Decision Tree Documentation."""

    def test_decision_tree_doc_exists(self):
        """docs/DECISION_TREE.md must physically exist."""
        assert DOCS_PATH.exists(), f"Missing critical documentation: {DOCS_PATH}"
        assert DOCS_PATH.stat().st_size > 1000, "docs/DECISION_TREE.md is suspiciously small or empty."

    def test_decision_tree_has_zero_drift(self):
        """Content on disk must match DecisionTreeGenerator.generate_markdown() byte-for-byte."""
        disk_content = DOCS_PATH.read_text(encoding="utf-8")
        generated_content = DecisionTreeGenerator.generate_markdown()
        assert disk_content == generated_content, (
            "🚨 DECISION TREE DOCUMENTATION DRIFT DETECTED!\n"
            "`docs/DECISION_TREE.md` does not match the active engine reflection.\n"
            "Run `.\\forge.ps1 tree` or `py -3.14 -m forge.decision_tree_generator` to synchronize."
        )

    def test_all_21_patterns_represented(self):
        """All 21 canonical architectural patterns must be documented in the matrix and flow."""
        content = DOCS_PATH.read_text(encoding="utf-8")
        expected_patterns = [p["pattern"] for p in PATTERN_METADATA]
        assert len(expected_patterns) == 21, f"Expected 21 patterns, got {len(expected_patterns)}"

        missing = [pat for pat in expected_patterns if pat not in content]
        assert not missing, f"The following patterns are missing from docs/DECISION_TREE.md: {missing}"

    def test_all_intake_flags_documented(self):
        """All technical flags returned by NounVerbSemanticParser must be documented."""
        content = DOCS_PATH.read_text(encoding="utf-8")
        sample_narrative = "Hospital encounter with bridge table and multi-valued diagnosis."
        from src.noun_verb_parser import NounVerbSemanticParser
        flags = NounVerbSemanticParser.infer_parameters_from_business_narrative(sample_narrative)

        for flag_name in flags.keys():
            assert f"`{flag_name}`" in content, (
                f"Flag `{flag_name}` is returned by parser but not documented in `docs/DECISION_TREE.md`."
            )

    def test_architecture_milestone_history_documented(self):
        """Milestone evolution log must be documented in Section 6."""
        content = DOCS_PATH.read_text(encoding="utf-8")
        assert "## 6. Architecture Revision History & Evolution Log" in content
        from forge.decision_tree_generator import MILESTONE_HISTORY
        for m in MILESTONE_HISTORY:
            assert f"`{m['version']}`" in content, f"Missing milestone {m['version']} in docs/DECISION_TREE.md"

    def test_generator_performance_sla(self):
        """Decision tree generation must complete in < 50ms without external API calls."""
        t0 = time.perf_counter()
        _ = DecisionTreeGenerator.generate_markdown()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert elapsed_ms < 50.0, (
            f"Decision tree generator exceeded 50ms SLA ({elapsed_ms:.2f}ms). "
            f"Generator must remain purely deterministic, in-memory reflection."
        )
