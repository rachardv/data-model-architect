from typing import Dict, Any, List

class ReviewFinding:
    def __init__(self, reviewer: str, title: str, description: str, impact: str, recommendation: str, severity: str = "HIGH"):
        self.reviewer = reviewer
        self.title = title
        self.description = description
        self.impact = impact
        self.recommendation = recommendation
        self.severity = severity
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "severity": self.severity
        }

class ReviewerCouncil:
    """
    Executes the Core 4 Pure Design Risk Audits on a proposed Data Model.
    """
    
    @staticmethod
    def audit_model(schema_spec: Dict[str, Any]) -> Dict[str, Any]:
        findings: List[ReviewFinding] = []
        tables = schema_spec.get("tables", [])
        temporal_type = schema_spec.get("temporal_strategy", "")
        
        # 1. Financial & Grain Audit
        for t in tables:
            cols = [c["name"].lower() for c in t.get("columns", [])]
            # Check for header-level discount on lineitem grain
            if "item" in t.get("name", "").lower() and "order_discount_amount" in cols:
                findings.append(ReviewFinding(
                    reviewer="financial_risk_reviewer",
                    title="Line-Item Grain Discount Multiplication Risk",
                    description="The order_discount_amount column is placed on an item-grain table.",
                    impact="Summing discounts across line items will double-count discounts by the item count (400%+ inflation).",
                    recommendation="Move order_discount_amount to the order header table; keep only line_discount_amount on item table.",
                    severity="CRITICAL"
                ))
                
        # 2. Temporal & History Audit (Applies to Dimensions)
        for t in tables:
            if t.get("type") == "DIMENSION" and temporal_type in ["SCD2", "BITEMPORAL"]:
                cols = [c["name"].lower() for c in t.get("columns", [])]
                has_valid_to = any("valid_to" in c for c in cols)
                if not has_valid_to:
                    findings.append(ReviewFinding(
                        reviewer="temporal_risk_reviewer",
                        title="Missing SCD2 Upper Validity Bound",
                        description=f"Dimension {t.get('name')} declared as SCD2 historical dimension but lacks valid_to column.",
                        impact="Point-in-time time-travel queries cannot determine when historical states ended.",
                        recommendation="Add scd_valid_from and scd_valid_to TIMESTAMPTZ columns with 9999-12-31 sentinel defaults.",
                        severity="HIGH"
                    ))
                
        # 3. Relational Decoupling Audit
        for t in tables:
            cols = t.get("columns", [])
            if len(cols) > 40:
                findings.append(ReviewFinding(
                    reviewer="relational_risk_reviewer",
                    title="Monolithic Ultra-Wide Table Trapping Volatile Attributes",
                    description=f"Table {t.get('name')} contains {len(cols)} columns across multiple domains.",
                    impact="Volatile attribute changes will trigger massive SCD2 row churn, bloating storage and indexes.",
                    recommendation="Decouple fast-changing attributes into a dedicated mini-dimension or outrigger table.",
                    severity="HIGH"
                ))
                
        # 4. Refactorability & Sprouting Audit
        for t in tables:
            if t.get("type") == "DIMENSION" and not t.get("is_conformed", True):
                findings.append(ReviewFinding(
                    reviewer="refactor_risk_reviewer",
                    title="Siloed Dimension Restricting Multi-Mart Sprouting",
                    description=f"Dimension {t.get('name')} contains domain-specific naming preventing reuse.",
                    impact="Downstream teams will create duplicate dimension silos instead of sharing conformed dimensions.",
                    recommendation="Standardize natural keys and grain into a Kimball Conformed Dimension.",
                    severity="MEDIUM"
                ))
                
        is_clean = len(findings) == 0
        return {
            "status": "APPROVED" if is_clean else "CHANGES_REQUIRED",
            "findings_count": len(findings),
            "findings": [f.to_dict() for f in findings],
            "quality_index": 100.0 if is_clean else max(70.0, 100.0 - (len(findings) * 8.0))
        }
