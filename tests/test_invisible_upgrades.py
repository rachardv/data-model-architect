import pytest
import duckdb
from src.ddl_generator import ANSISQLGenerator
from src.decision_engine import DataModelDecisionEngine
from src.sttm_generator import STTMGenerator
from src.medallion_generator import MedallionPipelineGenerator
from src.orchestration.captain import CaptainOrchestrator

def test_point_in_time_fact_join():
    # 1. Test STTM SQL generation
    pit_join = STTMGenerator.generate_point_in_time_fact_join(
        fact_alias="f",
        dim_table_name="dim_customer",
        dim_alias="c",
        join_key="customer_id",
        timestamp_col="order_timestamp"
    )
    assert "LEFT JOIN gold.dim_customer c" in pit_join
    assert "f.customer_id = c.customer_id" in pit_join
    assert "f.order_timestamp >= c.scd_valid_from" in pit_join
    assert "f.order_timestamp < c.scd_valid_to" in pit_join

    # 2. Test Medallion Gold Layer generation with PIT join enabled
    sample_schema = {
        "tables": [
            {
                "name": "dim_retail_customer_core",
                "type": "DIMENSION",
                "columns": [
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "customer_id", "type": "VARCHAR(64)"},
                    {"name": "customer_name", "type": "VARCHAR(255)"},
                    {"name": "scd_valid_from", "type": "TIMESTAMPTZ"},
                    {"name": "scd_valid_to", "type": "TIMESTAMPTZ"}
                ],
                "primary_key": "customer_sk"
            },
            {
                "name": "fact_retail_orders",
                "type": "FACT",
                "columns": [
                    {"name": "order_id", "type": "BIGINT"},
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)"}
                ],
                "primary_key": "order_id"
            }
        ]
    }
    gold_sql = MedallionPipelineGenerator.generate_gold_layer(
        domain="retail",
        target_schema=sample_schema,
        use_point_in_time_join=True
    )
    fact_sql = gold_sql["fact_retail_orders"]
    assert "Point-in-Time Range Join for Late-Arriving Fact Handling" in fact_sql
    assert "o.order_timestamp >= c.scd_valid_from" in fact_sql
    assert "o.order_timestamp < c.scd_valid_to" in fact_sql

def test_role_playing_views_generation():
    # 1. Fact table with multiple date role keys
    fact_table = {
        "name": "fact_shipments",
        "type": "FACT",
        "columns": [
            {"name": "shipment_id", "type": "BIGINT"},
            {"name": "order_date_sk", "type": "INT"},
            {"name": "shipped_date_sk", "type": "INT"},
            {"name": "delivery_date_sk", "type": "INT"}
        ]
    }
    views = ANSISQLGenerator.generate_role_playing_views(fact_table, base_dimension_name="dim_calendar_date")
    assert len(views) == 3
    assert "CREATE OR REPLACE VIEW v_order_date AS SELECT * FROM dim_calendar_date;" in views
    assert "CREATE OR REPLACE VIEW v_shipped_date AS SELECT * FROM dim_calendar_date;" in views
    assert "CREATE OR REPLACE VIEW v_delivery_date AS SELECT * FROM dim_calendar_date;" in views

    # 2. Fact table with single date key should not generate role-playing views
    fact_single_date = {
        "name": "fact_simple",
        "type": "FACT",
        "columns": [
            {"name": "event_id", "type": "BIGINT"},
            {"name": "order_date_sk", "type": "INT"}
        ]
    }
    views_single = ANSISQLGenerator.generate_role_playing_views(fact_single_date, base_dimension_name="dim_calendar_date")
    assert len(views_single) == 0

def test_factless_fact_coverage_generation():
    # 1. Decision Engine classification
    arch = DataModelDecisionEngine.classify_architecture(
        is_live_app=False,
        is_high_frequency_stream=False,
        needs_history=False,
        has_retroactive_backdating=False,
        has_multi_stage_milestones=False,
        is_periodic_state_rollup=False,
        has_high_churn_ml_scores=False,
        is_factless_event=True
    )
    assert arch["pattern"] == "FACTLESS_FACT_COVERAGE"
    assert arch["storage"] == "Kimball Star Schema"
    assert arch["schema_type"] == "Factless Event / Coverage Matrix"

    # 2. Captain Autonomous Factory Execution
    captain = CaptainOrchestrator()
    req = {
        "domain": "conference",
        "branch": "NEW_MODEL",
        "narrative": "Tracks attendee attendance across conference events.",
        "usage_params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": False,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False,
            "is_factless_event": True
        }
    }
    result = captain.execute_workflow(req)
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert result["architecture_pattern"] == "FACTLESS_FACT_COVERAGE"
    
    # Verify DDL contains factless fact coverage table
    ddl_map = result["generated_sql"]
    assert "fact_conference_attendance_coverage" in ddl_map
    factless_ddl = ddl_map["fact_conference_attendance_coverage"]
    
    # Must have composite PK and zero monetary/amount metrics
    assert "PRIMARY KEY (attendee_sk, event_sk, date_sk)" in factless_ddl
    assert "amount" not in factless_ddl.lower()
    assert "usd" not in factless_ddl.lower()

def test_duckdb_execution_of_role_playing_and_factless_fact():
    con = duckdb.connect(database=":memory:")
    
    # 1. Create base date dimension
    con.execute("""
        CREATE TABLE dim_calendar_date (
            date_sk INT PRIMARY KEY,
            calendar_date DATE,
            year INT,
            month INT,
            quarter INT
        );
        INSERT INTO dim_calendar_date VALUES 
            (20260101, '2026-01-01', 2026, 1, 1),
            (20260105, '2026-01-05', 2026, 1, 1),
            (20260110, '2026-01-10', 2026, 1, 1);
    """)
    
    # 2. Generate and execute Role-Playing Views in DuckDB
    fact_table = {
        "name": "fact_orders",
        "type": "FACT",
        "columns": [
            {"name": "order_id", "type": "BIGINT"},
            {"name": "order_date_sk", "type": "INT"},
            {"name": "shipped_date_sk", "type": "INT"}
        ]
    }
    views = ANSISQLGenerator.generate_role_playing_views(fact_table, base_dimension_name="dim_calendar_date")
    for view_sql in views:
        con.execute(view_sql)
        
    # Verify views exist and are queryable
    order_date_count = con.execute("SELECT COUNT(*) FROM v_order_date").fetchone()[0]
    shipped_date_count = con.execute("SELECT COUNT(*) FROM v_shipped_date").fetchone()[0]
    assert order_date_count == 3
    assert shipped_date_count == 3
    
    # 3. Create Factless Fact Table in DuckDB
    con.execute("""
        CREATE TABLE fact_student_attendance (
            student_sk BIGINT NOT NULL,
            course_sk BIGINT NOT NULL,
            date_sk INT NOT NULL,
            PRIMARY KEY (student_sk, course_sk, date_sk)
        );
        INSERT INTO fact_student_attendance VALUES 
            (101, 501, 20260101),
            (101, 502, 20260105),
            (102, 501, 20260101);
    """)
    
    # Query joining factless fact table to role-playing view
    res = con.execute("""
        SELECT f.student_sk, d.calendar_date 
        FROM fact_student_attendance f
        JOIN v_order_date d ON f.date_sk = d.date_sk
        ORDER BY f.student_sk, d.calendar_date;
    """).fetchall()
    
    assert len(res) == 3
    assert res[0][0] == 101
    assert str(res[0][1]) == "2026-01-01"
