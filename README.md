# DICOM Release Compare: Enterprise Automation Architecture

This repository defines an implementable, enterprise-grade architecture for comparing full DICOM standard releases (e.g., `2024e` → `2026a`) and generating machine-readable + audit-ready impact outputs for downstream validator updates.

---

## 1) High-Level Architecture

### Goals
- Compare **all DICOM Parts** (Part 01–20+ and future parts).
- Detect:
  - structural changes (sections/tables added, removed, moved, renumbered),
  - textual changes,
  - table-level semantic changes (IODs, Modules, Attributes, VR/VM, Type),
  - SOP Class add/retire/UID definition updates,
  - impacts on validation logic and conformance statements.
- Produce:
  - versioned JSON diff artifacts,
  - human-readable Markdown/PDF impact reports,
  - classification (`Minor`, `Clarification`, `Technical`, `Breaking`),
  - old→new clause traceability for audits.

### Architecture Pattern
Use a **hybrid deterministic + AI pipeline**:
1. Deterministic parsing + canonicalization for reliable extraction.
2. Rule-based diff engines for high-confidence structured changes.
3. Embedding + RAG + LLM semantic layer for nuance/intent classification.
4. Provenance-first storage for auditability and reproducibility.

---

## 2) Component Diagram (Textual)

```text
[Release Fetcher]
    |
    v
[Ingestion Orchestrator] --(events)--> [Workflow Engine (Airflow/Argo)]
    |                                          |
    |                                          +--> [OCR/PDF Parser Workers]
    |                                          +--> [HTML/CHTML Parser Workers]
    |                                          +--> [Table Extractor Workers]
    |                                          +--> [Normalization Workers]
    |                                          +--> [Diff Engine Workers]
    |                                          +--> [LLM Semantic Workers]
    |                                          +--> [Report Generator]
    v
[Raw Artifact Store (S3/GCS/Azure Blob)]
    |
    v
[Canonical Document Store (Postgres + JSONB)] <--> [Vector DB (pgvector/OpenSearch/Pinecone)]
    |
    v
[Rule Catalog + Scoring Engine]
    |
    v
[Versioned Diff Store + Trace Graph]
    |
    +--> [Impact API]
    +--> [Markdown/PDF Report Artifact]
    +--> [GitOps Output Repo / PR Bot]
    +--> [Audit Evidence Package]
```

---

## 3) Processing Pipeline (Step-by-Step)

1. **Release Discovery**
   - Poll `https://dicom.nema.org/medical/dicom/` yearly folder naming pattern (`YYYYa..e`).
   - Detect new releases and enqueue comparison jobs (e.g., last validated vs latest).

2. **Acquisition + Integrity**
   - Download all target sources (`pdf`, `html`, `chtml`, optionally `docx/odt`).
   - Store with SHA-256 checksum, timestamp, source URL, MIME type.

3. **Multi-Source Parsing Strategy**
   - Prefer `html/chtml` for structure fidelity.
   - Fallback to PDF parsing for sections/tables absent in HTML.
   - For each Part, produce canonical entities:
     - `Clause`, `Paragraph`, `Table`, `TableRow`, `Attribute`, `UID/SOPClass`.

4. **Canonical Normalization**
   - Normalize whitespace, bullets, Unicode, numbering variants, table cell wrapping.
   - Canonicalize DICOM attribute notation: `(gggg,eeee)`, VR, VM, Type.
   - Build section hierarchy paths and stable hash signatures.

5. **Deterministic Alignment**
   - Match same Part old/new.
   - Clause matching using hybrid:
     - exact IDs (if stable),
     - heading lexical similarity,
     - embedding similarity,
     - structural neighborhood (parent/children),
     - Hungarian assignment for global best mapping.
   - Output `matched`, `added`, `removed`, `renumbered` clause sets.

6. **Structured Table Diff**
   - Parse table schema by semantic headers (`Attribute Name`, `Tag`, `VR`, `VM`, `Type`, `Description`, etc.).
   - Compare rows by deterministic keys (Tag first, fallback normalized attribute name).
   - Detect row add/remove/update and field-level changes (VR/VM/Type/Req status).

7. **Semantic Text Diff (AI-assisted)**
   - For changed paragraphs and unmatched clauses, run LLM with strict JSON schema output.
   - Classify change intent: clarification vs normative behavior change.

