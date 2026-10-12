# Claims and Benchmark Metrics Audit

> **Verification and Traceability Ledger**:  
> Every empirical number, metric, and quantitative statement appearing in [`README.md`](../README.md) and [`docs/pitch_deck.md`](pitch_deck.md) mapped directly to verified source artifacts in [`results/benchmark.md`](../results/benchmark.md) and [`results/benchmark.json`](../results/benchmark.json).

---

## 1. Verified Metrics Audit Table

| Metric / Claim | Quoted Document & Location | Quoted Value | Source File | Source Location in `results/` | Audit Verification Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Text-to-SQL Accuracy Lift** | `README.md` (Badge, Summary, Ablations)<br>`docs/pitch_deck.md` (Slide 5) | `+13.34 pts` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:12, 37`<br>`benchmark.json:3, 5, 163` | Verified. 73.33% to 86.67% on 45 queries (+13.34 pts). |
| **Text-to-SQL Baseline (Bare Schema)** | `README.md` (Summary, Ablations)<br>`docs/pitch_deck.md` (Slide 2, 3, 5) | `73.3%` / `73.33% (33/45)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:22, 35, 53`<br>`benchmark.json:6, 159-160, 955-956` | Verified. 33 of 45 execution matches against DuckDB. |
| **Text-to-SQL Governed Context** | `README.md` (Summary, Ablations)<br>`docs/pitch_deck.md` (Slide 5) | `86.7%` / `86.67% (39/45)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:23, 36, 49`<br>`benchmark.json:7, 161-162, 927-928` | Verified. 39 of 45 execution matches against DuckDB. |
| **Evaluation Question Count** | `README.md` (Summary, Eval Harness)<br>`docs/pitch_deck.md` (Slide 5) | `45 questions` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:12, 22, 33`<br>`benchmark.json:3, 158` | Verified. Exactly 45 business questions evaluated. |
| **PII Classification F1-Score** | `README.md` (Summary Table)<br>`docs/pitch_deck.md` (Slide 5) | `94.3%` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:18`<br>`benchmark.json:8, 24, 35` | Verified. Harmonic mean of precision (96.2%) and recall (92.6%). |
| **PII Classification Precision** | `README.md` (Summary Table)<br>`docs/pitch_deck.md` (Slide 5) | `96.2%` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:16`<br>`benchmark.json:22, 33` | Verified. 25 TP / (25 TP + 1 FP) = 96.15%. |
| **PII Classification Recall** | `README.md` (Summary Table)<br>`docs/pitch_deck.md` (Slide 5) | `92.6%` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:17`<br>`benchmark.json:23, 34` | Verified. 25 TP / (25 TP + 2 FN) = 92.59%. |
| **Held-Out Split Column Count** | `README.md` (Summary, Eval Harness)<br>`docs/pitch_deck.md` (Slide 5) | `94 columns` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:16, 17`<br>`benchmark.json:25, 26, 36` | Verified. Held-out test split of 94 unseen columns. |
| **AST Column Lineage Accuracy** | `README.md` (Summary Table, ADR 006)<br>`docs/pitch_deck.md` (Slide 4, 5) | `97.4% (38/39)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:20, 61`<br>`benchmark.json:9, 41-44` | Verified. 38 of 39 hand-verified columns extracted correctly. |
| **Lineage Boundary Failures** | `README.md` (Summary Table)<br>`docs/pitch_deck.md` (Slide 5, 7) | `1 failure` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:63-65`<br>`benchmark.json:43, 46-79` | Verified. `mart_federated_shipments.carrier_item_ratio`. |
| **Defect Catch Rate** | `README.md` (Summary Table, Module 6)<br>`docs/pitch_deck.md` (Slide 5) | `62.5% (5/8)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:21, 82`<br>`benchmark.json:10, 84-88` | Verified. Caught 5 of 8 injected defects; 0 false positives. |
| **Governance Attack Block Rate** | `README.md` (Badge, Summary Table)<br>`docs/pitch_deck.md` (Slide 5) | `87.0% (20/23)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:24, 101`<br>`benchmark.json:11, 903, 905` | Verified. Blocked 20 of 23 adversarial PII prompts (86.96%). |
| **Governance False Refusal Rate** | `README.md` (Badge, Summary Table)<br>`docs/pitch_deck.md` (Slide 7) | `13.0% (3/23)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:25, 103`<br>`benchmark.json:12, 913, 915` | Verified. Blocked 3 of 23 benign control queries (13.04%). |
| **Description Quality Rubric** | `README.md` (Summary Table)<br>`docs/failures_and_limitations.md` | `4.53 / 5.0` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:19, 72`<br>`benchmark.json:13, 892` | Verified. Scored across 30 samples by LLM judge. |
| **Description Samples Evaluated** | `README.md` (Summary Table) | `30 samples` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:19, 70`<br>`benchmark.json:891` | Verified. 30 column descriptions evaluated. |
| **Description Hallucinations** | `results/benchmark.md` (Section 4) | `1 / 30 (3.3%)` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:73`<br>`benchmark.json:893, 898` | Verified. 1 of 30 descriptions contained unobserved claim. |
| **Enrichment Cost** | `README.md` (Summary Table)<br>`docs/pitch_deck.md` (Slide 5) | `$0.1024` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:26`<br>`benchmark.json:14, 967` | Verified. Cost per 1,000 API calls, gemini-3.1-flash-lite rates. |
| **Processing Latency** | `README.md` (Summary Table) | `6607.16 ms` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:27`<br>`benchmark.json:15, 968` | Verified. Mean API call latency on live timer. |
| **Ablation: No Lineage Context** | `README.md` (Ablations Table) | `82.22% (37/45), -4.45 pts` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:50`<br>`benchmark.json:934-936, 963` | Verified. 37 matches out of 45. |
| **Ablation: No Profiling Stats** | `README.md` (Ablations Table) | `86.67% (39/45), -0.00 pts` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:51`<br>`benchmark.json:941-943, 964` | Verified. 39 matches out of 45 (0 net change on n=45). |
| **Ablation: No Glossary Terms** | `README.md` (Ablations Table) | `84.44% (38/45), -2.23 pts` | `results/benchmark.md`<br>`results/benchmark.json` | `benchmark.md:52`<br>`benchmark.json:948-950, 965` | Verified. 38 matches out of 45 (-1 question shift). |
| **Test Suite Passing** | `README.md` (Badge, Quickstart)<br>`docs/pitch_deck.md` (Slide 8) | `54 passed` | `tests/` | Test runner execution | Verified via `pytest tests/ -v` (54 passed). |

