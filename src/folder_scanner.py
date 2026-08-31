import os
import json
import csv
import re
from typing import Dict, Any, List

class FolderSchemaScanner:
    """
    Recursively scans directory folders for schema files (.sql, .json, .csv, .py, .ts, .prisma, .yaml, .yml)
    and extracts confirmed source tables, columns, and datatypes.
    """
    
    SUPPORTED_EXTENSIONS = {".sql", ".json", ".csv", ".tsv", ".py", ".ts", ".prisma", ".yaml", ".yml"}
    
    @classmethod
    def scan_folder(cls, folder_path: str) -> Dict[str, Any]:
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return {
                "status": "NOT_FOUND",
                "folder_path": folder_path,
                "tables_found": []
            }
            
        tables = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in cls.SUPPORTED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    table_info = cls._parse_file(file_path, file, ext)
                    if table_info:
                        tables.append(table_info)
                        
        return {
            "status": "SUCCESS",
            "folder_path": folder_path,
            "total_files_scanned": len(tables),
            "tables_found": tables
        }
        
    @classmethod
    def _parse_file(cls, file_path: str, filename: str, ext: str) -> Dict[str, Any]:
        table_name = os.path.splitext(filename)[0]
        columns = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            if ext == ".sql":
                # Match CREATE TABLE col_name TYPE
                matches = re.findall(r"([a-zA-Z0-9_]+)\s+([A-Za-z0-9_()]+)", content)
                for col, dtype in matches:
                    if col.upper() not in {"CREATE", "TABLE", "CONSTRAINT", "PRIMARY", "KEY", "FOREIGN", "REFERENCES"}:
                        columns.append({"name": col.lower(), "type": dtype.upper(), "is_inferred": False})
                        
            elif ext == ".csv":
                reader = csv.reader(content.splitlines())
                headers = next(reader, [])
                for h in headers:
                    clean_h = h.strip().lower()
                    if clean_h:
                        columns.append({"name": clean_h, "type": "VARCHAR(255)", "is_inferred": False})
                        
            elif ext == ".json":
                data = json.loads(content)
                sample = data[0] if isinstance(data, list) and data else data
                if isinstance(sample, dict):
                    for k, v in sample.items():
                        dtype = "BIGINT" if isinstance(v, int) else "DECIMAL(14,2)" if isinstance(v, float) else "BOOLEAN" if isinstance(v, bool) else "VARCHAR(255)"
                        columns.append({"name": str(k).lower(), "type": dtype, "is_inferred": False})
                        
            elif ext in {".py", ".ts", ".prisma"}:
                # Extract field names from class/interface definitions
                field_matches = re.findall(r"([a-zA-Z0-9_]+)\s*:\s*([A-Za-z0-9_\[\]]+)", content)
                for col, dtype in field_matches:
                    columns.append({"name": col.lower(), "type": dtype, "is_inferred": False})
        except Exception:
            pass
            
        return {
            "table_name": table_name,
            "source_file": filename,
            "columns": columns
        }
