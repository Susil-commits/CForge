# ContextForge: Pitch Deck
## Governed Metadata Enrichment for Enterprise AI

---

### Slide 1: The Executive Thesis
> **Generative AI cannot safely or accurately query enterprise data without an active, governed context layer.**

* Today, companies connect LLMs directly to bare data warehouses. The result is hallucinated joins, wrong business metrics, and silent PII leaks.
* ContextForge is the **governed intelligence layer** between your data estate and downstream AI agents: automatically profiling schemas, mapping deterministic column lineage, enforcing Policy-as-Code guardrails, and serving real-time context over the Model Context Protocol (MCP).

---

### Slide 2: The Real-World Problem

Enterprises are investing in conversational agents and text-to-SQL interfaces, yet many fail in production. Why?

```mermaid
flowchart LR
    A[User / Executive Query] --> B[Bare LLM / Agent]
    B --> C[Bare Database Schema]
    C --> D1[💥 Hallucinated Metrics & Joins]
    C --> D2[🚨 Direct PII & Compliance Leaks]
    C --> D3[📉 73.3% Baseline Execution Accuracy]
```

1. **The Context Deficit (Silent Hallucinations & Broken Math)**:
   * Databases are built with cryptic column names (`usr_uid`, `tot_amt_curr`, `stat_cd`).
   * An LLM given bare DDL has no knowledge of business definitions, metric calculations (e.g., LTV vs. Net Revenue), or valid value ranges.
   * Result: Inaccurate joins, invalid groupings, and queries that fail or silently return wrong numbers.

2. **The Compliance Catastrophe (Unregulated PII Exposure)**:
   * AI agents have no innate sense of data privacy or compliance (GDPR, HIPAA, LGPD).
   * When asked for "customer purchase patterns," agents query and output raw names, phone numbers, and home addresses directly to unauthorized users.

---

### Slide 3: Why Existing Approaches Fail

| Approach | What It Does | Why It Fails in Enterprise AI |
| :--- | :--- | :--- |
| **Direct Bare Schema** | Feeds `CREATE TABLE` DDL directly to LLM prompt. | 73.3% accuracy on bare schema baseline (12/45 errors); zero privacy protection. |
| **Vector RAG over Docs** | Embeds wiki pages / data dictionaries into a vector database. | Unstructured chunks lack relational foreign keys, schema topology, and column data types. |
| **Fine-Tuning Models** | Trains an LLM on historical queries. | Brittle, expensive, cannot adapt to daily schema migrations, and lacks runtime security controls. |

---

### Slide 4: The Solution — ContextForge

ContextForge provides a governed metadata layer between the data estate and downstream AI agents:

```mermaid
flowchart TD
    Estate[Enterprise Data Estate<br/>DuckDB (Postgres init SQL provided)] --> Profiler[1. Statistical Profiler<br/>Non-LLM distributions, cardinality, nulls]
    Profiler --> Agents[2. Grounded Multi-Agent Ensemble<br/>Structured Pydantic JSON + Confidence Scores]
    Estate --> Lineage[3. AST Column Lineage Engine<br/>sqlglot parser · OpenLineage standard]
    Lineage --> Propagator[4. Recursive Tag Propagator<br/>PII tags traverse downstream models]
    Agents --> Policy[5. Policy-as-Code Engine<br/>Declarative YAML rules gate all catalog writes]
    Policy -->|High Risk / Low Conf| Queue[6. Human Steward Approval Queue]
    Policy -->|Approved| Catalog[7. Relational Catalog & Parquet Lakehouse]
    Catalog --> MCP[8. Model Context Protocol (MCP) Server]
    MCP --> Client[Enterprise AI Agents<br/>Claude · ChatGPT · Cursor · BI Tools]
```

