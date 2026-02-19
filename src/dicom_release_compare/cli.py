from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from dicom_release_compare.config import settings
from dicom_release_compare.models import DiffReport, DiffRun
from dicom_release_compare.pipeline import pipeline_overview


def cmd_doctor() -> None:
    print(f"environment={settings.environment}")
    print(f"postgres_dsn={settings.postgres_dsn}")
    print(f"vector_backend={settings.vector_backend}")
    print(f"llm_provider={settings.llm_provider}, llm_model={settings.llm_model}")
    print(f"embedding_model={settings.embedding_model}")


def cmd_pipeline() -> None:
    for idx, step in enumerate(pipeline_overview(), start=1):
        print(f"{idx}. {step.name}: {step.description}")


def cmd_init_run(base_release: str, target_release: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    report = DiffReport(
        run=DiffRun(
            run_id=f"run_{base_release}_{target_release}",
            base_release=base_release,
            target_release=target_release,
        )
    )
    output.write_text(json.dumps(asdict(report), indent=2, default=str), encoding="utf-8")
    print(f"Wrote bootstrap artifact to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="drc", description="DICOM release compare bootstrap CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Print active configuration")
    sub.add_parser("pipeline", help="List pipeline steps")

    init_run = sub.add_parser("init-run", help="Create an initial diff run artifact")
    init_run.add_argument("base_release")
    init_run.add_argument("target_release")
    init_run.add_argument("--output", default="artifacts/diff.json")

    args = parser.parse_args()

    if args.command == "doctor":
        cmd_doctor()
    elif args.command == "pipeline":
        cmd_pipeline()
    elif args.command == "init-run":
        cmd_init_run(args.base_release, args.target_release, Path(args.output))


if __name__ == "__main__":
    main()
