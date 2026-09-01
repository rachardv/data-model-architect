import os
import sys
import json
import time
from typing import Dict, Any, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from decision_engine import DataModelDecisionEngine
from noun_verb_parser import NounVerbSemanticParser

SCENARIOS: List[Dict[str, Any]] = [
    # =========================================================================
    # CATEGORY 1: E-COMMERCE & RETAIL (10 Scenarios)
    # =========================================================================
    {
        "id": 1,
        "category": "E-Commerce & Retail",
        "title": "Omnichannel Sales & Customer Journey",
        "narrative": "A customer browses products online and places an order. The order is fulfilled from a local retail store or shipped from a regional warehouse.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Requires surrogate key separation between online customer profile and store location."
    },
    {
        "id": 2,
        "category": "E-Commerce & Retail",
        "title": "Multi-Stage Order Fulfillment & Delivery Pipeline",
        "narrative": "Tracks an e-commerce order from initial placement, through payment capture, warehouse picking, carrier dispatch, and final doorstep delivery with milestone duration metrics.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Multi-milestone lag tracking requiring role-playing date keys and monotonic timestamp validation."
    },
    {
        "id": 3,
        "category": "E-Commerce & Retail",
        "title": "Daily Warehouse SKU Inventory Snapshots",
        "narrative": "Daily midnight snapshot recording physical stock on hand, allocated reservations, and reorder thresholds across 50 distribution centers.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT",
        "tricky_note": "Semi-additive inventory metrics (cannot SUM across dates; must use AVG or LAST_VALUE)."
    },
    {
        "id": 4,
        "category": "E-Commerce & Retail",
        "title": "High-Churn Customer VIP Tiers & Propensity Scores",
        "narrative": "Retail marketing model where ML models re-score customer churn risk and lifetime value propensity every 24 hours across 5 million active shoppers.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Fast-changing daily ML scores must be decoupled into a Mini-Dimension band to prevent SCD2 table explosion."
    },
    {
        "id": 5,
        "category": "E-Commerce & Retail",
        "title": "Product Returns & Restocking Processing",
        "narrative": "Customer initiates a return authorization, mails back the package, quality inspection checks items, and merchant issues store credit or card refund.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Return pipeline involves multiple stage updates over weeks."
    },
    {
        "id": 6,
        "category": "E-Commerce & Retail",
        "title": "Live Mobile Checkout Cart (OLTP)",
        "narrative": "A high-concurrency microservice handling mobile shopping cart additions, item quantity updates, and temporary item locks during checkout.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "Pure live application requires 3NF normalized tables with row-level locks and zero historical overhead."
    },
    {
        "id": 7,
        "category": "E-Commerce & Retail",
        "title": "Flash Sale Real-Time Clickstream & Add-to-Cart Telemetry",
        "narrative": "Ingesting 50,000 click and add-to-cart events per second during a Black Friday flash sale for real-time traffic monitoring.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "High-throughput append-only time-series partitioning required."
    },
    {
        "id": 8,
        "category": "E-Commerce & Retail",
        "title": "Promotional Coupon Header Discount Allocation",
        "narrative": "Orders apply a $20 order-level coupon across 5 line items. Sales reports must evaluate item-level margins without multiplying the coupon amount.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Header vs line-item grain allocation to prevent 500% discount multiplication."
    },
    {
        "id": 9,
        "category": "E-Commerce & Retail",
        "title": "Multi-Vendor Marketplace Commission Split",
        "narrative": "A single customer purchase contains items from 3 independent sellers, requiring split payouts, platform commission deductions, and sales tax allocation.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Line-item grain fact joined to vendor and customer conformed dimensions."
    },
    {
        "id": 10,
        "category": "E-Commerce & Retail",
        "title": "Customer Loyalty Points Real-Time Ledger",
        "narrative": "Real-time accrual and redemption of reward points where every earn and burn transaction modifies the member's current point balance.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "Strict ACID transactional balance consistency in PostgreSQL."
    },

    # =========================================================================
    # CATEGORY 2: BANKING & FINTECH (10 Scenarios)
    # =========================================================================
    {
        "id": 11,
        "category": "Banking & FinTech",
        "title": "Month-End Depository Account Balance Ledger",
        "narrative": "Monthly snapshot of all retail checking, savings, and certificate of deposit accounts for regulatory liquidity coverage ratio (LCR) reporting.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT",
        "tricky_note": "Preserves dormant zero-activity accounts and marks balances as semi-additive."
    },
    {
        "id": 12,
        "category": "Banking & FinTech",
        "title": "SOX Regulated Financial Ledger with Retroactive Adjustments",
        "narrative": "Financial General Ledger accounting where quarterly audits require reporting the exact ledger state as of past dates, incorporating backdated adjusting journal entries.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": True, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE",
        "tricky_note": "Requires dual-axis time: Valid Time (transaction effective date) + System Time (when entry was posted)."
    },
    {
        "id": 13,
        "category": "Banking & FinTech",
        "title": "Commercial Mortgage Loan Origination Lifecycle",
        "narrative": "Commercial real estate loans progressing through application intake, credit underwriting, appraisal, title search, loan approval, closing, and funding.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Multi-month underwriting pipeline with role-playing dates and duration calculations."
    },
    {
        "id": 14,
        "category": "Banking & FinTech",
        "title": "Real-Time High-Frequency FX Currency Ticks",
        "narrative": "Forex trading platform streaming real-time EUR/USD bid-ask spreads at 10,000 updates per second for quantitative arbitrage algorithms.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "High-throughput append-only time-series with microsecond precision."
    },
    {
        "id": 15,
        "category": "Banking & FinTech",
        "title": "Joint Checking Accounts (Many-to-Many Ownership)",
        "narrative": "Bank checking accounts co-owned by married couples and family trusts, requiring fractional balance attribution and joint statement generation.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Requires a Weighted Bridge Table between account and customer dimensions."
    },
    {
        "id": 16,
        "category": "Banking & FinTech",
        "title": "Credit Card Fraud Ring Detection Network",
        "narrative": "Graph model linking compromised credit cards, common ATM terminal IDs, merchant locations, and shared burner phone numbers to catch organized fraud syndicates.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Relational node & edge tables with bidirectional traversal composite indexing."
    },
    {
        "id": 17,
        "category": "Banking & FinTech",
        "title": "Daily Dynamic Credit Risk Scoring & Delinquency Bands",
        "narrative": "Credit risk monitoring engine updating 10 million borrower FICO tiers, payment delinquency buckets, and probability of default scores every 24 hours.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Shards volatile FICO scores into discrete mini-dimension bands to protect core customer table."
    },
    {
        "id": 18,
        "category": "Banking & FinTech",
        "title": "ATM Cash Dispense Transaction Core (OLTP)",
        "narrative": "Core banking transaction switch processing live ATM withdrawals, PIN authorizations, and ledger balances with sub-second ACID guarantees.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "Strict 3NF ACID transaction model with zero isolation anomalies."
    },
    {
        "id": 19,
        "category": "Banking & FinTech",
        "title": "Wealth Management Portfolio Holdings History",
        "narrative": "Wealth management mart tracking historical stock and bond position balances across client portfolios with full SCD2 point-in-time investor profile history.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "SCD2 point-in-time joining on trade execution date."
    },
    {
        "id": 20,
        "category": "Banking & FinTech",
        "title": "Retroactive Tax Classification Audit Ledger",
        "narrative": "Corporate banking tax ledger where overseas entities receive retroactive tax residency adjustments from government auditors requiring bi-temporal historical queries.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": True, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE",
        "tricky_note": "Bi-temporal interval matching to reconstruct historical corporate tax filings."
    },

    # =========================================================================
    # CATEGORY 3: HEALTHCARE & LIFE SCIENCES (8 Scenarios)
    # =========================================================================
    {
        "id": 21,
        "category": "Healthcare & Life Sciences",
        "title": "Inpatient Hospital Stay & Admission-to-Discharge Journey",
        "narrative": "Tracks an inpatient hospital admission through triage, room transfer, surgery, ICU care, post-op recovery, and final physician discharge.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Multi-stage clinical milestone fact table measuring length-of-stay metrics."
    },
    {
        "id": 22,
        "category": "Healthcare & Life Sciences",
        "title": "Medical Insurance Claims with Multi-Diagnosis Codes",
        "narrative": "Insurance claims where 1 patient claim contains up to 10 distinct primary and secondary ICD-10 diagnosis codes requiring non-duplicated cost analysis.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Multi-valued diagnosis dimension resolved via a Bridge Table."
    },
    {
        "id": 23,
        "category": "Healthcare & Life Sciences",
        "title": "ICU Real-Time Bedside Patient Monitor Vitals",
        "narrative": "High-frequency streaming telemetry collecting heart rate, SpO2, and blood pressure readings every 250 milliseconds from 200 ICU beds.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "Sub-second append-only medical telemetry hypertable."
    },
    {
        "id": 24,
        "category": "Healthcare & Life Sciences",
        "title": "Clinical Trial Phase 1-3 Patient Protocol Progression",
        "narrative": "Pharmaceutical trial tracking patient cohorts across screening, consent, baseline dosing, week 4 evaluation, week 12 evaluation, and study completion.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Accumulating snapshot tracking patient adherence milestones."
    },
    {
        "id": 25,
        "category": "Healthcare & Life Sciences",
        "title": "Monthly Hospital Department Bed Occupancy Snapshot",
        "narrative": "Monthly rollups of bed utilization rates, available staffed beds, and occupancy ratios across oncology, cardiology, and pediatrics departments.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT",
        "tricky_note": "Semi-additive bed occupancy counts rolled up at department grain."
    },
    {
        "id": 26,
        "category": "Healthcare & Life Sciences",
        "title": "Electronic Health Record (EHR) Live Patient Charting (OLTP)",
        "narrative": "Live physician charting system recording doctor notes, medication orders, and allergy alerts during live patient encounters.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "Strict 3NF HIPAA-compliant transactional charting model."
    },
    {
        "id": 27,
        "category": "Healthcare & Life Sciences",
        "title": "Pharmacy Prescription Dispense Mart",
        "narrative": "Retail pharmacy analytics mart tracking medication prescriptions, NDC drug codes, prescriber NPI numbers, and copay amounts with SCD2 patient history.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Conformed patient and physician dimensions with currency copay precision."
    },
    {
        "id": 28,
        "category": "Healthcare & Life Sciences",
        "title": "Daily Patient Readmission Risk Scoring",
        "narrative": "AI predictive model updating 30-day hospital readmission risk percentiles and comorbidity severity scores every morning for all active inpatients.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Volatile daily readmission risk scores sharded into discrete mini-dimensions."
    },

    # =========================================================================
    # CATEGORY 4: SUPPLY CHAIN & LOGISTICS (8 Scenarios)
    # =========================================================================
    {
        "id": 29,
        "category": "Supply Chain & Logistics",
        "title": "Intermodal Freight Shipment Lifecycle",
        "narrative": "Tracking ocean container shipments across booking, port loading, customs clearance, rail interchange, truck dispatch, and final warehouse receiving.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Multi-carrier milestone tracking across multi-week freight journeys."
    },
    {
        "id": 30,
        "category": "Supply Chain & Logistics",
        "title": "Cold-Chain Reefer Truck Temperature IoT Telemetry",
        "narrative": "Streaming IoT sensor telemetry recording refrigerated container temperatures, ambient humidity, and GPS coordinates every 10 seconds to catch spoilage.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "High-velocity time-series IoT data with time-bucket aggregations."
    },
    {
        "id": 31,
        "category": "Supply Chain & Logistics",
        "title": "Daily Distribution Center Pallet Stock Snapshot",
        "narrative": "Nightly snapshot of pallet counts, bin locations, and safety stock levels across 30 regional fulfillment centers.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT",
        "tricky_note": "Semi-additive inventory quantities by warehouse location."
    },
    {
        "id": 32,
        "category": "Supply Chain & Logistics",
        "title": "Manufacturing Recursive Bill of Materials (BOM)",
        "narrative": "Aircraft manufacturing parts explosion where 1 aircraft contains sub-assemblies, which contain modules, which contain individual screws across 12 levels.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Ragged variable-depth hierarchy requiring a Kimball Hierarchy Bridge Table."
    },
    {
        "id": 33,
        "category": "Supply Chain & Logistics",
        "title": "Warehouse Forklift Dispatch Job Engine (OLTP)",
        "narrative": "Live task dispatch system assigning pallet put-away and pick jobs to warehouse forklift operators in real time.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "High-throughput row-locking transactional job queue."
    },
    {
        "id": 34,
        "category": "Supply Chain & Logistics",
        "title": "Supplier Purchase Order Fulfillment & Invoice Variance",
        "narrative": "Procurement analytics comparing purchase order amounts, goods received note (GRN) quantities, and vendor invoice dollar amounts with SCD2 supplier profiles.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Header vs line-item grain procurement variance fact table."
    },
    {
        "id": 35,
        "category": "Supply Chain & Logistics",
        "title": "Daily Carrier On-Time Performance & Reliability Tiers",
        "narrative": "Logistics carrier scorecards updating on-time delivery percentages, claims rates, and gold/silver/bronze service level tiers every 24 hours.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Daily carrier performance scores decoupled into Mini-Dimension tiers."
    },
    {
        "id": 36,
        "category": "Supply Chain & Logistics",
        "title": "Customs Tariff Retroactive Rate Adjustment Audit",
        "narrative": "Import/export customs duty ledger subject to retrospective multi-year government tariff reclassifications requiring bi-temporal point-in-time tax audits.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": True, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE",
        "tricky_note": "Bi-temporal valid time vs transaction time for customs compliance."
    },

    # =========================================================================
    # CATEGORY 5: SAAS & PRODUCT ANALYTICS (8 Scenarios)
    # =========================================================================
    {
        "id": 37,
        "category": "SaaS & Product Analytics",
        "title": "Monthly Recurring Revenue (MRR) Waterfall Snapshot",
        "narrative": "Monthly SaaS financial snapshot breaking down new MRR, expansion MRR, contraction MRR, churned MRR, and net retained ARR across subscription tiers.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT",
        "tricky_note": "Semi-additive recurring revenue metrics across monthly accounting boundaries."
    },
    {
        "id": 38,
        "category": "SaaS & Product Analytics",
        "title": "Enterprise B2B Free Trial to Paid Conversion Lifecycle",
        "narrative": "Tracks trial signups across account creation, team invite sent, feature onboarding completed, demo attended, sales proposal sent, and contract closed.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT",
        "tricky_note": "Multi-milestone sales funnel with role-playing date keys."
    },
    {
        "id": 39,
        "category": "SaaS & Product Analytics",
        "title": "Real-Time User Feature Event Telemetry Stream",
        "narrative": "High-volume clickstream logging button clicks, API calls, and query execution times across 2 million daily active software users.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "Append-only high-velocity time-series event partitions."
    },
    {
        "id": 40,
        "category": "SaaS & Product Analytics",
        "title": "Daily Account Churn Propensity & Health Scores",
        "narrative": "Daily machine learning health score calculation (0-100) and product engagement quadrant updating nightly for 100,000 corporate tenants.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Decouples volatile health scores into Mini-Dimension health quadrants."
    },
    {
        "id": 41,
        "category": "SaaS & Product Analytics",
        "title": "Live User Authentication & Session Token Store (OLTP)",
        "narrative": "Authentication microservice managing active user JWT sessions, token expirations, and password reset rate limits.",
        "params": {
            "is_live_app": True, "is_high_frequency_stream": False, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL",
        "tricky_note": "Low-latency sub-millisecond point reads and writes."
    },
    {
        "id": 42,
        "category": "SaaS & Product Analytics",
        "title": "Seat-Based License Assignment & User Entitlements",
        "narrative": "Subscription license manager mapping purchased seats to employee user accounts with SCD2 plan upgrade and downgrade history.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "SCD Type 2 subscription plan history with open sentinels."
    },
    {
        "id": 43,
        "category": "SaaS & Product Analytics",
        "title": "Retroactive Billing Credit & Invoicing Adjustment Audit",
        "narrative": "SaaS billing engine managing retrospective SLA downtime refund credits and tax true-ups requiring bi-temporal accounting reconciliation.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": True, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE",
        "tricky_note": "Bi-temporal audit capability for subscription billing adjustments."
    },
    {
        "id": 44,
        "category": "SaaS & Product Analytics",
        "title": "Feature Flag Rollout & Experimentation Variant Mart",
        "narrative": "A/B testing analytics evaluating user conversion rates across control and experimental variant cohorts with conformed user dimensions.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Experiment allocation fact table joining to conformed user dimension."
    },

    # =========================================================================
    # CATEGORY 6: TRICKY EDGE CASES (6 Scenarios)
    # =========================================================================
    {
        "id": 45,
        "category": "Tricky Edge Cases",
        "title": "Cascading Corporate Reorg Hierarchy Trap",
        "narrative": "Company reorganizations where a VP transfer threatens to duplicate 500 subordinate employee records in an SCD2 dimension.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Requires a Time-Versioned Hierarchy Bridge to decouple reporting tree from employee dimension."
    },
    {
        "id": 46,
        "category": "Tricky Edge Cases",
        "title": "The 60-Column Monolithic Customer Profile Trap",
        "narrative": "Customer dimension with 60 columns mixing static demographics with daily-changing credit scores and real-time login counts.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True, "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM",
        "tricky_note": "Relational reviewer must mandate decoupling volatile attributes into Mini-Dimensions."
    },
    {
        "id": 47,
        "category": "Tricky Edge Cases",
        "title": "Multi-Hop Cyclic Money Laundering Graph",
        "narrative": "Detecting circular fund transfers across shell company accounts (A -> B -> C -> A) where standard relational queries enter infinite loops.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Relational Node and Edge schema with check constraints preventing self-transfers."
    },
    {
        "id": 48,
        "category": "Tricky Edge Cases",
        "title": "The 6-Location Geography Fact Table Key Bloat",
        "narrative": "Logistics fact table attempting to store billing, shipping, store, warehouse, and supplier addresses directly as 6 separate Foreign Keys.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2",
        "tricky_note": "Refactor reviewer must mandate moving locations to Outriggers attached to primary dimensions."
    },
    {
        "id": 49,
        "category": "Tricky Edge Cases",
        "title": "High-Frequency Crypto Orderbook L3 Depth Stream",
        "narrative": "Cryptocurrency exchange streaming 100,000 orderbook bid/ask cancellations and limit orders per second with nanosecond timestamps.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": True, "needs_history": False,
            "has_retroactive_backdating": False, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE",
        "tricky_note": "Append-only partitioned time-series hypertable with high-throughput compression."
    },
    {
        "id": 50,
        "category": "Tricky Edge Cases",
        "title": "SOX Compliance Multi-Year Retroactive Backdated Journal",
        "narrative": "Multi-year corporate revenue restatement where transactions from 2023 are restated in 2026 under new revenue recognition rules.",
        "params": {
            "is_live_app": False, "is_high_frequency_stream": False, "needs_history": True,
            "has_retroactive_backdating": True, "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False, "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE",
        "tricky_note": "Bi-temporal validity time interval matching against system audit clock."
    }
]

def run_benchmark():
    print("=" * 80)
    print("EXECUTING 50-SCENARIO DATA MODEL AGENT RELIABILITY BENCHMARK")
    print("=" * 80)
    
    results = []
    correct_count = 0
    total_start = time.time()
    category_stats = {}
    
    for sc in SCENARIOS:
        sc_id = sc["id"]
        cat = sc["category"]
        title = sc["title"]
        params = sc["params"]
        expected = sc["expected_pattern"]
        
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0}
        category_stats[cat]["total"] += 1
        
        # 1. Parse Narrative via DDD Noun-Verb Parser
        parsed_grammar = NounVerbSemanticParser.parse_workflow_narrative(sc["narrative"])
        
        # 2. Classify Architecture via 21-Q Decision Engine
        classification = DataModelDecisionEngine.classify_architecture(
            is_live_app=params.get("is_live_app", False),
            is_high_frequency_stream=params.get("is_high_frequency_stream", False),
            needs_history=params.get("needs_history", True),
            has_retroactive_backdating=params.get("has_retroactive_backdating", False),
            has_multi_stage_milestones=params.get("has_multi_stage_milestones", False),
            is_periodic_state_rollup=params.get("is_periodic_state_rollup", False),
            has_high_churn_ml_scores=params.get("has_high_churn_ml_scores", False)
        )
        
        actual_pattern = classification["pattern"]
        is_match = (actual_pattern == expected)
        
        if is_match:
            correct_count += 1
            category_stats[cat]["correct"] += 1
            status_icon = "PASS"
        else:
            status_icon = "FAIL"
            
        results.append({
            "id": sc_id,
            "category": cat,
            "title": title,
            "expected_pattern": expected,
            "actual_pattern": actual_pattern,
            "schema_type": classification["schema_type"],
            "temporal_strategy": classification["temporal"],
            "nouns_extracted": parsed_grammar["dimensions_nouns"],
            "verbs_extracted": parsed_grammar["facts_verbs"],
            "status": "PASS" if is_match else "FAIL",
            "tricky_note": sc["tricky_note"]
        })
        
        print(f"[{sc_id:02d}/50] {status_icon:<4} | {cat:<24} | {title:<40} -> Actual: {actual_pattern}")

    total_duration = time.time() - total_start
    accuracy_pct = (correct_count / len(SCENARIOS)) * 100.0
    
    print("\n" + "=" * 80)
    print(f"BENCHMARK SUMMARY: {correct_count}/{len(SCENARIOS)} PASSED ({accuracy_pct:.1f}% Accuracy)")
    print(f"Total Execution Time: {total_duration:.2f} seconds ({(total_duration/len(SCENARIOS))*1000:.1f}ms per scenario)")
    print("=" * 80)
    
    print("\nCATEGORY BREAKDOWN:")
    for cat, stats in category_stats.items():
        cat_acc = (stats["correct"] / stats["total"]) * 100.0
        print(f"  * {cat:<26}: {stats['correct']}/{stats['total']} ({cat_acc:.1f}%)")
        
    # Save Report Artifact
    report_data = {
        "summary": {
            "total_scenarios": len(SCENARIOS),
            "passed": correct_count,
            "failed": len(SCENARIOS) - correct_count,
            "accuracy_percentage": accuracy_pct,
            "duration_seconds": total_duration,
            "avg_latency_ms": (total_duration / len(SCENARIOS)) * 1000
        },
        "category_breakdown": category_stats,
        "results": results
    }
    
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(docs_dir, exist_ok=True)
    report_path = os.path.join(docs_dir, "BENCHMARK_50_SCENARIOS_RESULTS.json")
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved machine-readable results to: {report_path}")
    
    return report_data

if __name__ == "__main__":
    run_benchmark()
