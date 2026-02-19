from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class DiffRun:
    run_id: str
    base_release: str
    target_release: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_version: str = "0.1.0"


@dataclass
class TraceabilityMap:
    old_clause: str
    new_clause: str
    confidence: float
    method: str


@dataclass
class FieldDiff:
    field: str
    old: str | None = None
    new: str | None = None
    impact: str | None = None


@dataclass
class ImpactTags:
    validation_rule_updates: bool = False
    data_dictionary_updates: bool = False
    conformance_statement_review: bool = False


@dataclass
class ChangeItem:
    change_id: str
    part: str
    entity: Literal["clause", "table", "table_row", "attribute", "sop_class"]
    change_type: Literal["added", "removed", "modified", "renumbered", "moved"]
    classification: Literal["Minor", "Clarification", "Technical", "Breaking"]
    score: int
    location_old: str | None = None
    location_new: str | None = None
    field_diffs: list[FieldDiff] = field(default_factory=list)
    impact_tags: ImpactTags = field(default_factory=ImpactTags)

    def __post_init__(self) -> None:
        if self.score < 0 or self.score > 100:
            raise ValueError("score must be between 0 and 100")


@dataclass
class DiffReport:
    run: DiffRun
    traceability: list[TraceabilityMap] = field(default_factory=list)
    changes: list[ChangeItem] = field(default_factory=list)
