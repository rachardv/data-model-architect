from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

class ColumnSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str
    type: str = "VARCHAR(255)"
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True
    default: Optional[str] = None
    is_inferred: bool = False
    masking_policy: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TableSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str
    type: str = "DIMENSION"  # DIMENSION | FACT | FACTLESS_FACT | ACCUMULATING_FACT | PERIODIC_SNAPSHOT | BRIDGE
    grain: Optional[str] = None
    primary_key: Optional[str] = None
    scd_type: Optional[int] = None
    is_conformed: bool = True
    description: Optional[str] = None
    columns: List[ColumnSpec] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["columns"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.columns]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableSpec":
        cols = []
        for c in data.get("columns", []):
            if isinstance(c, dict):
                cols.append(ColumnSpec(**c))
            elif isinstance(c, ColumnSpec):
                cols.append(c)
        table_data = dict(data)
        table_data["columns"] = cols
        return cls(**table_data)


class RelationshipSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    parent: str
    child: str
    label: str = "has"
    cardinality: str = "1:N"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class SchemaSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    domain: str
    tables: List[TableSpec] = Field(default_factory=list)
    relationships: List[RelationshipSpec] = Field(default_factory=list)
    temporal_strategy: str = "SCD2"
    pattern: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "temporal_strategy": self.temporal_strategy,
            "pattern": self.pattern,
            "tables": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.tables],
            "relationships": [r.to_dict() if hasattr(r, "to_dict") else r for r in self.relationships]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaSpec":
        tables = [TableSpec.from_dict(t) if isinstance(t, dict) else t for t in data.get("tables", [])]
        relationships = [RelationshipSpec(**r) if isinstance(r, dict) else r for r in data.get("relationships", [])]
        return cls(
            domain=data.get("domain", "default"),
            temporal_strategy=data.get("temporal_strategy", "SCD2"),
            pattern=data.get("pattern"),
            tables=tables,
            relationships=relationships
        )
