"""Non-LLM Statistical Column Profiler.

Extracts real distributions, null rates, cardinality ratios, sample values,
and regex pattern matches directly from the database estate.
"""

from typing import Dict, List, Any, Optional
import re
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH

# Standard Governance Regex Patterns
PATTERNS = {
    "UUID_PATTERN": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I),
    "HEX_ID_PATTERN": re.compile(r"^[0-9a-f]{32}$", re.I),
    "EMAIL_PATTERN": re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$"),
    "PHONE_PATTERN": re.compile(r"^\+?[\d\s\(\)-]{7,20}$"),
    "ZIP_PATTERN": re.compile(r"^\d{4,5}(-\d{3,4})?$"),
    "DATE_ISO_PATTERN": re.compile(r"^\d{4}-\d{2}-\d{2}"),
    "NUMERIC_CURRENCY_PATTERN": re.compile(r"^\$?\d+(\.\d{2})?$"),
}


class ColumnProfile(BaseModel):
    table_name: str
    column_name: str
    data_type: str
    total_rows: int
    null_count: int
    null_percentage: float
    distinct_count: int
    cardinality_ratio: float
    is_unique: bool
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    avg_value: Optional[float] = None
    sample_values: List[str] = Field(default_factory=list)
    detected_patterns: List[str] = Field(default_factory=list)
    neighbor_columns: List[str] = Field(default_factory=list)


class EstateProfiler:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or ESTATE_DB_PATH)

    def profile_column(self, table_name: str, column_name: str) -> ColumnProfile:
        """Compute statistical profile for a single column."""
        conn = duckdb.connect(self.db_path, read_only=True)
        
        # Get table schema & neighbors
        cols_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
        neighbors = [c[0] for c in cols_info if c[0] != column_name]
        data_type = next((c[1] for c in cols_info if c[0] == column_name), "UNKNOWN")

        # Basic counts
        stats = conn.execute(f"""
            SELECT 
                COUNT(*) AS total_rows,
                COUNT(*) - COUNT("{column_name}") AS null_count,
                COUNT(DISTINCT "{column_name}") AS distinct_count
            FROM {table_name}
        """).fetchone()

        total_rows = stats[0]
        null_count = stats[1]
        distinct_count = stats[2]
        null_percentage = round((null_count / total_rows * 100.0) if total_rows > 0 else 0.0, 2)
        cardinality_ratio = round((distinct_count / total_rows) if total_rows > 0 else 0.0, 4)
        is_unique = (distinct_count == total_rows) and (null_count == 0)

        # Min, Max, Avg (if numeric)
        min_val = None
        max_val = None
        avg_val = None
        try:
            val_bounds = conn.execute(f"""
                SELECT 
                    CAST(MIN("{column_name}") AS VARCHAR),
                    CAST(MAX("{column_name}") AS VARCHAR)
                FROM {table_name}
            """).fetchone()
            min_val = str(val_bounds[0]) if val_bounds[0] is not None else None
            max_val = str(val_bounds[1]) if val_bounds[1] is not None else None
        except Exception:
            pass

        t_upper = data_type.upper()
        if any(n in t_upper for n in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"]):
            try:
                avg_res = conn.execute(f"SELECT AVG(\"{column_name}\") FROM {table_name}").fetchone()[0]
                avg_val = round(float(avg_res), 2) if avg_res is not None else None
            except Exception:
                pass

        # Samples
        samples_res = conn.execute(f"""
            SELECT DISTINCT CAST("{column_name}" AS VARCHAR)
            FROM {table_name}
            WHERE "{column_name}" IS NOT NULL
            LIMIT 5
        """).fetchall()
        samples = [str(r[0]) for r in samples_res if r[0] is not None]

        # Pattern detection
        detected_patterns = []
        for pat_name, pat_regex in PATTERNS.items():
            matches = sum(1 for s in samples if pat_regex.match(s.strip()))
            if matches >= max(1, len(samples) // 2):
                detected_patterns.append(pat_name)

        return ColumnProfile(
            table_name=table_name,
            column_name=column_name,
            data_type=data_type,
            total_rows=total_rows,
            null_count=null_count,
            null_percentage=null_percentage,
            distinct_count=distinct_count,
            cardinality_ratio=cardinality_ratio,
            is_unique=is_unique,
            min_value=min_val,
            max_value=max_val,
            avg_value=avg_val,
            sample_values=samples,
            detected_patterns=detected_patterns,
            neighbor_columns=neighbors
        )

    def profile_table(self, table_name: str) -> Dict[str, ColumnProfile]:
        """Profile all columns of a table."""
        conn = duckdb.connect(self.db_path, read_only=True)
        cols = [r[0] for r in conn.execute(f"DESCRIBE {table_name}").fetchall()]
        return {col: self.profile_column(table_name, col) for col in cols}
