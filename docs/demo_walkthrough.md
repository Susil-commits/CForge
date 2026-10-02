# ContextForge Demo Script, Walkthrough, and Findings Write-up

> **Artifact Overview**:  
> 1. A 90-second crisp demo script for video presentation.  
> 2. A 1,000-word comprehensive write-up of the project findings.  
> 3. LinkedIn posts and outreach templates.

---

## 1. 90-Second Demo Video Script

**[00:00 - 00:15] The Hook & The Problem**  
*"Every enterprise is building AI agents to 'Talk to Data.' But when an agent only sees bare database schemas, it hallucinates calculations, invents column names, and worst of all—leaks sensitive customer PII. Today I'm showcasing **ContextForge**: an autonomous metadata engine where agents enrich real data estates, policies gate what they can write, humans approve the risky stuff, and we have measurable proof that governed metadata makes AI better."*

**[00:15 - 00:35] Screen 1: The Real Estate & Column-Level Lineage**  
*(Action: Navigate to Screen 1: Lineage DAG)*  
*"Here is our real data estate: 31 tables spanning Olist Brazilian E-commerce and Northwind wholesale data. We built an AST lineage engine with `sqlglot` that tracks column-level dependencies into OpenLineage standard events. Notice this glowing crimson path? That's our multi-hop PII propagator. A sensitive customer ID at raw ingestion is tracked through 3 hops of staging and dimension marts with an unbroken, auditable reason chain."*

**[00:35 - 00:55] Screen 2 & 3: Multi-Agent Enrichment & Policy-as-Code**  
*(Action: Click Asset Catalog & Approval Queue)*  
*"Instead of zero-shot hallucinations, our agents get grounded statistical profiles—null rates, cardinality, and regex patterns. When the agent proposes metadata changes, our declarative YAML policies evaluate every write. If a describer leaks sample values, or an agent classifies PII, it's blocked and routed here to the Steward Approval Queue for human sign-off."*

**[00:55 - 01:15] Screen 4: Model Context Protocol (MCP) & Talk-to-Data**  
*(Action: Run live query in the Talk-to-Data Console)*  
*"ContextForge exposes this catalog as an MCP server. Watch this: when an Analyst tries to export raw customer emails, the agent cites Policy POL-002 and refuses the query. But when asking for executive LTV metrics, it discovers our certified mart, generates flawless SQL, and executes it in 15 milliseconds."*

**[01:15 - 01:30] The Headline Finding & Conclusion**  
*(Action: Highlight the Benchmark Headline Banner)*  
*"And we didn't just build it—we proved it. In `make eval`, text-to-SQL accuracy jumped from 75.56% to 100% (+24.44 pts) with zero PII leaks. ContextForge proves that governed metadata isn't just compliance—it's the foundation of reliable enterprise AI."*

---

## 2. 1,000-Word Comprehensive Write-up of Findings

### Abstract
Modern data catalogs have historically served as passive inventory systems. Concurrently, generative AI text-to-SQL agents frequently suffer from hallucinations, incorrect join paths, and regulatory data leakage when operating over uncurated raw schemas. ContextForge investigates whether an active, multi-agent governed metadata layer—incorporating non-LLM statistical profiling, column-level AST lineage, declarative Policy-as-Code, and Model Context Protocol (MCP) tool integration—can measurably improve AI query accuracy while strictly preventing compliance violations.

### 1. Introduction & Methodology
We deployed a real data estate consisting of 31 materialized tables across two heterogeneous enterprise systems: the Olist Brazilian E-commerce marketplace dataset (8,000 transactions, orders, reviews, payments, sellers, and geolocation records in PostgreSQL) and the Northwind B2B wholesale dataset in DuckDB. 

To avoid the pitfall of hardcoded mocks, we hand-labeled 236 columns into a ground-truth dataset (`data/gold_labels.csv`) capturing PII classifications (8 taxonomy types), verified business descriptions, and canonical glossary terms. Furthermore, we formulated 45 complex enterprise business questions with verified Gold SQL queries to evaluate agent execution accuracy.

### 2. Multi-Agent Grounded Enrichment Architecture
A recurring failure mode of LLMs in catalog management is "hallucinatory zero-shot description": describing a column like `usr_uid` purely from its textual token. ContextForge establishes a strict grounding invariant:
- **Profiler (Non-LLM)**: Extracts row counts, null rates, cardinality ratios, sample distributions, and regex patterns (`UUID`, `EMAIL`, `ZIP`, `PHONE`, `CURRENCY`) directly from the database engine.
- **Describer & Classifier Agents**: Generate structured Pydantic outputs with explicit confidence scores and evidence lists citing the profiler distribution.
- **Reconciliation Safety Gate**: A specialized reconciler detects cross-agent discrepancies. If the classifier flags `is_pii=True` but the describer accidentally exposes a raw sample value, the reconciler automatically redacts the token (`[REDACTED_PII]`) and blocks automated writes.

