"""Thread-safe SQLite Disk Cache for LLM responses and real telemetry."""

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from cforge.config import LLM_CACHE_PATH


@dataclass
class CachedResponse:
    cache_key: str
    model: str
    response_text: str
    parsed_json: Optional[Dict[str, Any]]
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    created_at: str


class LLMDiskCache:
    """Persistent disk cache for LLM API calls with real token and cost tracking."""

    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or LLM_CACHE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS llm_cache (
                        cache_key TEXT PRIMARY KEY,
                        model TEXT NOT NULL,
                        prompt_hash TEXT NOT NULL,
                        system_prompt TEXT,
                        user_prompt TEXT,
                        response_text TEXT NOT NULL,
                        parsed_json TEXT,
                        input_tokens INTEGER NOT NULL,
                        output_tokens INTEGER NOT NULL,
                        latency_ms REAL NOT NULL,
                        cost_usd REAL NOT NULL,
                        created_at TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_llm_cache_model 
                    ON llm_cache(model);
                """)
                conn.commit()

    @staticmethod
    def compute_key(model: str, system_prompt: str, user_prompt: str, schema_dict: Optional[Dict[str, Any]] = None) -> str:
        """Compute deterministic SHA-256 cache key from model, prompts, and schema."""
        schema_str = json.dumps(schema_dict, sort_keys=True) if schema_dict else ""
        content = f"{model.strip()}||{system_prompt.strip()}||{user_prompt.strip()}||{schema_str}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[CachedResponse]:
        """Retrieve cached response if available."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM llm_cache WHERE cache_key = ?", (cache_key,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            parsed_data = None
            if row["parsed_json"]:
                try:
                    parsed_data = json.loads(row["parsed_json"])
                except Exception:
                    parsed_data = None

            return CachedResponse(
                cache_key=row["cache_key"],
                model=row["model"],
                response_text=row["response_text"],
                parsed_json=parsed_data,
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                latency_ms=row["latency_ms"],
                cost_usd=row["cost_usd"],
                created_at=row["created_at"]
            )

    def get_by_prompt(self, system_prompt: str, user_prompt: str) -> Optional[CachedResponse]:
        """Retrieve cached response by prompt content if model-specific cache key missed."""
        prompt_hash = hashlib.sha256(f"{system_prompt.strip()}||{user_prompt.strip()}".encode("utf-8")).hexdigest()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM llm_cache WHERE prompt_hash = ? ORDER BY created_at DESC LIMIT 1",
                (prompt_hash,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            parsed_data = None
            if row["parsed_json"]:
                try:
                    parsed_data = json.loads(row["parsed_json"])
                except Exception:
                    parsed_data = None

            return CachedResponse(
                cache_key=row["cache_key"],
                model=row["model"],
                response_text=row["response_text"],
                parsed_json=parsed_data,
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                latency_ms=row["latency_ms"],
                cost_usd=row["cost_usd"],
                created_at=row["created_at"]
            )

    def set(
        self,
        cache_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        parsed_json: Optional[Dict[str, Any]],
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost_usd: float
    ) -> None:
        """Save response and telemetry to disk cache."""
        prompt_hash = hashlib.sha256(f"{system_prompt}||{user_prompt}".encode("utf-8")).hexdigest()
        parsed_str = json.dumps(parsed_json) if parsed_json is not None else None
        now_utc = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO llm_cache 
                    (cache_key, model, prompt_hash, system_prompt, user_prompt, 
                     response_text, parsed_json, input_tokens, output_tokens, 
                     latency_ms, cost_usd, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key, model, prompt_hash, system_prompt, user_prompt,
                        response_text, parsed_str, input_tokens, output_tokens,
                        round(latency_ms, 2), round(cost_usd, 6), now_utc
                    )
                )
                conn.commit()

    def stats(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate total cached calls, tokens, latency, and cost, optionally filtered by model."""
        query = """
            SELECT 
                COUNT(*) as total_entries,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
                COALESCE(AVG(latency_ms), 0.0) as avg_latency_ms
            FROM llm_cache
        """
        params = ()
        if model:
            query += " WHERE model = ?"
            params = (model,)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return {
                "total_entries": row["total_entries"],
                "total_input_tokens": row["total_input_tokens"],
                "total_output_tokens": row["total_output_tokens"],
                "total_tokens": row["total_input_tokens"] + row["total_output_tokens"],
                "total_cost_usd": round(row["total_cost_usd"], 6),
                "avg_latency_ms": round(row["avg_latency_ms"], 2)
            }
