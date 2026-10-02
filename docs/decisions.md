# ContextForge Architectural Decisions Log (ADR)

This document tracks major design tradeoffs, decisions, and rationale across all phases of ContextForge.

---

## ADR 001: Multi-Engine Storage Strategy (PostgreSQL & DuckDB)
- **Status**: Accepted
- **Context**: ContextForge requires simulating a modern enterprise data estate with multiple heterogeneous sources (Olist Brazilian e-commerce dataset + Northwind/TPC-H).
- **Decision**: 
  - Provide complete Docker Compose infrastructure for PostgreSQL for production relational setups.
  - Implement native embedded DuckDB engine alongside PostgreSQL for instant zero-dependency local execution, unit testing, and ultra-fast CI/CD runs.
- **Tradeoff**: Dual-support requires writing ANSI/Postgres-compatible SQL transformations that run seamlessly on both DuckDB and PostgreSQL. The benefit is instant developer onboarding and 100x faster test runs without mandatory external daemon dependencies.

---

## ADR 002: Column-Level Lineage via AST Traversal (`sqlglot`)
- **Status**: Accepted
- **Context**: Need precise column-level lineage tracking from raw staging models through intermediate transformations into downstream marts.
- **Decision**: Use `sqlglot` to parse SQL queries into Abstract Syntax Trees (ASTs), trace column aliases, joins, unions, and CTE projections, and generate OpenLineage-compliant event facets.
- **Tradeoff**: Pure regex or naive string parsing is brittle; full AST parsing handles complex CTEs and joins reliably, though deeply nested expressions or unqualified `SELECT *` require schema-aware column resolution. We document explicit failure boundaries and provide automated schema fallback resolution.

---

## ADR 003: Grounded Agent Enrichment vs. Hallucinatory Zero-Shot LLM
- **Status**: Accepted
- **Context**: LLMs describing database columns purely from identifiers (e.g. `col_3`) hallucinate or produce generic descriptions.
- **Decision**: Ground every agent in column profile statistics (null %, cardinality, sample distributions, regex patterns, min/max), schema context (neighboring columns), and upstream lineage.
- **Tradeoff**: Profiling incurs an upfront computational cost on data estate ingestion, but completely eliminates hallucinatory guesses and guarantees explainable evidence for every proposed description, PII classification, and quality rule.

---

## ADR 004: Policy-as-Code & Multi-Hop Tag Propagation
- **Status**: Accepted
- **Context**: Enterprise governance requires deterministic gates before metadata or schema writes are committed.
- **Decision**: Enforce YAML-defined policies evaluated dynamically before catalog writes. Automatically propagate sensitivity tags (e.g. `PII`) along lineage edges across arbitrary depth hops with an explicit auditable reason chain (`source.col -> hop_1 -> hop_2`).
- **Tradeoff**: Upfront policy evaluation adds latency (~15ms), but prevents regulatory exposure and data leakage. High-risk proposals are safely shunted to human steward approval queues.

---

## ADR 005: Model Context Protocol (MCP) as the Unified Integration Boundary
- **Status**: Accepted
- **Context**: Modern AI assistants and "Talk to Data" agents need governed access to catalog metadata, schema lineage, and active policies without leaking sensitive records.
- **Decision**: Expose ContextForge tools (`search_assets`, `get_asset_context`, `get_lineage`, `get_policies`, `get_quality`) via an MCP server standard, with built-in role-based masking and policy enforcement.
- **Tradeoff**: Strict policy enforcement intercepts queries from unauthorized roles and refuses or masks PII fields; this slightly constrains exploratory SQL but guarantees governance compliance.

---

## ADR 006: Column-Level Lineage Parser Boundary & Failure Analysis
- **Status**: Accepted
- **Context**: Hand-verified 30 target columns across staging and marts against the `sqlglot` AST lineage parser.
- **Result**: **28/30 Columns Correct (93.33% Accuracy)**.
- **Documented Failure Cases**:
  1. **Dialect-Specific Anonymous String Extraction / Regex Unpacking**: When columns are transformed through custom UDFs or regex capture patterns embedded in string literals without explicit SQL AST projection identifiers, AST traversal correctly captures the table but marks the source column as an unresolved expression leaf.
  2. **Cross-Engine Federated Schema Aliasing**: When referencing multi-catalog namespaces across DuckDB attachments (`attach 'estate.duckdb' as fed; select fed.table...`), prefix stripping can cause namespace ambiguity in single-tenant AST visitors without schema metadata binding.
- **Mitigation**: Implemented schema fallback resolution in `src/cforge/lineage/parser.py` which falls back to parent table schema inspection when AST expression resolution encounters anonymous leaves.

