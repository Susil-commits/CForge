"""Multi-Agent Parallel Orchestrator with Token, Latency, and Cost Accounting."""

from typing import Dict, List, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH
from cforge.enrichment.profiler import EstateProfiler, ColumnProfile
from cforge.enrichment.describer import DescriberAgent, DescriptionResult
from cforge.enrichment.classifier import ClassifierAgent, ClassificationResult
from cforge.enrichment.glossary_mapper import GlossaryMapperAgent, GlossaryMappingResult
from cforge.enrichment.quality_proposer import QualityProposerAgent, QualityProposalResult
from cforge.enrichment.reconciler import EnrichmentReconciler, ReconciledEnrichment


class AssetEnrichmentTelemetry(BaseModel):
    table_name: str
    column_name: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    reconciled: ReconciledEnrichment


class EstateEnrichmentSummary(BaseModel):
    total_columns_enriched: int
    total_tokens: int
    total_cost_usd: float
    total_latency_seconds: float
    auto_approved_count: int
    queued_for_review_count: int
    reconciliation_flags_count: int
    summary_message: str
    telemetry: List[AssetEnrichmentTelemetry] = Field(default_factory=list)


class MultiAgentOrchestrator:
    # Standard LLM Pricing per 1,000 tokens
    COST_PER_1K_INPUT = 0.00015
    COST_PER_1K_OUTPUT = 0.00060

    def __init__(self, db_path: Optional[str] = None):
        self.profiler = EstateProfiler(db_path or str(ESTATE_DB_PATH))
        self.describer = DescriberAgent()
        self.classifier = ClassifierAgent()
        self.glossary_mapper = GlossaryMapperAgent()
        self.quality_proposer = QualityProposerAgent()
        self.reconciler = EnrichmentReconciler()

    def enrich_column(self, table_name: str, column_name: str,
                      upstream_lineage: Optional[List[str]] = None) -> AssetEnrichmentTelemetry:
        """Execute all 5 agents and reconciler for a single column with telemetry."""
        start_time = time.perf_counter()

        # Step 1: Non-LLM Profiler (Grounded context foundation)
        profile = self.profiler.profile_column(table_name, column_name)

        # Estimate input tokens based on prompt grounding
        context_str = f"{profile.model_dump_json()} | Lineage: {upstream_lineage}"
        input_tokens = len(context_str) // 4 + 120

        # Step 2: Run Agents
        desc_res = self.describer.describe(profile, lineage_upstream=upstream_lineage)
        clf_res = self.classifier.classify(profile)
        gloss_res = self.glossary_mapper.map_term(profile)
        qual_res = self.quality_proposer.propose_rules(profile)

        # Step 3: Reconcile disagreements & safety
        reconciled = self.reconciler.reconcile(profile, desc_res, clf_res, gloss_res, qual_res)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Estimate output tokens from structured results
        output_str = f"{reconciled.model_dump_json()}"
        output_tokens = len(output_str) // 4 + 80

        cost_usd = (input_tokens / 1000.0 * self.COST_PER_1K_INPUT) + (output_tokens / 1000.0 * self.COST_PER_1K_OUTPUT)

        return AssetEnrichmentTelemetry(
            table_name=table_name,
            column_name=column_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 6),
            latency_ms=round(elapsed_ms, 2),
            reconciled=reconciled
        )

    def enrich_estate(self, max_workers: int = 8, limit_tables: Optional[List[str]] = None) -> EstateEnrichmentSummary:
        """Run multi-agent enrichment across the entire estate in parallel."""
        start_time = time.perf_counter()
        conn = duckdb.connect(self.profiler.db_path, read_only=True)
        all_tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
        
        target_tables = limit_tables if limit_tables else all_tables
        tasks: List[tuple] = []
        for t in target_tables:
            cols = [r[0] for r in conn.execute(f"DESCRIBE {t}").fetchall()]
            for c in cols:
                tasks.append((t, c))

        telemetries: List[AssetEnrichmentTelemetry] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_col = {
                executor.submit(self.enrich_column, t, c): (t, c)
                for t, c in tasks
            }
            for future in as_completed(future_to_col):
                telemetry = future.result()
                telemetries.append(telemetry)

        total_elapsed_seconds = round(time.perf_counter() - start_time, 2)
        total_minutes = round(total_elapsed_seconds / 60.0, 2)
        total_tokens = sum(t.input_tokens + t.output_tokens for t in telemetries)
        total_cost = round(sum(t.cost_usd for t in telemetries), 4)
        auto_approved = sum(1 for t in telemetries if t.reconciled.can_auto_write)
        queued = len(telemetries) - auto_approved
        flags_count = sum(len(t.reconciled.flags) for t in telemetries)

        summary_msg = f"{len(telemetries)} columns, ${total_cost:.4f}, {total_minutes} minutes"

        return EstateEnrichmentSummary(
            total_columns_enriched=len(telemetries),
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            total_latency_seconds=total_elapsed_seconds,
            auto_approved_count=auto_approved,
            queued_for_review_count=queued,
            reconciliation_flags_count=flags_count,
            summary_message=summary_msg,
            telemetry=telemetries
        )
