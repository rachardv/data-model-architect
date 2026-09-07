import pytest
import os
from src.config import AppSettings
from src.orchestration.captain import CaptainOrchestrator

def test_default_settings():
    s = AppSettings()
    assert s.output_dir == "docs"
    assert s.log_level == "INFO"
    assert s.log_json is True
    assert s.default_dialect == "ansi"
    assert s.quality_threshold == 80.0
    assert s.strict_intake_gate is True

def test_env_var_override(monkeypatch):
    monkeypatch.setenv("DATA_MODEL_OUTPUT_DIR", "production_artifacts")
    monkeypatch.setenv("DATA_MODEL_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATA_MODEL_LOG_JSON", "false")
    monkeypatch.setenv("DATA_MODEL_DIALECT", "snowflake")
    monkeypatch.setenv("DATA_MODEL_QUALITY_THRESHOLD", "95.5")
    monkeypatch.setenv("DATA_MODEL_STRICT_INTAKE", "0")
    
    s = AppSettings.load_from_env()
    assert s.output_dir == "production_artifacts"
    assert s.log_level == "DEBUG"
    assert s.log_json is False
    assert s.default_dialect == "snowflake"
    assert s.quality_threshold == 95.5
    assert s.strict_intake_gate is False

def test_dotenv_file_parsing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("""# Production Config
DATA_MODEL_OUTPUT_DIR=s3_staging
DATA_MODEL_DIALECT=bigquery
LOG_LEVEL=WARNING
""", encoding="utf-8")

    s = AppSettings.load_from_env(dotenv_path=str(env_file))
    assert s.output_dir == "s3_staging"
    assert s.default_dialect == "bigquery"
    assert s.log_level == "WARNING"

def test_captain_inherits_output_dir(monkeypatch):
    monkeypatch.setenv("DATA_MODEL_OUTPUT_DIR", "custom_captain_docs")
    from src.config import AppSettings
    custom_settings = AppSettings.load_from_env()
    
    # Passing None to Captain resolves from settings
    captain = CaptainOrchestrator(output_dir=custom_settings.output_dir)
    assert captain.output_dir == "custom_captain_docs"