8. **Impact Classification**
   - Rule engine + model fusion computes severity score and class.
   - Examples:
     - VM narrowing, Type tightening, SOP deprecation → likely `Breaking`.
     - wording-only clarifications with no constraints change → `Clarification`.

9. **Traceability Graph Build**
   - Store old clause ↔ new clause mappings with confidence + evidence spans.
   - Persist provenance: parser version, model version, prompt hash, extraction method.

10. **Output Generation**
   - JSON diff package for systems.
   - Markdown/PDF impact report with executive summary + detailed per-part evidence.
   - Auto-generated validation checklist and Jira ticket seeds.

11. **CI/CD + Governance**
   - Pipeline runs in CI on schedule/manual trigger.
   - Commit artifacts to Git branch; open PR for review/signoff.

---

## 4) Recommended Tech Stack

### Parsing / NLP / AI
- PDF: `pdfplumber` + `PyMuPDF` (+ `camelot`/`tabula` for tables).
- HTML parsing: `lxml`, `BeautifulSoup4`.
- Structured NLP: `spaCy` custom patterns for DICOM terms.
- Embeddings:
  - preferred: **bge-m3** or **e5-large-v2** (good for retrieval + semantic matching),
  - enterprise alternative: managed embedding APIs if policy requires.
- LLM:
  - primary: high-accuracy reasoning model for semantic diff/classification,
  - optional smaller model for low-risk triage.

### Data / Storage
- Object store: S3/GCS/Azure Blob.
- Relational + JSON: PostgreSQL (JSONB).
- Vector index: `pgvector` (simpler ops) or OpenSearch vector engine (larger scale).
- Graph traceability (optional): Neo4j for audit lineage queries.

### Orchestration / Infra
- Workflow: Argo Workflows or Apache Airflow.
- Compute: Kubernetes jobs (autoscaled worker pools).
- Eventing: SQS/PubSub/Kafka.
- API + report service: FastAPI.

### MLOps / Governance
- Model registry: MLflow or managed model catalog.
- Prompt/version tracking: store prompt template IDs and hashes in DB.
- Observability: OpenTelemetry + Prometheus + Grafana.

---

## 5) Data Model for Differences

Core entities:
- `release` (`id`, `label`, `published_at`, `source_uri`, `checksum_manifest`)
- `document_part` (`release_id`, `part_no`, `source_type`, `content_hash`)
- `clause` (`part_no`, `clause_id`, `title`, `path`, `text`, `embedding`, `hash`)
- `table` (`table_id`, `part_no`, `caption`, `schema_signature`, `location`)
- `table_row` (`table_id`, `row_key`, `cells_json`, `norm_hash`)
- `diff_run` (`base_release`, `target_release`, `pipeline_version`, `status`)
- `diff_item` (`entity_type`, `change_type`, `old_ref`, `new_ref`, `severity`, `score`)
- `trace_map` (`old_clause_ref`, `new_clause_ref`, `confidence`, `method`)
- `impact_tag` (`diff_item_id`, `validation_rules`, `data_dictionary`, `conformance_review`)
- `evidence` (`diff_item_id`, `source_span_old`, `source_span_new`, `prompt_hash`, `model_id`)

---

## 6) Example JSON Output Format

```json
{
  "diff_run": {
    "id": "run_2024e_2026a_001",
    "base_release": "2024e",
    "target_release": "2026a",
    "generated_at": "2026-02-19T12:00:00Z",
    "pipeline_version": "v1.4.2"
  },
  "summary": {
    "parts_compared": 22,
    "clauses_added": 48,
    "clauses_removed": 19,
    "clauses_renumbered": 132,
    "table_changes": 287,
    "sop_classes_added": 5,
    "sop_classes_retired": 2,
    "breaking_changes": 14
  },
  "changes": [
    {
      "id": "chg_part03_tbl_C.8.12-7_row_45",
      "part": "03",
      "entity": "table_row",
      "location_old": "C.8.12.4/Table C.8.12-7/Row(Tag=0018,9311)",
      "location_new": "C.8.13.1/Table C.8.13-2/Row(Tag=0018,9311)",
      "traceability": {
        "old_clause": "C.8.12.4",
        "new_clause": "C.8.13.1",
        "mapping_confidence": 0.93,
        "mapping_method": "heading+embedding+table_key"
      },
      "change_type": "modified",
      "field_diffs": [
        {"field": "VM", "old": "1-n", "new": "1", "impact": "constraint_tightened"},
        {"field": "Type", "old": "3", "new": "2", "impact": "requirement_strengthened"}
      ],
      "semantic_assessment": {
        "classification": "Breaking",
        "rationale": "Multiplicity reduced and attribute requirement tightened.",
        "llm_confidence": 0.89
      },
      "impact_tags": {
        "validation_rule_updates": true,
        "data_dictionary_updates": true,
        "conformance_statement_review": true
      },
      "evidence": {
        "old_text_span": "...",
        "new_text_span": "...",
        "source_docs": ["part03.pdf", "part03.html"]
      }
    }
  ]
}
```

