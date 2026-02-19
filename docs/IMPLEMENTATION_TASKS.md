# Implementation Tasks and Environment Setup

This document converts the architecture into a concrete execution backlog with tool setup details.

## 0) Repository Bootstrap (done in this PR)
- [x] Python package scaffold (`src/dicom_release_compare`)
- [x] CLI entrypoint (`drc`) with config and pipeline visibility
- [x] Config templates for pipeline, LLM, embeddings, scoring
- [x] Initial domain models for diff run/report
- [x] Initial task + setup documentation

## 1) Infrastructure Setup Tasks

### 1.1 Object Storage (S3/Blob/GCS)
- Create bucket/container: `dicom-release-artifacts-{env}`.
- Enable object versioning + immutable retention policy for audit outputs.
- Configure lifecycle rules:
  - raw downloads: retain 2 years,
  - evidence bundles: retain per regulatory requirement (e.g., 7+ years).
- Configure IAM:
  - `drc-ingestor` write-only raw path,
  - `drc-pipeline` read/write processing paths,
  - `drc-audit-reader` read-only evidence path.

### 1.2 PostgreSQL + pgvector
- Provision PostgreSQL 15+.
- Enable extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Create schemas:
  - `core` (release/part/clause/table entities),
  - `diff` (runs/items/traceability),
  - `audit` (provenance/model/prompt artifacts).
- Enable PITR backups and automated snapshots.

### 1.3 Vector DB
- Option A (recommended initially): pgvector in same Postgres cluster.
- Option B (scale-out): OpenSearch/Pinecone with namespace per release.
- Configure ANN index on `clause.embedding`.

### 1.4 Workflow Engine
- Deploy Argo Workflows or Airflow.
- Define DAG/WorkflowTemplate stages:
  `fetch -> parse -> normalize -> align -> diff -> semantic -> score -> report -> publish`
- Enable retries, backoff, dead-letter handling.

### 1.5 Queue/Event Bus
- Provision SQS/PubSub/Kafka topics:
  - `release.detected`,
  - `part.parse.requested`,
  - `diff.run.completed`,
  - `review.required`.

## 2) Parsing & Canonicalization Tasks
- [ ] Implement release crawler for yearly folders (`YYYYa..e`).
- [ ] Build HTML/CHTML parser preserving clause hierarchy.
- [ ] Build PDF fallback parser and table extractor with confidence scoring.
- [ ] Implement canonical normalizer:
  - heading normalization,
  - tag/VR/VM normalization,
  - table header alias normalization.
- [ ] Persist canonical entities with source offsets/page references.

## 3) Diff Engine Tasks
- [ ] Clause alignment engine (exact + lexical + embeddings + neighborhood).
- [ ] Renumbering detection with weighted bipartite matching.
- [ ] Text diff engine with sentence-level deltas.
- [ ] Table diff engine (row key by tag/name/hash fallback).
- [ ] SOP Class and UID diff module.

## 4) Semantic/LLM Tasks
- [ ] Implement prompt templates as versioned assets.
- [ ] Enforce JSON schema output validation.
- [ ] Add model routing (small model first, premium on uncertainty).
- [ ] Persist prompt hash/model metadata for each semantic decision.

## 5) Impact Scoring and Rules
- [ ] Implement weighted scoring from `configs/scoring.yaml`.
- [ ] Add rule packs:
  - VM tightening,
  - VR change class transitions,
  - Type strengthening,
  - module mandate changes,
  - retired SOP/UId changes.
- [ ] Add calibration workflow using historical release comparisons.

## 6) Output + Audit Tasks
- [ ] Generate `diff.json`, `impact_report.md`, `traceability.csv`, `checklist.md`.
- [ ] Build signed manifest (`manifest.json`) with checksums.
- [ ] Package evidence bundle as immutable release artifact.

## 7) CI/CD Setup Tasks

### GitHub Actions / GitLab / Azure DevOps
- [ ] Add scheduled workflow for release discovery.
- [ ] Add manual workflow dispatch for ad-hoc pair compare.
- [ ] On run completion:
  - commit artifacts to branch `diff/{base}_to_{target}`,
  - open PR with risk summary,
  - request approvals from DICOM domain owners.
- [ ] Enforce gates:
  - schema validation pass,
  - unit tests pass,
  - high-risk diffs reviewed.

## 8) Security / Compliance Tasks
- [ ] Secret management via Vault/KMS/Secrets Manager.
- [ ] Encrypt data in transit and at rest.
- [ ] Add access audit logs to all evidence reads.
- [ ] Add SBOM + container image signing for pipeline services.

## 9) Initial Milestone Plan
- **M1 (2–3 weeks):** Ingestion + canonical parser for Part 03/04 + deterministic table diff.
- **M2 (2–3 weeks):** Full part coverage + renumbering + SOP/UID diff.
- **M3 (2 weeks):** LLM semantic layer + scoring + checklist/report generation.
- **M4 (1–2 weeks):** CI/CD automation + audit bundle + reviewer workflow.

## 10) Dependent Tool Configuration Checklist
- [ ] OpenAI/Azure OpenAI credentials configured (`DRC_LLM_*`).
- [ ] Embedding service configured (`DRC_EMBEDDING_*`).
- [ ] Postgres DSN configured (`DRC_POSTGRES_DSN`).
- [ ] Object storage credentials and bucket configured.
- [ ] Queue endpoints and workflow scheduler credentials configured.
- [ ] Monitoring endpoints configured (OTel collector, Prometheus).

