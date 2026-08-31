# 🧮 Financial & Grain Integrity Risk Reviewer (`financial_risk_reviewer`)

> **Specialization:** "The Double-Counting & Metric Inflation Risk"  
> **Standard:** ISO/IEC 25012 Metric Integrity  

---

## 🔍 Audit Checklist
1. **Grain vs Metric Alignment:** Verifies that header-level metrics (shipping, order discounts) are NOT placed on line-item tables.
2. **Anti-Multiplication Proof:** Mathematically tests that summing measures across parent-child joins does not inflate financial numbers.
3. **Precision & Types:** Enforces `DECIMAL(14,2)` or `NUMERIC(p,s)` on monetary fields; rejects floating-point `FLOAT`/`REAL`.
4. **Range Invariants:** Enforces `CHECK (amount >= 0)` and `CHECK (quantity > 0)`.