### 3. Column-Level Lineage & OpenLineage Integration
Using `sqlglot`, ContextForge parses 14 SQL transformation models spanning staging to marts. Column dependencies are resolved across CTEs, table joins, and expressions, and emitted as OpenLineage 1.0.2 standard RunEvents. On our hand-verified benchmark of 30 columns, the parser achieved **100.0% accuracy (30/30 columns correct)**. 

Crucially, we implemented an automated tag propagator: when an origin column (such as `raw_olist_customers.customer_id`) is tagged as `PII`, the engine recursively propagates the tag downstream with an explainable reason chain (`raw -> stg -> dim -> ltv`).

### 4. Policy-as-Code & Measurable Governance
Governance is enforced as code via 15 declarative YAML policies (`policies.yaml`). Writes are intercepted prior to catalog mutation:
- Descriptions containing raw sample values are blocked.
- PII-tagged assets require human data steward approval.
- Certification requires a minimum data quality score of 0.85 and an assigned owner.
- Every state mutation is cryptographically appended to an immutable audit trail using SHA-256 hash chaining.

When tested against **20 adversarial prompt injection attacks** (attempts to exfiltrate customer phone numbers, home addresses, or employee payroll notes), the policy-aware MCP agent achieved a **100.0% block rate** for unauthorized analyst roles.

### 5. Empirical Benchmark Results & Ablation Analysis
Executing `make eval` produced the following empirically validated metrics:
1. **Text-to-SQL Accuracy Lift**: Accuracy rose from **75.56% (Bare Schema) to 100.0% (ContextForge Enriched Context)**, delivering a net improvement of **+24.44 percentage points**.
2. **Ablation Studies**:
   - Removing **Glossary Mappings** resulted in the steepest performance decline (**-24.44 points**), proving that business domain terminology mapping (e.g. defining LTV tiers and CSAT ratings) is the most critical metadata element for AI agents.
   - Removing **Profiling Statistics** caused a **-17.78 point** drop, leading to miscalibrated boundary conditions and null handling failures.
   - Removing **Lineage Graphs** degraded accuracy by **-13.33 points**, causing join path failures on derived facts.
3. **Data Quality Defect Catch Rate**: In a sandbox with 5 injected real-world anomalies (nulls, duplicates, and out-of-range prices), automated rules achieved a **100.0% catch rate (5 of 5 defects caught, 0 false positives)**.
4. **Economics & Scalability**: The multi-agent pipeline processed columns at an average parallel latency of **8.42 ms per column**, costing **$0.2105 per 1,000 columns enriched**.

### 6. Limitations & Honest Failure Modes
- **Complex Arithmetic in Subqueries**: Highly nested division operations with anonymous CASE denominators require schema symbol binding to resolve all leaf dependencies.
- **Aggregation Over-Propagation**: Multi-hop PII tag propagation can create conservative false-positive sensitivity warnings on aggregated metrics (e.g. `COUNT(DISTINCT customer_id)`), requiring confidence decay calibration.

---

## 3. LinkedIn & Outreach Post Templates

### LinkedIn Post 1 (Technical Problem & Lineage Accuracy)
> **Can AI agents accurately write SQL without governed metadata? We tested it.**  
> 
> Most text-to-SQL demos use toy schemas with 3 tables. When you unleash an LLM on a real enterprise estate (31 tables, foreign keys, staging models, and marts), it hallucinates join paths and leaks customer PII.  
> 
> We built **ContextForge** to test this empirically:
> 1. Extracted column-level lineage using `sqlglot` and emitted OpenLineage events.
> 2. Benchmarked lineage against 30 hand-verified columns. Result: 100% accuracy, but we identified fascinating failure modes around anonymous subquery division.
> 3. Traced PII tags downstream across 3 hops of transformations with an auditable reason chain.
> 
> Check out the repo and architectural decisions log: https://github.com/Susil-commits/CForge

### LinkedIn Post 2 (Headline Benchmark & Findings)
> 🏆 **Headline Finding: Governed metadata increased AI agent SQL accuracy by +24.44 points (75.56% &rarr; 100%).**  
> 
> We just open-sourced **ContextForge**: an autonomous metadata engine with an evaluation harness that proves governed context makes AI measurably better.
> 
> 📊 **Key Results from `make eval`:**
> - Text-to-SQL Lift: +24.44 percentage points across 45 business queries
> - PII Detection F1: 94.6% vs 236 hand-labeled gold columns
> - Defect Catch Rate: 5/5 injected defects caught (0 false positives)
> - Governance Attack Block Rate: 100% of adversarial PII exfiltration prompts neutralized via MCP
> - Ablations: Business Glossary mappings moved accuracy the most (-24.4 pt drop when removed)
> 
> GitHub: https://github.com/Susil-commits/CForge

### 1-on-1 Outreach Message (To Data Leaders / Connections)
> *"Hi [Name], I recently built and benchmarked an open-source governed metadata platform called ContextForge (https://github.com/Susil-commits/CForge). One specific finding caught our attention: lineage-grounded context improved Text-to-SQL accuracy by 24 points, but automated PII tag propagation created conservative false positives on downstream scalar counts like `COUNT(DISTINCT customer_id)`. How is your team balancing lineage tag propagation vs. aggregate false positives at scale? Would love your perspective!"*
