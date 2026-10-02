"""Test Suite for Step 4: Multi-Agent Grounded Enrichment."""

import pytest
from cforge.enrichment.profiler import EstateProfiler, ColumnProfile
from cforge.enrichment.describer import DescriberAgent, DescriptionResult
from cforge.enrichment.classifier import ClassifierAgent, ClassificationResult
from cforge.enrichment.glossary_mapper import GlossaryMapperAgent, GlossaryMappingResult
from cforge.enrichment.quality_proposer import QualityProposerAgent, QualityProposalResult
from cforge.enrichment.reconciler import EnrichmentReconciler
from cforge.enrichment.orchestrator import MultiAgentOrchestrator


def test_statistical_profiler_on_real_tables():
    """Verify profiler computes real distributions and patterns without LLM."""
    profiler = EstateProfiler()
    profile = profiler.profile_column("stg_customers", "zip_code_prefix")

    assert profile.table_name == "stg_customers"
    assert profile.column_name == "zip_code_prefix"
    assert profile.total_rows > 0
    assert profile.null_count >= 0
    assert profile.distinct_count > 0
    assert len(profile.sample_values) > 0
    assert len(profile.neighbor_columns) > 0
    # ZIP pattern or spatial cardinality
    assert profile.cardinality_ratio <= 1.0


def test_agent_structured_outputs_and_confidence():
    """Verify all agents produce validated Pydantic models with confidence and evidence."""
    profiler = EstateProfiler()
    profile = profiler.profile_column("fct_orders", "grand_total_brl")

    describer = DescriberAgent()
    desc = describer.describe(profile)
    assert isinstance(desc, DescriptionResult)
    assert 0.0 <= desc.confidence <= 1.0
    assert len(desc.evidence) > 0
    assert "currency" in desc.description.lower() or "monetary" in desc.description.lower()

    classifier = ClassifierAgent()
    clf = classifier.classify(profile)
    assert isinstance(clf, ClassificationResult)
    assert 0.0 <= clf.confidence <= 1.0
    assert len(clf.evidence) > 0

    glossary = GlossaryMapperAgent()
    gloss = glossary.map_term(profile)
    assert isinstance(gloss, GlossaryMappingResult)
    assert gloss.term_name == "Order Grand Total"

    proposer = QualityProposerAgent()
    qual = proposer.propose_rules(profile)
    assert isinstance(qual, QualityProposalResult)
    assert len(qual.suggested_rules) > 0


def test_reconciler_catches_pii_sample_leakage():
    """Verify reconciler catches describer exposing a PII sample value, redacts it, and blocks write."""
    profile = ColumnProfile(
        table_name="raw_olist_customers",
        column_name="customer_id",
        data_type="VARCHAR",
        total_rows=1000,
        null_count=0,
        null_percentage=0.0,
        distinct_count=1000,
        cardinality_ratio=1.0,
        is_unique=True,
        sample_values=["06b8999e2fba1a1fbc88172c00ba8bc7", "18955e83d337fd6b2def6b18a428ac77"]
    )

    # Simulate describer accidentally leaking the sample value in its text
    leaky_desc = DescriptionResult(
        description="Customer account identified by sample key 06b8999e2fba1a1fbc88172c00ba8bc7 in the database.",
        confidence=0.95,
        evidence=["Leaked sample"],
        reasoning="Test"
    )
    clf = ClassificationResult(
        is_pii=True,
        pii_type="CUSTOMER_ID",
        sensitivity_level="RESTRICTED",
        confidence=0.98,
        evidence=["Customer token"],
        regulatory_domains=["GDPR"]
    )
    gloss = GlossaryMappingResult(
        term_name="Customer Identifier",
        domain="Customer Domain",
        definition="Unique customer ID",
        is_new_term=False,
        confidence=0.95,
        evidence=["Test"]
    )
    qual = QualityProposalResult(column_name="customer_id", suggested_rules=[], confidence=0.9, evidence=[])

    reconciler = EnrichmentReconciler()
    reconciled = reconciler.reconcile(profile, leaky_desc, clf, gloss, qual)

    assert not reconciled.can_auto_write, "Leaked PII sample must block auto write!"
    assert any(f.flag_type == "PII_SAMPLE_LEAKAGE" for f in reconciled.flags)
    assert "06b8999e2fba1a1fbc88172c00ba8bc7" not in reconciled.description
    assert "[REDACTED_PII]" in reconciled.description


def test_full_estate_enrichment_one_command():
    """Verify full estate enrichment in one command with cost and time summary."""
    orchestrator = MultiAgentOrchestrator()
    # Enrich key marts & staging tables
    summary = orchestrator.enrich_estate(limit_tables=["stg_customers", "stg_orders", "dim_customers", "fct_orders"])

    assert summary.total_columns_enriched >= 20
    assert summary.total_cost_usd > 0.0
    assert summary.total_latency_seconds >= 0.0
    assert "columns" in summary.summary_message
    assert "$" in summary.summary_message
    assert "minutes" in summary.summary_message
    print(f"\nProof: {summary.summary_message}")
