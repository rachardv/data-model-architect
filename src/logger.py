import logging
import json
import os
import sys
from datetime import datetime, timezone
import contextvars
import uuid
from typing import Any, Dict, Optional

# Context variable for request correlation/trace ID
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")

class StructuredJSONFormatter(logging.Formatter):
    """
    JSON Formatter emitting RFC 3339 timestamps, trace IDs, and structured extra fields.
    Compatible with Datadog, Splunk, CloudWatch, Google Cloud Logging, and OpenTelemetry collectors.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get() or getattr(record, "trace_id", None)
        }
        
        # Include location info in debug or errors
        if record.levelno >= logging.ERROR or record.levelno <= logging.DEBUG:
            log_entry["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
            
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Merge extra attributes if provided
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry)

def configure_logging(level: Optional[str] = None, json_format: bool = True) -> None:
    """Configures root and application loggers."""
    log_level_str = level or os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    root_logger = logging.getLogger("data_model_architect")
    root_logger.setLevel(log_level)
    root_logger.propagate = False
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if json_format:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"))
        
    root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """Returns a logger namespaced under data_model_architect."""
    return logging.getLogger(f"data_model_architect.{name}")

def set_trace_id(new_trace_id: Optional[str] = None) -> str:
    """Sets the active trace ID for the current async or thread context."""
    tid = new_trace_id or str(uuid.uuid4())
    trace_id_var.set(tid)
    return tid

def get_trace_id() -> str:
    """Gets the active trace ID or creates a new one if unset."""
    tid = trace_id_var.get()
    if not tid:
        tid = set_trace_id()
    return tid

# Initialize logging on module load
configure_logging()
