from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment/.env (if exported)."""

    environment: str
    storage_backend: str
    artifact_bucket: str
    postgres_dsn: str
    vector_backend: str
    llm_provider: str
    llm_model: str
    llm_temperature: float
    embedding_provider: str
    embedding_model: str



def load_settings() -> Settings:
    return Settings(
        environment=os.getenv("DRC_ENVIRONMENT", "dev"),
        storage_backend=os.getenv("DRC_STORAGE_BACKEND", "s3"),
        artifact_bucket=os.getenv("DRC_ARTIFACT_BUCKET", "dicom-release-artifacts"),
        postgres_dsn=os.getenv("DRC_POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/drc"),
        vector_backend=os.getenv("DRC_VECTOR_BACKEND", "pgvector"),
        llm_provider=os.getenv("DRC_LLM_PROVIDER", "openai"),
        llm_model=os.getenv("DRC_LLM_MODEL", "gpt-5"),
        llm_temperature=float(os.getenv("DRC_LLM_TEMPERATURE", "0.1")),
        embedding_provider=os.getenv("DRC_EMBEDDING_PROVIDER", "local"),
        embedding_model=os.getenv("DRC_EMBEDDING_MODEL", "bge-m3"),
    )


settings = load_settings()
