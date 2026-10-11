"""Quality Proposer Agent: Proposes data quality validation rules grounded in column stats.

Provides both an LLM-powered agent with schema validation and a heuristic baseline agent.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile
from cforge.llm.client import LLMClient, LLMAuthenticationError


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


class HeuristicQualityProposerAgent:
    """Distribution & threshold baseline quality proposer agent."""

    def __init__(self, model_name: str = "heuristic-rule-baseline"):
        self.model_name = model_name

    def propose_rules(self, profile: ColumnProfile) -> QualityProposalResult:
        """Propose automated data quality checks based on distribution statistics."""
        rules: List[SuggestedRule] = []
        evidence: List[str] = []

        if profile.null_count == 0 and profile.total_rows > 0:
            rules.append(SuggestedRule(
                rule_type="NOT_NULL",
                parameters={"column": profile.column_name},
                severity="ERROR",
                confidence=0.99,
                rationale=f"Zero null values observed across all {profile.total_rows} records."
            ))
            evidence.append("Null percentage is 0.0%.")

        if profile.is_unique:
            rules.append(SuggestedRule(
                rule_type="UNIQUE",
                parameters={"column": profile.column_name},
                severity="ERROR",
                confidence=0.98,
                rationale="Column exhibits 100% cardinality ratio with no duplicates."
            ))
            evidence.append(f"Distinct count equals total rows ({profile.distinct_count}).")

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

        for pat in profile.detected_patterns:
            rules.append(SuggestedRule(
                rule_type="PATTERN_MATCH",
                parameters={"column": profile.column_name, "pattern_name": pat},
                severity="WARNING",
                confidence=0.94,
                rationale=f"Column values adhere consistently to {pat} regular expression."
            ))
            evidence.append(f"Detected pattern: {pat}.")

        avg_conf = sum(r.confidence for r in rules) / len(rules) if rules else 0.85

        return QualityProposalResult(
            column_name=profile.column_name,
            suggested_rules=rules,
            confidence=round(avg_conf, 2),
            evidence=evidence
        )


class LLMQualityProposerAgent:
    """Real LLM-powered data quality assertion generator."""

    SYSTEM_PROMPT = """You are an automated Data Quality Rule Proposer.
Inspect the column profile statistics (null rates, uniqueness, numeric ranges, regex patterns) and propose enforceable data validation rules (NOT_NULL, UNIQUE, RANGE_CHECK, PATTERN_MATCH, REFERENTIAL_INTEGRITY) with appropriate thresholds and severity (ERROR or WARNING).
Ensure all thresholds are mathematically grounded in the observed distribution.
"""

    def __init__(self, model_name: Optional[str] = None):
        self.client = LLMClient(model_name=model_name)

    def propose_rules(self, profile: ColumnProfile) -> QualityProposalResult:
        """Call LLM with JSON-schema validation to generate quality rule proposals."""
        user_prompt = f"""Table: {profile.table_name}
Column: {profile.column_name}
Data Type: {profile.data_type}
Total Rows: {profile.total_rows}
Null Count: {profile.null_count} ({profile.null_percentage}%)
Distinct Values: {profile.distinct_count} (Unique Flag: {profile.is_unique})
Min Value: {profile.min_value}
Max Value: {profile.max_value}
Avg Value: {profile.avg_value}
Detected Patterns: {profile.detected_patterns}
Sample Values: {profile.sample_values[:5] if profile.sample_values else []}

Propose data quality rules adhering to the schema.
"""
        response = self.client.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=QualityProposalResult
        )
        return response.parsed


class QualityProposerAgent:
    """Facade Quality Proposer Agent with configurable execution mode ('auto', 'llm', 'heuristic')."""

    def __init__(self, model_name: str = "cforge-quality-proposer-v1", mode: str = "heuristic"):
        self.model_name = model_name
        self.mode = mode
        self.heuristic_agent = HeuristicQualityProposerAgent(model_name)
        self.llm_agent = LLMQualityProposerAgent()

    def propose_rules(self, profile: ColumnProfile) -> QualityProposalResult:
        if self.mode == "heuristic":
            return self.heuristic_agent.propose_rules(profile)
        
        if self.mode == "llm":
            return self.llm_agent.propose_rules(profile)

        try:
            return self.llm_agent.propose_rules(profile)
        except LLMAuthenticationError:
            return self.heuristic_agent.propose_rules(profile)
        except Exception:
            return self.heuristic_agent.propose_rules(profile)
