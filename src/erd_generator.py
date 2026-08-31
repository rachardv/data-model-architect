from typing import Dict, Any, List

class VisualMermaidERDGenerator:
    """
    Generates interactive Visual Mermaid Entity-Relationship Diagrams (ERDs)
    with clean entity boxes, column types, and cardinality relationship markers.
    """
    
    @staticmethod
    def generate_erd(domain: str, tables: List[Dict[str, Any]], relationships: List[Dict[str, str]] = None) -> str:
        lines = [
            f"# 🎨 Data Model ERD Blueprint: `{domain.upper()}`",
            "",
            "```mermaid",
            "erDiagram"
        ]
        
        # 1. Add Relationships
        if relationships:
            for rel in relationships:
                p = rel["parent"]
                c = rel["child"]
                lbl = rel["label"]
                lines.append(f'    {p} ||--o{{ {c} : "{lbl}"')
        else:
            # Default star schema relationships
            facts = [t for t in tables if t.get("type") == "FACT"]
            dims = [t for t in tables if t.get("type") == "DIMENSION"]
            for f in facts:
                for d in dims:
                    dn = d["name"]
                    fn = f["name"]
                    lines.append(f'    {dn} ||--o{{ {fn} : "has"')
                    
        lines.append("")
        
        # 2. Add Table Entities
        for t in tables:
            lines.append(f"    {t['name']} {{")
            for col in t.get("columns", []):
                dtype = col.get("type", "VARCHAR").split("(")[0].lower()
                pk = "PK" if col["name"] == t.get("primary_key") else "FK" if "sk" in col["name"] or "id" in col["name"] else ""
                tag = "inferred" if col.get("is_inferred", False) else ""
                lines.append(f"        {dtype:<12} {col['name']:<24} {pk} {tag}".rstrip())
            lines.append("    }")
            lines.append("")
            
        lines.append("```")
        return "\n".join(lines)
