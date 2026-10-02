"""Quality Proposer Agent: Proposes data quality validation rules grounded in column stats."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile


class SuggestedRule(BaseModel):
    rule_type: str = Field(description="Type: NOT_NULL, UNIQUE, RANGE_CHECK, PATTERN_MATCH, REFERENTIAL_INTEGRITY.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule arguments and thresholds.")
    severity: str = Field(description="Enforcement severity: ERROR or WARNING.")
    confidence: float = Field(ge=0.0, le=1.0, description="Proposal confidence score.")
    rationale: str = Field(description="Mathematical and contextual justification for the rule.")


class QualityProposalResult(BaseModel):
    column_name: str
    suggested_rules: List[SuggestedRule]
    confidence: float
    evidence: List[str]


class QualityProposerAgent:
    def __init__(self, model_name: str = "cforge-quality-proposer-v1"):
        self.model_name = model_name

    def propose_rules(self, profile: ColumnProfile) -> QualityProposalResult:
        """Propose automated data quality checks based on distribution statistics."""
        rules: List[SuggestedRule] = []
        evidence: List[str] = []

        # 1. NOT NULL check
        if profile.null_count == 0 and profile.total_rows > 0:
            rules.append(SuggestedRule(
                rule_type="NOT_NULL",
                parameters={"column": profile.column_name},
                severity="ERROR",
                confidence=0.99,
                rationale=f"Zero null values observed across all {profile.total_rows} records."
            ))
            evidence.append("Null percentage is 0.0%.")

        # 2. UNIQUE check
        if profile.is_unique:
            rules.append(SuggestedRule(
                rule_type="UNIQUE",
                parameters={"column": profile.column_name},
                severity="ERROR",
                confidence=0.98,
                rationale="Column exhibits 100% cardinality ratio with no duplicates."
            ))
            evidence.append(f"Distinct count equals total rows ({profile.distinct_count}).")

        # 3. Numeric RANGE_CHECK
        if profile.avg_value is not None and profile.min_value is not None and profile.max_value is not None:
            try:
                min_f = float(profile.min_value)
                max_f = float(profile.max_value)
                buffer_low = min_f if min_f >= 0 else min_f * 1.1
                buffer_high = max_f * 1.5
                rules.append(SuggestedRule(
                    rule_type="RANGE_CHECK",
                    parameters={"column": profile.column_name, "min": buffer_low, "max": buffer_high},
                    severity="WARNING",
                    confidence=0.93,
                    rationale=f"Profile range observed between {min_f} and {max_f} (avg: {profile.avg_value})."
                ))
                evidence.append(f"Numeric distribution min={min_f}, max={max_f}, avg={profile.avg_value}.")
            except ValueError:
                pass

        # 4. PATTERN_MATCH check
        for pat in profile.detected_patterns:
            rules.append(SuggestedRule(
                rule_type="PATTERN_MATCH",
                parameters={"column": profile.column_name, "pattern_name": pat},
                severity="WARNING",
                confidence=0.94,
                rationale=f"Column values adhere consistently to {pat} regular expression."
            ))
            evidence.append(f"Detected pattern: {pat}.")

        # Overall confidence
        avg_conf = sum(r.confidence for r in rules) / len(rules) if rules else 0.85

        return QualityProposalResult(
            column_name=profile.column_name,
            suggested_rules=rules,
            confidence=round(avg_conf, 2),
            evidence=evidence
        )
