import os
from typing import Optional
from pydantic import BaseModel, Field

def _load_dotenv_file(dotenv_path: str = ".env") -> None:
    """Lightweight .env parser with zero external dependencies."""
    if os.path.exists(dotenv_path):
        try:
            with open(dotenv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

class AppSettings(BaseModel):
    """
    12-Factor Application Configuration for Data Model Architect.
    Loads from environment variables with 'DATA_MODEL_' prefix or standard names.
    """
    output_dir: str = Field(default="docs", description="Base output directory for generated artifacts")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    log_json: bool = Field(default=True, description="Emit structured JSON logs")
    default_dialect: str = Field(default="ansi", description="Target SQL warehouse dialect")
    quality_threshold: float = Field(default=80.0, description="Minimum quality score threshold")
    strict_intake_gate: bool = Field(default=True, description="Enforce 100% completeness gate")
    duckdb_memory_limit: str = Field(default="1GB", description="In-memory DuckDB RAM limit")

    @classmethod
    def load_from_env(cls, dotenv_path: str = ".env") -> "AppSettings":
        _load_dotenv_file(dotenv_path)
        
        output_dir = os.environ.get("DATA_MODEL_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR") or "docs"
        log_level = os.environ.get("DATA_MODEL_LOG_LEVEL") or os.environ.get("LOG_LEVEL") or "INFO"
        
        log_json_raw = os.environ.get("DATA_MODEL_LOG_JSON") or os.environ.get("LOG_JSON")
        log_json = log_json_raw.lower() not in ("0", "false", "no") if log_json_raw is not None else True
        
        default_dialect = os.environ.get("DATA_MODEL_DIALECT") or os.environ.get("DEFAULT_DIALECT") or "ansi"
        
        thresh_raw = os.environ.get("DATA_MODEL_QUALITY_THRESHOLD")
        quality_threshold = float(thresh_raw) if thresh_raw else 80.0
        
        strict_raw = os.environ.get("DATA_MODEL_STRICT_INTAKE")
        strict_intake_gate = strict_raw.lower() not in ("0", "false", "no") if strict_raw is not None else True
        
        duckdb_mem = os.environ.get("DUCKDB_MEMORY_LIMIT") or "1GB"
        
        return cls(
            output_dir=output_dir,
            log_level=log_level.upper(),
            log_json=log_json,
            default_dialect=default_dialect.lower(),
            quality_threshold=quality_threshold,
            strict_intake_gate=strict_intake_gate,
            duckdb_memory_limit=duckdb_mem
        )

# Global settings singleton
settings = AppSettings.load_from_env()
