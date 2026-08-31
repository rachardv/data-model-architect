from typing import Dict, Any, List

class DataContractCompiler:
    """
    Compiles plain-English business rules and invariants into formal Data Contract specifications.
    """
    
    @staticmethod
    def compile_contract(domain: str, rules: List[Dict[str, Any]], freshness_sla: str = "60m") -> str:
        lines = [
            f"# 📋 Enterprise Data Contract Specification: `{domain.upper()}`",
            "",
            "> **Version:** `1.0.0`  ",
            f"> **Freshness SLA Target:** `{freshness_sla}`  ",
            "> **Enforcement:** Hard Database Constraints (`CHECK`) + Pipeline Invariants  ",
            "",
            "---",
            "",
            "## 🛡️ Business Invariants & Contract Rules",
            "",
            "| Rule ID | Invariant Description | Enforcement Type | Constraint Definition |",
            "| :---: | :--- | :---: | :--- |"
        ]
        
        for i, r in enumerate(rules, 1):
            rule_id = f"BR-{i:02d}"
            desc = r.get("description", "")
            etype = r.get("enforcement", "Hard Database CHECK")
            definition = f"`{r.get('definition', '')}`"
            lines.append(f"| **{rule_id}** | {desc} | **{etype}** | {definition} |")
            
        return "\n".join(lines)
