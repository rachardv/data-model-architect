import os
import json
import csv
import re
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

class FolderSchemaScanner:
    """
    Recursively scans directory folders for schema files (.sql, .json, .csv, .py, .ts, .prisma, .yaml, .yml)
    and extracts confirmed source tables, columns, and datatypes.
    Supports multi-table .sql files with comment stripping.
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
                        if isinstance(table_info, list):
                            tables.extend(table_info)
                        else:
                            tables.append(table_info)
                        
        return {
            "status": "SUCCESS",
            "folder_path": folder_path,
            "total_files_scanned": len(tables),
            "tables_found": tables
        }
        
    @classmethod
    def _parse_file(cls, file_path: str, filename: str, ext: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        default_table_name = os.path.splitext(filename)[0]
        columns = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            if ext == ".sql":
                # 1. Strip comments (single-line -- and multi-line /* */)
                cleaned = re.sub(r"--.*?$", "", content, flags=re.MULTILINE)
                cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
                
                # 2. Extract multiple CREATE TABLE statements
                create_table_pattern = re.compile(
                    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*\((.*?)\);",
                    re.IGNORECASE | re.DOTALL
                )
                table_matches = list(create_table_pattern.finditer(cleaned))
                
                if table_matches:
                    parsed_tables = []
                    for match in table_matches:
                        tbl_name = match.group(1).lower()
                        body = match.group(2)
                        tbl_columns = []
                        
                        for line in body.splitlines():
                            clean_line = line.strip().rstrip(",")
                            if not clean_line:
                                continue
                            upper_line = clean_line.upper()
                            if any(upper_line.startswith(k) for k in ["CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK"]):
                                continue
                            col_match = re.match(r"^([a-zA-Z0-9_]+)\s+([A-Za-z0-9_()]+)", clean_line)
                            if col_match:
                                c_name = col_match.group(1).lower()
                                c_type = col_match.group(2).upper()
                                if c_name not in {"create", "table", "constraint", "primary", "key", "foreign", "references"}:
                                    tbl_columns.append({"name": c_name, "type": c_type, "is_inferred": False})
                                    
                        parsed_tables.append({
                            "table_name": tbl_name,
                            "source_file": filename,
                            "columns": tbl_columns
                        })
                    return parsed_tables
                else:
                    # Fallback if no full CREATE TABLE block is closed with semicolon
                    lines = cleaned.splitlines()
                    for line in lines:
                        clean_line = line.strip().rstrip(",")
                        col_match = re.match(r"^([a-zA-Z0-9_]+)\s+([A-Za-z0-9_()]+)", clean_line)
                        if col_match:
                            c_name = col_match.group(1).lower()
                            c_type = col_match.group(2).upper()
                            if c_name not in {"create", "table", "constraint", "primary", "key", "foreign", "references"}:
                                columns.append({"name": c_name, "type": c_type, "is_inferred": False})
                                
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
                field_matches = re.findall(r"([a-zA-Z0-9_]+)\s*:\s*([A-Za-z0-9_\[\]]+)", content)
                for col, dtype in field_matches:
                    columns.append({"name": col.lower(), "type": dtype, "is_inferred": False})
        except Exception as e:
            logger.debug("Failed to parse schema file %s: %s", file_path, e)
            
        return {
            "table_name": default_table_name,
            "source_file": filename,
            "columns": columns
        }
