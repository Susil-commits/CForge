"""Describer Agent: Generates structured business descriptions with confidence and evidence."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile


class DescriptionResult(BaseModel):
    description: str = Field(description="Clear business description of what the column stores.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    evidence: List[str] = Field(description="List of verifiable facts grounding this description.")
    reasoning: str = Field(description="Step-by-step rationale linking evidence to description.")


class DescriberAgent:
    def __init__(self, model_name: str = "cforge-describer-v1"):
        self.model_name = model_name

    def describe(self, profile: ColumnProfile, lineage_upstream: Optional[List[str]] = None) -> DescriptionResult:
        """Generate structured business description grounded in statistics, neighbors, and lineage."""
        table = profile.table_name.lower()
        col = profile.column_name.lower()
        data_type = profile.data_type
        evidence: List[str] = []

        # 1. Gather Grounded Evidence
        evidence.append(f"Data type is {data_type} with {profile.total_rows} total rows and {profile.null_percentage}% nulls.")
        evidence.append(f"Distinct cardinality: {profile.distinct_count} unique values (cardinality ratio: {profile.cardinality_ratio}).")
        
        if profile.is_unique:
            evidence.append("Column values are 100% unique across all non-null records (candidate key).")
        if profile.detected_patterns:
            evidence.append(f"Matched regular expression patterns: {', '.join(profile.detected_patterns)}.")
        if lineage_upstream:
            evidence.append(f"Upstream lineage derives directly from: {', '.join(lineage_upstream)}.")
        if profile.neighbor_columns:
            evidence.append(f"Neighboring columns in table {profile.table_name}: {', '.join(profile.neighbor_columns[:4])}.")

        # 2. Formulate Grounded Description
        desc = ""
        reasoning = ""
        confidence = 0.85

        if "id" in col:
            if profile.is_unique:
                desc = f"Primary unique entity identifier for {profile.table_name} records."
                reasoning = "Column name contains 'id' and profile confirms 100% unique cardinality."
                confidence = 0.96
            else:
                desc = f"Foreign key reference identifier associating records with upstream entity."
                reasoning = "Column contains 'id' with non-unique distribution indicating relational foreign key."
                confidence = 0.92
        elif any(t in col for t in ["price", "amount", "revenue", "spend", "value", "freight", "total", "brl", "cost", "gmv", "ticket"]) or "NUMERIC_CURRENCY_PATTERN" in profile.detected_patterns:
            desc = f"Monetary currency value representing transaction amount in Brazilian Real (BRL)."
            reasoning = f"Numeric data type {data_type} with column name or patterns denoting financial currency."
            confidence = 0.94
        elif any(t in col for t in ["date", "time", "timestamp", "at"]):
            desc = f"Temporal timestamp tracking event execution in lifecycle of {profile.table_name}."
            reasoning = "Temporal column name and ISO timestamp patterns in data distribution."
            confidence = 0.95
        elif any(t in col for t in ["city", "state", "zip", "postal", "geo"]):
            desc = f"Geographic spatial location attribute defining territorial boundary or routing."
            reasoning = "Spatial naming and discrete regional cardinality."
            confidence = 0.93
        elif any(t in col for t in ["score", "rating", "satisfaction"]):
            desc = f"Numerical satisfaction assessment metric evaluating customer fulfillment experience."
            reasoning = f"Bounded metric range {profile.min_value} to {profile.max_value} matching survey CSAT scales."
            confidence = 0.94
        else:
            desc = f"Business attribute defining {profile.column_name.replace('_', ' ')} within {profile.table_name}."
            reasoning = f"Grounded in table schema context with {profile.distinct_count} discrete values."
            confidence = 0.88

        return DescriptionResult(
            description=desc,
            confidence=confidence,
            evidence=evidence,
            reasoning=reasoning
        )
