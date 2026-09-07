from src.logger import get_logger
logger = get_logger('reviewer_council')
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
    Includes Multi-Currency FX Triad and JSONB Polymorphic Column Audits.
    """
    
    @staticmethod
    def audit_model(schema_spec: Dict[str, Any]) -> Dict[str, Any]:
        findings: List[ReviewFinding] = []
        tables = schema_spec.get("tables", [])
        temporal_type = schema_spec.get("temporal_strategy", "")
        is_multi_currency = schema_spec.get("is_multi_currency", False)
        
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
            
            # Check for multi-currency FX triad compliance
            if t.get("type") == "FACT" and is_multi_currency:
                has_fx_rate = any("exchange_rate" in c or "fx_rate" in c for c in cols)
                has_currency = any("currency" in c for c in cols)
                if not (has_fx_rate and has_currency):
                    findings.append(ReviewFinding(
                        reviewer="financial_risk_reviewer",
                        title="Multi-Currency FX Conversion Distortion Hazard",
                        description=f"Fact table {t.get('name')} handles international transactions but lacks exchange_rate or currency_code triad columns.",
                        impact="Summing amounts across diverse currencies without normalized exchange rates will produce severely distorted financial totals.",
                        recommendation="Implement Kimball Multi-Currency Fact Triad (amount_local, currency_code, exchange_rate_to_target, amount_target).",
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
            # Exempt valid JSONB / VARIANT semi-structured polymorphic attributes from flat scalar width limits
            non_json_cols = [c for c in cols if c.get("type", "").upper() not in ["JSONB", "VARIANT", "RECORD"]]
            if len(non_json_cols) > 40:
                findings.append(ReviewFinding(
                    reviewer="relational_risk_reviewer",
                    title="Monolithic Ultra-Wide Table Trapping Volatile Attributes",
                    description=f"Table {t.get('name')} contains {len(non_json_cols)} scalar columns across multiple domains.",
                    impact="Volatile attribute changes will trigger massive SCD2 row churn, bloating storage and indexes.",
                    recommendation="Decouple fast-changing attributes into a dedicated mini-dimension, outrigger, or semi-structured JSONB column.",
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
                
        # Final Council Consensus
        passed = all(f.severity != "CRITICAL" for f in findings)
        status = "APPROVED" if passed else "CHANGES_REQUIRED"
        return {
            "status": status,
            "passed": passed,
            "findings_count": len(findings),
            "finding_count": len(findings),
            "findings": [f.to_dict() for f in findings]
        }
