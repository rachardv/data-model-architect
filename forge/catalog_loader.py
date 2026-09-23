import os
import glob
import json
import yaml
from typing import Dict, Any, List, Optional
from pydantic import ValidationError
from forge.benchmark_catalog import (
    PredefinedBenchmarkCase,
    VerificationQuery,
    register_benchmark_case,
    clear_registered_benchmark_cases,
    get_predefined_benchmark_catalog
)
from src.logger import get_logger

logger = get_logger("catalog_loader")

class BenchmarkCatalogLoader:
    """
    Declarative Auto-Discovery Loader for Predefined Benchmark Cases.
    Recursively scans directory trees for YAML/JSON specifications, validates them
    against Pydantic schemas, and registers them into the runtime benchmark catalog.
    """

    SUPPORTED_EXTENSIONS = (".yaml", ".yml", ".json")

    @classmethod
    def load_case_file(cls, file_path: str) -> PredefinedBenchmarkCase:
        """
        Loads, parses, and validates a single benchmark case specification file.
        Sets source_file metadata on the instantiated case.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Benchmark case file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}' for benchmark case: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if ext in (".yaml", ".yml"):
                    raw_data = yaml.safe_load(f)
                else:
                    raw_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Syntax error parsing benchmark case file '{file_path}': {e}") from e

        if not isinstance(raw_data, dict):
            raise ValueError(f"Invalid benchmark case structure in '{file_path}': Expected a dictionary, got {type(raw_data).__name__}")

        raw_data["source_file"] = os.path.abspath(file_path)
        
        # Auto-infer workload_type from file path / trap flag if not explicitly declared
        if "workload_type" not in raw_data:
            if raw_data.get("is_intentional_trap") or "trap" in file_path.lower() or "guardrail" in file_path.lower():
                raw_data["workload_type"] = "TRAP"
            elif "oltp" in file_path.lower():
                raw_data["workload_type"] = "OLTP"
            elif "streaming" in file_path.lower():
                raw_data["workload_type"] = "STREAMING"
            elif "lakehouse" in file_path.lower():
                raw_data["workload_type"] = "LAKEHOUSE"
            else:
                raw_data["workload_type"] = "OLAP"

        try:
            case = PredefinedBenchmarkCase(**raw_data)
            return case
        except ValidationError as ve:
            raise ValueError(f"Schema validation error in benchmark case '{file_path}':\n{ve}") from ve

    @classmethod
    def load_from_directory(
        cls,
        dir_path: str = "benchmarks/catalog",
        register: bool = True,
        clear_existing: bool = False,
        strict: bool = True
    ) -> List[PredefinedBenchmarkCase]:
        """
        Recursively scans a directory for .yaml, .yml, and .json benchmark case files.
        Optionally registers discovered cases into the runtime catalog.
        
        Args:
            dir_path: Directory path to scan recursively.
            register: Whether to register cases into the global runtime catalog.
            clear_existing: Whether to clear previously registered cases before registering.
            strict: If True, raises immediately on any invalid file; if False, logs warnings and continues.
        """
        if not os.path.exists(dir_path):
            logger.warning(f"Benchmark catalog directory does not exist: {dir_path}")
            return []

        if clear_existing:
            clear_registered_benchmark_cases()

        discovered_cases: List[PredefinedBenchmarkCase] = []
        pattern = os.path.join(dir_path, "**", "*")
        all_files = glob.glob(pattern, recursive=True)
        case_files = sorted([f for f in all_files if os.path.isfile(f) and f.lower().endswith(cls.SUPPORTED_EXTENSIONS)])

        logger.info(f"Discovered {len(case_files)} potential benchmark case file(s) in '{dir_path}'")

        for fpath in case_files:
            try:
                case = cls.load_case_file(fpath)
                discovered_cases.append(case)
                if register:
                    register_benchmark_case(case)
                logger.debug(f"Successfully loaded benchmark case [{case.case_id}] from {fpath}")
            except Exception as e:
                logger.error(f"Failed to load benchmark case from '{fpath}': {e}")
                if strict:
                    raise

        logger.info(f"Loaded and validated {len(discovered_cases)} benchmark case(s) from '{dir_path}'")
        return discovered_cases

    @classmethod
    def filter_cases(
        cls,
        cases: List[PredefinedBenchmarkCase],
        tags: Optional[List[str]] = None,
        hazard_category: Optional[str] = None,
        case_ids: Optional[List[str]] = None,
        workload_type: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[PredefinedBenchmarkCase]:
        """
        Filters a list of benchmark cases by tags, hazard category, case IDs, workload type, or domain.
        """
        filtered = cases
        if case_ids:
            target_ids = set(c.upper() for c in case_ids)
            filtered = [c for c in filtered if c.case_id.upper() in target_ids]
        if hazard_category:
            filtered = [c for c in filtered if c.hazard_category.upper() == hazard_category.upper()]
        if workload_type:
            target_workload = workload_type.strip().upper()
            if target_workload in ["TRAP", "TRAPS"]:
                filtered = [c for c in filtered if c.is_intentional_trap or c.workload_type.upper() in ["TRAP", "TRAPS"]]
            else:
                filtered = [c for c in filtered if c.workload_type.upper() == target_workload]
        if domain:
            target_domain = domain.strip().lower()
            filtered = [c for c in filtered if c.domain.lower() == target_domain or target_domain in c.domain.lower()]
        if tags:
            req_tags = set(t.lower() for t in tags)
            filtered = [c for c in filtered if req_tags.issubset(set(t.lower() for t in c.tags))]
        return filtered

    @classmethod
    def list_catalog_summary(cls, cases: Optional[List[PredefinedBenchmarkCase]] = None) -> List[Dict[str, Any]]:
        """
        Returns a human-readable list of summaries for all provided or registered cases.
        """
        target_cases = cases if cases is not None else get_predefined_benchmark_catalog()
        summaries = []
        for c in target_cases:
            summaries.append({
                "case_id": c.case_id,
                "name": c.name,
                "domain": c.domain,
                "workload_type": c.workload_type,
                "hazard_category": c.hazard_category,
                "is_intentional_trap": c.is_intentional_trap,
                "expected_status": c.expected_status,
                "query_count": len(c.verification_queries),
                "citation": c.citation,
                "tags": c.tags,
                "source_file": c.source_file
            })
        return summaries