1. **Automated Grounded Enrichment**: Non-LLM statistical profilers extract null rates, cardinality ratios, and value distributions. Specialized LLM agents generate technical descriptions, glossary mappings, and quality checks with strict JSON Schema validation.
2. **Deterministic Column-Level Lineage**: An AST parser (`sqlglot`) traces dependencies across joins, aggregations, CTEs, and window functions (38/39 verified) into OpenLineage standard events.
3. **Multi-Hop Tag Propagation**: When a source column is tagged `PII`, the sensitivity tag automatically cascades downstream to derived dimensions and marts with an unbroken reason chain.
4. **Policy-as-Code & Cryptographic Audit**: Declarative YAML policies intercept and validate every metadata change before commit. High-risk proposals route to human stewards; every change is appended to a SHA-256 hash-chained audit log.
5. **Model Context Protocol (MCP) Server**: Provides dynamic, role-governed schema context, column masking, and active policy guardrails to any AI client at inference time.

---

### Slide 5: Quantified Proof & Benchmark Results

We evaluated ContextForge against a 45-question business query benchmark on an enterprise estate (Olist e-commerce + Northwind wholesale) executing directly on DuckDB:

| Metric | Baseline (Bare Schema) | Governed ContextForge | Enterprise Impact |
| :--- | :---: | :---: | :--- |
| **Text-to-SQL Execution Match** | 73.33% (33/45) | **86.67% (39/45)** | **+13.34 pt accuracy uplift** (single run, one model) |
| **PII Classification F1** | — | **94.3%** (P: 96.2%, R: 92.6%) | Tested on independent held-out split of 94 unseen columns |
| **Column Lineage AST Accuracy** | — | **97.4%** (38/39 verified) | Deterministic dependency tracing across CTEs and window queries |
| **Governance Adversarial Defense** | n/a (no gate) | **87.0%** (20/23 blocked) | Intercepts unauthorized PII extraction attempts at inference |
| **Defect Detection Rate** | n/a (no gate) | **62.5%** (5/8 caught) | Automated quality suite catches schema/null anomalies before production |
| **Enrichment Cost** | — | **$0.1024** | Cost per 1,000 API calls, gemini-3.1-flash-lite rates |

---

### Slide 6: Architectural Distinction

* **Runtime Governance**: Evaluates policies and serves metadata directly to AI at runtime over MCP rather than relying on static documentation.
* **Relational Graphs**: Operates on deterministic relational schemas, AST lineage trees, and statistical profiles rather than unstructured vector text chunks.
* **Open Protocols**: Built on OpenLineage, Model Context Protocol (MCP), and standard SQL Parquet lakehouse formats.

---

### Slide 7: Honest Engineering & Limitations

Rather than claiming complete coverage, we document exactly where ContextForge breaks:
* **Unstructured Free-Text PII**: Regex and token classifiers catch structured identifiers (emails, UUIDs) but miss PII embedded in free-form delivery notes.
* **Correlated Scalar Subqueries**: AST resolution struggles with correlated subqueries evaluated as anonymous columns.
* **Relational Semantic Defects**: Schema rules catch null spikes and range violations, but miss cross-table business logic errors (e.g. `delivery_date < order_date`).
* **Paraphrased Prompt Injections**: Evasive phrasing can bypass keyword policy filters; keyword rules produce a 13.0% false refusal rate on benign queries.

*Full details: [`docs/failures_and_limitations.md`](failures_and_limitations.md).*

---

### Slide 8: The Vision & Roadmap

* **Phase 1 (Shipped)**: Core engine, DuckDB estate (Postgres init SQL provided), AST lineage, Policy-as-Code, MCP server, web UI, 54-test suite.
* **Phase 2 (Next)**: Apache Iceberg & Delta Lake metadata connector, dbt semantic layer integration, and LLM-as-a-Judge real-time semantic policy gating.
* **Phase 3 (Enterprise)**: Distributed enterprise RBAC, SAML/Okta integration, multi-engine lineage (Snowflake + BigQuery + Databricks).

---

### Summary
ContextForge gives enterprise AI agents the **eyes to understand your schema** and the **guardrails to protect your data**.