---

## 2. Audited and Removed / Softened Claims

The following claims and figures previously existed in `README.md` or `docs/pitch_deck.md` but had no empirical source in `results/` or presented unmeasured baselines. All were audited and removed or corrected:

| Removed / Softened Text | Original Location | Reason for Removal / Modification | Replacement / Corrected Phrasing |
| :--- | :--- | :--- | :--- |
| `Catalog Enrichment Unit Cost: Manual unit cost and 500-fold multiplier claim` | `docs/pitch_deck.md:90` | **Unsourced claim & mismatched units.** No empirical source in `results/` for manual cost estimate or multiplier. Cost units mixed table vs column. | **Row deleted.** Replaced with verified enrichment cost: `$0.1024` with unit `Cost per 1,000 API calls, gemini-3.1-flash-lite rates`. |
| `0% blocked` (Governance Baseline) | `docs/pitch_deck.md:88`<br>`README.md:94` | **Unmeasured baseline.** Presenting "0% blocked" as an empirical baseline measurement when no gate was installed is unmeasured by construction. | Replaced with `n/a (no gate)`. |
| `0% caught` (Defect Baseline) | `docs/pitch_deck.md:89`<br>`README.md:93` | **Unmeasured baseline.** Presenting "0% caught" as a measured baseline without a testing harness is unmeasured by construction. | Replaced with `n/a (no gate)`. |
| `over 80% of deployments fail or stall` | `README.md:29`<br>`docs/pitch_deck.md:16` | **Unsourced industry marketing claim.** Not measured or verified in `results/`. | Softened to plain statement: `many deployments fail or stall before production due to architectural gaps`. |
| `Sub-75% Query Execution Accuracy` | `docs/pitch_deck.md:24` | **Imprecise rounded figure.** | Aligned to exact measured bare schema baseline: `73.3% Baseline Execution Accuracy`. |
| `26.7% error rate` / `27% failures` | `README.md:52`<br>`docs/pitch_deck.md:47` | **Inverted unsourced figure.** | Replaced with exact measured baseline: `73.3% accuracy on bare schema baseline (12/45 errors)`. |
| `10,000+ columns manually` | `docs/pitch_deck.md:38` | **Unsourced claim** in legacy catalog section. | **Section deleted completely.** |
| Mentions of legacy commercial catalog vendors, static catalog metaphors, and `quadrantChart` | `README.md:41-44, 55`<br>`docs/pitch_deck.md:36-40, 50, 96-110` | **Competitor names, marketing metaphors, and subjective quadrant chart.** | **Deleted entirely.** Replaced with plain technical descriptions of architectural distinctions. |
| Overstated marketing runtime descriptions | `README.md:61`<br>`docs/pitch_deck.md:2, 56` | **Marketing buzzwords.** | Replaced with plain technical language: `ContextForge is a metadata enrichment and policy governance layer that sits between a data warehouse and downstream AI agents.` |
| `PostgreSQL · DuckDB · Snowflake` (as tested runtime) | `README.md:65, 125, 133`<br>`docs/pitch_deck.md:60, 132` | **Postgres was not benchmarked.** All benchmark runs executed against DuckDB. Postgres is supported only via SQL export. | Replaced with `DuckDB (Postgres init SQL provided)`. |
| `236 hand-labeled ground-truth columns` | `README.md:179, 224, 320` | **Full dataset label count not in `results/`.** Benchmark evaluation explicitly evaluated 94 held-out columns. | Updated to cite the measured `94 held-out columns`. |
| `20 adversarial prompts` | `README.md:224` | **Inaccurate count.** Results evaluate 23 adversarial attacks and 23 benign control queries. | Aligned to `23 adversarial prompts alongside 23 benign control prompts`. |
| Unit mismatch in catalog cost metric | `docs/pitch_deck.md:90` | **Incorrect unit.** Previously quoted cost per columns instead of API calls. | Aligned to `cost per 1,000 API calls, gemini-3.1-flash-lite rates`. |
