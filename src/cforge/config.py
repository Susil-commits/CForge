"""ContextForge configuration module."""

from pathlib import Path
import os

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

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "cforge")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
