"""ContextForge configuration module."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ESTATE_DB_PATH = DATA_DIR / "estate.duckdb"
METADATA_DB_PATH = DATA_DIR / "metadata.duckdb"
LAKEHOUSE_DIR = DATA_DIR / "lakehouse"
GOLD_LABELS_PATH = DATA_DIR / "gold_labels.csv"
HAND_VERIFIED_LINEAGE_PATH = DATA_DIR / "hand_verified_lineage.json"
BUSINESS_QUESTIONS_PATH = DATA_DIR / "business_questions.json"
INJECTED_DEFECTS_PATH = DATA_DIR / "injected_defects.json"
POLICIES_PATH = PROJECT_ROOT / "src" / "cforge" / "governance" / "policies.yaml"
RESULTS_DIR = PROJECT_ROOT / "results"
BENCHMARK_PATH = RESULTS_DIR / "benchmark.md"
BENCHMARK_JSON_PATH = RESULTS_DIR / "benchmark.json"
LLM_CACHE_PATH = DATA_DIR / "llm_cache.sqlite"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "cforge")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Security, CORS & Governance Authorization
raw_origins = os.getenv(
    "CFORGE_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000"
)
if raw_origins.strip() == "*":
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

STEWARD_ACCESS_TOKEN = os.getenv("STEWARD_ACCESS_TOKEN", "steward-demo-secure")
RATE_LIMIT_CHAT_PER_MIN = int(os.getenv("RATE_LIMIT_CHAT_PER_MIN", "30"))
ENABLE_DUCKDB_EXTERNAL_ACCESS = os.getenv("ENABLE_DUCKDB_EXTERNAL_ACCESS", "false").lower() in ("true", "1")