---

## 7) Prompt Engineering Strategy (Semantic Diff)

Principles:
- Deterministic pre-filtering first; only ambiguous/high-impact cases go to LLM.
- Force strict JSON schema output with required fields.
- Include **only minimal context** (old clause, new clause, neighboring heading, parsed table row deltas).
- Include classification rubric in prompt (Minor/Clarification/Technical/Breaking).
- Use low temperature for consistency.

### Recommended LLM Settings
- Semantic diff extraction: `temperature=0.0` to `0.2`.
- Rationale expansion (report prose): `temperature=0.2` to `0.4`.
- Max tokens constrained per item to reduce cost.

### Prompt Template

```text
SYSTEM:
You are a DICOM standards change analyst. Output valid JSON only.
Classify changes according to this rubric:
- Minor: editorial/non-normative formatting.
- Clarification: wording improved, no constraint or behavior change.
- Technical: normative behavior changed but backward compatibility likely manageable.
- Breaking: validation behavior or interoperability can fail without updates.

USER:
Compare OLD vs NEW content from DICOM Part {part_no}.
OLD CLAUSE: {old_clause_id} - {old_title}
NEW CLAUSE: {new_clause_id} - {new_title}
OLD TEXT:
{old_text}
NEW TEXT:
{new_text}
STRUCTURED DELTAS:
{table_or_attribute_deltas_json}

Return JSON with fields:
{
  "classification": "Minor|Clarification|Technical|Breaking",
  "confidence": 0.0-1.0,
  "normative_change": true|false,
  "validation_logic_impact": true|false,
  "data_dictionary_impact": true|false,
  "conformance_impact": true|false,
  "rationale": "short explanation",
  "recommended_actions": ["..."]
}
```

---

## 8) PDF Chunking Strategy for Embeddings

Chunk by document semantics, not fixed tokens only:
1. Split by Part → section headings (`1`, `1.1`, `A.1`, `C.7.6.1`, etc.).
2. Keep tables as separate chunks with table metadata.
3. Within long clauses, chunk to ~400–900 tokens with 10–15% overlap.
4. Attach metadata:
   - `release`, `part`, `clause_id`, `heading_path`, `table_id`, `page_range`, `normative_flag`.
5. Store parent-child links (chunk → clause → part).

Why: improves retrieval precision and renumbering resilience.

---

## 9) Table Comparison Algorithm (Implementable)

1. Detect table boundaries and parse rows/cells.
2. Normalize header aliases:
   - `Attribute Name`, `Attribute`, `Name` → `attribute_name`
   - `Tag`/`Attribute Tag` → `tag`
   - `VR`, `VM`, `Type`, `Description` standardized.
3. Build row key:
   - primary: `tag` if valid DICOM tag,
   - secondary: normalized `attribute_name`,
   - tertiary: composite hash of significant cells.
4. Align rows old/new using key + similarity fallback.
5. Compute field-level diff map.
6. Apply domain rules:
   - VM narrowed (e.g., `1-n`→`1`) => higher severity,
   - Type strengthened (`3`→`2` or `2`→`1`) => higher severity,
   - VR changed => likely technical/breaking,
   - attribute removed from required module => critical review.
7. Emit structured diff item with confidence and rationale.

---

## 10) Method to Detect VM/VR/Cardinality Changes

Parsing rules:
- VR regex: `^[A-Z]{2}$`.
- VM parser supports ranges (`1`, `1-n`, `2-2n`, `1-3`, `1,3`, etc.).
- Convert VM expression to normalized interval model:
  - lower bound,
  - upper bound (`inf` allowed),
  - multiplicity pattern (`exact`, `range`, `step`).

Impact logic:
- If new allowed set ⊂ old allowed set => **tightened** (higher risk).
- If new allowed set ⊃ old allowed set => relaxed (usually non-breaking).
- VR changed from text-like to binary-like or numeric class shift => potential parser/validator impact.

