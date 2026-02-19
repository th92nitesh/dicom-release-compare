from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineStep:
    name: str
    description: str


PIPELINE_STEPS = [
    PipelineStep("fetch", "Discover release and download official artifacts"),
    PipelineStep("parse", "Parse HTML/CHTML/PDF into canonical structures"),
    PipelineStep("normalize", "Normalize clauses, numbering, table schemas"),
    PipelineStep("align", "Map clauses/tables and detect renumbering"),
    PipelineStep("diff", "Perform deterministic structural/text/table diffs"),
    PipelineStep("semantic", "Apply LLM semantic classification for ambiguous/high-risk items"),
    PipelineStep("score", "Compute technical/breaking risk score and impact tags"),
    PipelineStep("report", "Generate JSON diff, markdown report, audit bundle"),
    PipelineStep("publish", "Commit artifacts and open PR for review"),
]


def pipeline_overview() -> list[PipelineStep]:
    return PIPELINE_STEPS
