"""Reconciler Agent: Resolves disagreements across agents and prevents PII data leakage."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from cforge.enrichment.profiler import ColumnProfile
from cforge.enrichment.describer import DescriptionResult
from cforge.enrichment.classifier import ClassificationResult
from cforge.enrichment.glossary_mapper import GlossaryMappingResult
from cforge.enrichment.quality_proposer import QualityProposalResult


class ReconciliationFlag(BaseModel):
    flag_type: str  # PII_SAMPLE_LEAKAGE, PATTERN_DISAGREEMENT, LOW_CONFIDENCE, SCHEMA_ANOMALY
    severity: str  # CRITICAL, WARNING, INFO
    description: str
    action_taken: str


class ReconciledEnrichment(BaseModel):
    table_name: str
    column_name: str
    description: str
    is_pii: bool
    pii_type: str
    sensitivity_level: str
    glossary_term: str
    suggested_rules_count: int
    overall_confidence: float
    can_auto_write: bool
    flags: List[ReconciliationFlag] = Field(default_factory=list)
    reconciled_evidence: List[str] = Field(default_factory=list)


class EnrichmentReconciler:
    def reconcile(self, profile: ColumnProfile,
                  desc: DescriptionResult,
                  clf: ClassificationResult,
                  glossary: GlossaryMappingResult,
                  quality: QualityProposalResult) -> ReconciledEnrichment:
        """Reconcile multi-agent outputs, enforce safety gates, and resolve conflicts."""
        flags: List[ReconciliationFlag] = []
        can_auto_write = True
        final_description = desc.description

        # 1. Critical Gate: PII Sample Value Exposure Check
        if clf.is_pii:
            for sample in profile.sample_values:
                s_clean = sample.strip()
                if len(s_clean) >= 3 and s_clean.lower() in desc.description.lower():
                    flags.append(ReconciliationFlag(
                        flag_type="PII_SAMPLE_LEAKAGE",
                        severity="CRITICAL",
                        description=f"Describer text exposed raw sample value '{s_clean}' for PII-classified column.",
                        action_taken="Blocked write, redacted value with [REDACTED_PII], and shunted to review."
                    ))
                    # Redact the text
                    final_description = final_description.replace(s_clean, "[REDACTED_PII]")
                    can_auto_write = False

        # 2. Pattern vs Classifier Disagreement
        if not clf.is_pii and any(p in profile.detected_patterns for p in ["EMAIL_PATTERN", "PHONE_PATTERN", "ZIP_PATTERN"]):
            flags.append(ReconciliationFlag(
                flag_type="PATTERN_DISAGREEMENT",
                severity="WARNING",
                description=f"Profiler detected sensitive pattern ({profile.detected_patterns}) but classifier labeled is_pii=False.",
                action_taken="Overriding is_pii=True and queuing for steward review."
            ))
            clf.is_pii = True
            clf.pii_type = "POSTAL_CODE" if "ZIP_PATTERN" in profile.detected_patterns else "SENSITIVE"
            can_auto_write = False

        # 3. Low Confidence Gate
        min_conf = min(desc.confidence, clf.confidence, glossary.confidence, quality.confidence)
        if min_conf < 0.80:
            flags.append(ReconciliationFlag(
                flag_type="LOW_CONFIDENCE",
                severity="WARNING",
                description=f"Agent confidence ({min_conf}) below auto-write threshold 0.80.",
                action_taken="Queued for data steward review."
            ))
            can_auto_write = False

        # Aggregate evidence
        combined_evidence = (
            [f"[Describer] {e}" for e in desc.evidence[:2]] +
            [f"[Classifier] {e}" for e in clf.evidence[:2]] +
            [f"[Glossary] {e}" for e in glossary.evidence[:1]] +
            [f"[Quality] {e}" for e in quality.evidence[:1]]
        )

        overall_conf = round((desc.confidence + clf.confidence + glossary.confidence + quality.confidence) / 4.0, 3)

        return ReconciledEnrichment(
            table_name=profile.table_name,
            column_name=profile.column_name,
            description=final_description,
            is_pii=clf.is_pii,
            pii_type=clf.pii_type,
            sensitivity_level=clf.sensitivity_level,
            glossary_term=glossary.term_name,
            suggested_rules_count=len(quality.suggested_rules),
            overall_confidence=overall_conf,
            can_auto_write=can_auto_write,
            flags=flags,
            reconciled_evidence=combined_evidence
        )
