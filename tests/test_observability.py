import pytest
import json
import logging
from src.logger import configure_logging, get_logger, set_trace_id, get_trace_id, StructuredJSONFormatter
from src.orchestration.captain import CaptainOrchestrator

def test_json_log_formatting():
    formatter = StructuredJSONFormatter()
    set_trace_id("test-trace-12345")
    
    logger = logging.getLogger("test_logger")
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_file.py",
        lno=42,
        msg="Test structured log message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Test structured log message"
    assert parsed["trace_id"] == "test-trace-12345"
    assert "timestamp" in parsed

def test_trace_id_contextvars():
    tid1 = set_trace_id("trace-abc")
    assert get_trace_id() == "trace-abc"
    
    set_trace_id("")
    new_tid = get_trace_id()
    assert len(new_tid) > 10
    assert new_tid != "trace-abc"

def test_captain_emits_structured_logs(caplog):
    custom_trace = "trace-captain-workflow-999"
    captain = CaptainOrchestrator()
    payload = {
        "domain": "observability_test",
        "branch": "NEW_MODEL",
        "narrative": "A user logs into an app and performs actions.",
        "trace_id": custom_trace,
        "usage_params": {
            "is_live_app": True,
            "is_high_frequency_stream": False,
            "needs_history": False,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        }
    }
    
    with caplog.at_level(logging.INFO):
        result = captain.execute_workflow(payload)
        
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert custom_trace in caplog.text
    assert "data_model_architect.captain" in caplog.text