---

## 11) Strategy for IOD Definition Diffs

For each IOD/module table:
1. Extract module inclusion matrix and attribute table.
2. Compare module presence and usage constraints.
3. Detect attribute-level Type/VM/VR/Conditional statement changes.
4. Parse conditional expressions ("Required if...") and compare normalized logic AST where possible.
5. Score impact:
   - new mandatory module/attribute: high,
   - removed required attribute: high,
   - conditional logic change: medium-high,
   - description-only edits: low.

---

## 12) Clause Renumbering Detection Strategy

Use multi-signal matching model:
- Heading similarity (BM25 + embeddings).
- Paragraph signature similarity (MinHash/SimHash).
- Table signature overlap.
- Structural position similarity (parent/child neighborhood).

Then solve matching with weighted bipartite optimization:
- cost = 1 - weighted_similarity.
- threshold for accepted mapping (e.g., >0.82).
- produce `renumbered` mapping with confidence.

This separates actual removals/additions from renumbering-only moves.

---

## 13) Scoring System for Breaking Change Detection

Example weighted score (0–100):
- `+35` Type strengthened (`3→2`, `2→1`, `1C→1` when condition broadens)
- `+30` VM tightened (domain reduction)
- `+25` VR changed
- `+25` SOP Class retired / UID semantic change
- `+20` module made mandatory
- `+15` normative statement changed (shall/shall not/required)
- `+10` clause moved without semantic change (low)
- `-20` purely editorial evidence

Classification:
- `0–19`: Minor
- `20–39`: Clarification
- `40–69`: Technical
- `70–100`: Breaking

Use calibration set from prior known release deltas for threshold tuning.

---

## 14) Regulatory Audit Traceability Strategy

Store immutable evidence package per diff run:
- Source artifact checksums + URLs.
- Parser version/container digest.
- Model ID/version + prompt template hash.
- Deterministic diff outputs + LLM outputs + confidence.
- Reviewer approvals and timestamped signoffs.

Generate audit bundle:
- `manifest.json` (hashes + metadata),
- `diff.json`,
- `impact_report.md/pdf`,
- `traceability.csv` (old clause → new clause),
- signed attestation.

This supports FDA/CE quality system traceability expectations.

---

## 15) CI/CD Integration Model

### Git-based workflow
1. Scheduled pipeline checks for new DICOM release.
2. On detection, create branch: `diff/{base}_to_{target}`.
3. Run full pipeline in CI (GitHub Actions/GitLab CI/Azure DevOps).
4. Commit generated artifacts:
   - `artifacts/{run_id}/diff.json`
   - `artifacts/{run_id}/impact_report.md`
   - `artifacts/{run_id}/traceability.csv`
   - `artifacts/{run_id}/checklist.md`
5. Auto-open PR with summary counts and risk highlights.
6. Require domain reviewer approvals before merge.

### Pipeline stages
- `fetch` → `parse` → `normalize` → `diff` → `semantic-classify` → `report` → `publish`.

---

## 16) Cost Optimization Strategy

- **Tiered analysis:** deterministic-only for unchanged/high-confidence trivial deltas.
- LLM only for:
  - ambiguous clause mappings,
  - high-impact structured changes,
  - report narrative synthesis.
- Cache embeddings and clause hashes; skip reprocessing unchanged content.
- Use small model first-pass classifier; escalate uncertain cases to premium model.
- Batch embedding requests and parallelize table extraction workers.
- Maintain token budgets by prompt trimming and schema-locked outputs.

---

## 17) Risks and Mitigations

- Parsing errors in complex tables:
  - Mitigation: multi-parser consensus + confidence flags + manual review queue.
- LLM hallucination:
  - Mitigation: no free-form extraction; require evidence-linked JSON only.
- Renumbering false positives:
  - Mitigation: ensemble matching + threshold + reviewer approval for low confidence.
- Drift in classification over time:
  - Mitigation: benchmark suite from historical release pairs.
- Regulatory defensibility:
  - Mitigation: immutable provenance, signed manifests, reproducible containers.

---

## 18) Hybrid Classical + AI Blueprint (Recommended)

- **Classical:** deterministic parsing, canonical schemas, rule-based diff and scoring.
- **AI:** semantic equivalence, ambiguity resolution, impact rationale.
- Decision policy:
  - if deterministic confidence > threshold, skip AI;
  - else invoke AI and attach evidence + confidence.

This gives enterprise reliability while leveraging semantic understanding.

---

## 19) Python Pseudo-code (End-to-End)

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Clause:
    id: str
    title: str
    text: str
    path: str
    embedding: List[float]


def run_diff(base_release: str, target_release: str) -> Dict[str, Any]:
    base_docs = ingest_release(base_release)
    target_docs = ingest_release(target_release)

    base_parts = parse_and_normalize(base_docs)
    target_parts = parse_and_normalize(target_docs)

    all_changes = []
    trace_map = []

    for part_no in union_part_numbers(base_parts, target_parts):
        old = base_parts.get(part_no, {})
        new = target_parts.get(part_no, {})

        clause_map = align_clauses(old["clauses"], new["clauses"])  # includes renumbering detection
        trace_map.extend(clause_map.trace)

        text_changes = diff_text_clauses(old["clauses"], new["clauses"], clause_map)
        table_changes = diff_tables(old["tables"], new["tables"], clause_map)
        sop_changes = diff_sop_classes(old.get("sops", []), new.get("sops", []))

        structured = text_changes + table_changes + sop_changes

        for chg in structured:
            risk = rule_based_risk_score(chg)
            if needs_semantic_review(chg, risk):
                semantic = llm_semantic_classify(chg)
                chg.update(semantic)
            else:
                chg["classification"] = map_score_to_class(risk)
                chg["confidence"] = 0.95

            chg["impact_tags"] = {
                "validation_rule_updates": infer_validation_impact(chg),
                "data_dictionary_updates": infer_dictionary_impact(chg),
                "conformance_statement_review": infer_conformance_impact(chg),
            }
            all_changes.append(chg)

    result = build_output(base_release, target_release, all_changes, trace_map)
    write_json_artifact(result)
    write_markdown_report(result)
    write_validation_checklist(result)
    return result
```

### Table diff pseudo-code

```python
def diff_tables(old_tables, new_tables, clause_map):
    changes = []
    table_pairs = align_tables(old_tables, new_tables, clause_map)

    for old_t, new_t in table_pairs:
        old_rows = index_rows(old_t.rows)  # by tag/name/hash
        new_rows = index_rows(new_t.rows)

        for key in union_keys(old_rows, new_rows):
            o = old_rows.get(key)
            n = new_rows.get(key)
            if o and not n:
                changes.append(make_change("removed", o, None))
            elif n and not o:
                changes.append(make_change("added", None, n))
            else:
                field_diffs = compare_fields(o, n, ["vr", "vm", "type", "description"])
                if field_diffs:
                    changes.append(make_change("modified", o, n, field_diffs))

    return changes
```

### VM/VR specific detection pseudo-code

```python
def vm_vr_impact(old_row, new_row):
    impact = []
    if old_row.vr != new_row.vr:
        impact.append({"kind": "vr_changed", "severity": "high"})

    old_vm = parse_vm(old_row.vm)
    new_vm = parse_vm(new_row.vm)
    if new_vm.is_subset_of(old_vm):
        impact.append({"kind": "vm_tightened", "severity": "high"})
    elif old_vm.is_subset_of(new_vm):
        impact.append({"kind": "vm_relaxed", "severity": "low"})

    return impact
```

---

## 20) Auto-Generated Release Validation Checklist Strategy

Generate checklist items from `impact_tags` and `classification`:
- For each `Breaking/Technical` change:
  - create validator test case updates,
  - create data dictionary migration tasks,
  - create conformance statement review tasks.
- Group by Part, modality, and business system owner.

Example checklist sections:
- [ ] Update parser rules for changed VR/VM in Part 03.
- [ ] Revalidate SOP Class whitelist for retired UIDs.
- [ ] Update conformance templates for new mandatory modules.
- [ ] Run regression suite against golden DICOM datasets.

Checklist can be emitted as Markdown and as Jira/ADO CSV import.

---

## 21) Implementation Notes

- Start with historical backfill (`2024e`→`2025a..2026a`) to tune thresholds.
- Build a gold standard benchmark set from manually reviewed diffs.
- Enforce schema contracts on every stage to avoid silent data corruption.
- Keep deterministic and LLM-derived fields separate for compliance reviews.

This architecture is designed for production-grade DICOM release governance with full traceability, scalable processing, and AI-assisted semantic precision.
