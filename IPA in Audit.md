# Use Case Automation Blueprint: Intelligent RPA for Audit Planning

This blueprint shows how to automate the Audit Planning phase with Intelligent RPA (IPA) to surface audit risk at the financial statement, account, and transaction levels using only Python and open-source libraries. It operationalizes:
- Huang & Vasarhelyi’s RPA Framework: task selection (structured, repetitive, mature), procedure modification and data standardization, in-house implementation, and evaluation with a focus on detection risk.
- Zhang’s IPA approach: blending RPA for structured tasks with NLP/ML for semi-structured and unstructured tasks, then integrating results with human judgment in an IPA loop during planning.

Your inputs:
- Prior year financial statements (PDF/Word).
- Current-year draft BS/PL, Trial Balance (TB), General Ledger (GL).

---

## 1) Workflow Analysis & Automation Strategy

### A. Manual planning steps (current state)
- Gather prior-year FS, workpapers, and permanent files.
- Import TB and GL; map chart of accounts across periods; normalize sign conventions.
- Perform preliminary analytical procedures:
  - Horizontal/vertical (YoY and common-size) analysis, identify significant fluctuations.
  - Ratio analytics (liquidity, leverage, profitability, turnover).
- Read prior-year footnotes for significant accounting policies, estimates, contingencies, going concern, related parties.
- Scan GL to flag unusual transactions and period-end journal entries.
- Set materiality benchmarks and scope high-risk accounts.
- Draft planning memo and risk assessment.

### B. Bottlenecks and pain points
- Data wrangling and standardization (account names change; inconsistent signs; vendor/customer name variants).
- Unstructured disclosures in PDF footnotes require manual reading.
- GL volume makes manual risk scanning impractical; high false negatives for rare patterns.
- Repetitive manual recalculation when client provides updated drafts.

### C. Why this is a strong candidate for Intelligent RPA
- Per Huang & Vasarhelyi, planning contains many structured and semi-structured tasks ideal for RPA:
  - Structured: file organization, TB/GL ingestion, data checks, common-size analytics.
  - Semi-structured: reviewing prior-year disclosures and extracting risk cues (NLP).
  - Unstructured: final risk assessment judgment supported by a cognitive assistant (IPA loop).
- Zhang highlights an IPA loop for planning: RPA organizes inputs → NLP extracts signals → cognitive assistant proposes risk → auditor decides and forwards to next phase. This directly maps to automating planning analytics and risk surfacing, then letting the audit manager confirm/override with professional judgment.

### D. Automation strategy (RPA + AI/ML blend)
- RPA layer (rules-based, deterministic):
  - File watcher to ingest TB/GL drafts and prior FS automatically.
  - Data validation and standardization (schema checks, sign normalization, COA mapping).
  - Deterministic analytics (YoY, common-size, ratio library) and rules (negative balances, new/dropped accounts).
  - Exception routing, audit logs, reproducible outputs (Excel, docx, dashboards).
- IPA layer (ML/NLP for cognitive assistance):
  - NLP of prior FS footnotes to extract risk topics (going concern, contingencies, related parties, significant estimates).
  - GL anomaly detection combining heuristics with unsupervised models (e.g., IsolationForest/PyOD).
  - Change-point detection and seasonality-aware anomalies for revenue/expenses.
  - Risk scoring model that aggregates rule-based red flags, NLP signals, and ML anomaly scores into account-level and transaction-level risk.
- Human-in-the-loop:
  - Manager reviews risk heatmap and top-transaction exceptions, adjusts weights/thresholds, and documents rationale.
  - This mitigates detection risk per Huang & Vasarhelyi’s Stage 4; evaluation compares IPA results to manual planning before go-live.

---

## 2) Proposed System Architecture

Text diagram:
1. Data Ingestion (watcher/CLI; Pandas, pdfplumber/Selenium if needed) 
-> 2. Data Validation & Standardization (pandera/Great Expectations; rapidfuzz for name matching; COA mapping) 
-> 3. Core Analytical Procedures (Pandas/statsmodels; horizontal/vertical, ratios) 
-> 4. Rules Engine (deterministic TB/GL checks, Benford, JE heuristics) 
-> 5. NLP Risk Extraction (pdfplumber + spaCy + sentence-transformers) 
-> 6. ML Anomaly Detection (PyOD/scikit-learn; ruptures for change points) 
-> 7. Risk Scoring & Prioritization (weighted aggregation; configurable YAML) 
-> 8. Output Generation (xlsxwriter/python-docx/Plotly) 
-> 9. Orchestration & Monitoring (Typer/Prefect/APScheduler; logging) 
-> 10. Human Review & Feedback (override thresholds; accept/waive exceptions; update config)

Data flow explanation:
- The watcher/CLI triggers on new TB/GL/FS files. A standardization layer enforces schema and harmonizes labels across years (handle Amazon vs Amazon.com, Inc. with fuzzy/entity resolution).
- Analytical and rules layers produce account-level red flags (e.g., unusual fluctuations, negative balances), while the NLP layer extracts narrative risks from prior footnotes and summaries.
- ML models flag transaction-level anomalies in the GL. All signals feed a configurable risk scoring module to rank accounts and transactions.
- Outputs include a planning analytics workbook, a risk heatmap, JE exception lists, and a draft planning memo. A review UI/process records human adjustments, closing the IPA loop.

---

## 3) Detailed Implementation Approach (Python Stack)

| Component Task | Proposed Method (RPA vs IPA) | Key Python Libraries & Repositories |
|---|---|---|
| File ingestion from a “Planning” folder; optional ERP portal scrape | RPA: deterministic file watcher or scheduled CLI. Optional browser automation for ERP exports. | watchdog or APScheduler; Typer (CLI); Selenium/Playwright (if portal downloads) |
| Unzip, parse TB/GL CSV/XLSX; parse prior FS PDFs | RPA: deterministic parsing | pandas; openpyxl; pyxlsb (if needed); pdfplumber or PyMuPDF; camelot or tabula-py for PDF tables; pytesseract + OpenCV if scanned |
| Data validation (schema and quality checks) | RPA: rule-based validations | pandera or Great Expectations for schema; cerberus; pytest for unit tests |
| Standardize COA across years (name variants, sign conventions) | IPA (semi-structured matching) + RPA for rules | rapidfuzz (string matching), python-Levenshtein; dedupe.io (open-source dedupe) for entity resolution; pycountry (if needed); custom mapping YAML |
| Normalize GL structure (date, period, doc type, user, source, amount, account, subledger ref, description) | RPA: deterministic transforms | pandas; dateparser; python-slugify |
| Materiality and scoping calculator (benchmarks: revenue, assets, equity) | RPA: deterministic formulas with overrides | pandas; YAML config; statsmodels (if you want robust measures) |
| Horizontal/vertical analysis, YoY deltas, common-size | RPA: deterministic analytics | pandas; numpy |
| Ratio analytics library (liquidity, leverage, profitability, turnover) | RPA: deterministic | pandas; statsmodels for z-scores/robust z |
| Change-point and seasonality-aware anomaly detection for key accounts (e.g., revenue) | IPA: ML/statistics to detect regime shifts | ruptures (change-point detection); statsmodels (seasonal decomposition); scikit-learn |
| Rules-based red flags at TB-level (new/dropped accounts, sign flips, unusual negative balances, outlier deltas) | RPA: deterministic | pandas |
| Benford’s Law analysis (overall and per account class) | RPA/IPA-lite: statistical test | benford_py or custom; scipy.stats (chi-square) |
| Journal entry heuristics (round-dollar; weekend/after-hours; posted by admin; entries bypassing subledgers; unusual account pairs) | RPA: deterministic + IPA-lite frequency stats | pandas; mlxtend (frequent itemsets) |
| Unsupervised JE anomaly detection (account combos, amounts, timing, user) | IPA: ML model | PyOD (IsolationForest, LOF, COPOD), scikit-learn; umap-learn for embeddings/visualization |
| NLP on prior-year FS: extract risk topics (going concern, contingencies, impairments, related party, significant estimates) | IPA: NLP for semi-structured text | pdfplumber; spaCy (NER, dependency); sentence-transformers (SBERT) for semantic similarity; keybert or YAKE for keywords |
| Related party and contingent liability cue extraction (entity recognition, lexicon + embeddings) | IPA: rule-augmented NLP | spaCy; nltk; lexicon lists (custom YAML); sentence-transformers |
| Duplicate/near-duplicate transaction detection | IPA-lite: entity resolution | dedupe; rapidfuzz; recordlinkage |
| Name standardization (vendor/customer across periods) | IPA-lite: fuzzy/entity match | dedupe; rapidfuzz; networkx (optional relationship graphs) |
| Risk scoring and prioritization (account-level and transaction-level) | IPA: weighted aggregation with human-tunable config | pandas; numpy; YAML config; SHAP (optional explainability for ML) |
| Output: Planning Analytics Pack (Excel workbook with multiple tabs) | RPA: deterministic export | xlsxwriter/openpyxl; seaborn/plotly for charts |
| Output: Draft Planning Memo (sections auto-filled with analytics) | RPA: template population | python-docx; jinja2 for doc templates |
| Dashboard/heatmap (optional lightweight HTML report) | RPA: static HTML report | plotly; jinja2; weasyprint (PDF from HTML) |
| Orchestration and monitoring | RPA: scheduling and logs | Prefect or Dagster (open-source orchestrators); logging/json-logging; rich for CLI |
| Configuration management and reproducibility | RPA: config-driven | pydantic; pyyaml/toml; joblib for model persistence |
| Data standardization and audit trail for labels (Amazon vs Amazon.com, Inc.) | RPA/IPA-lite: maintain crosswalk with confidence scores | pandas; SQLite for a local lookup table; write-back of manual reviewer decisions |

---

## How the pieces work together (practical flow)

1) Ingestion and setup (RPA)
- Drop current TB/GL and prior-year FS in a watched folder or run a CLI command like: ipa-plan run --tb tb_2024.xlsx --gl gl_2024.csv --fs prior_fs_2023.pdf
- The system parses files, validates schemas (pandera/Great Expectations), and logs any exceptions.

2) Standardization and validation (RPA + IPA-lite)
- Normalize GL fields, assign standard account taxonomy, sign conventions.
- Build or update a COA crosswalk (prior to current) using rapidfuzz; surface low-confidence matches for human approval.
- Resolve entity name variants across periods with dedupe; log reviewer-approved merges to a persistent mapping.

3) Core analytics and rules (RPA)
- Compute horizontal/vertical analyses and ratios; flag significant changes vs prior-year expectations.
- TB rules: new/dropped accounts, sign flips, unexpected negative balances, material YoY variances.
- Benford analysis identifies numeric distribution anomalies per account class.

4) NLP risk extraction from prior FS (IPA)
- Extract footnotes and MD&A-like sections; detect and summarize risk topics (going concern, contingencies, significant estimates, impairments, related party).
- Link extracted risks to TB accounts (e.g., impairment → PPE/intangibles; litigation → accruals).

5) GL anomaly detection (IPA)
- Heuristic JE risk features: round-dollar, period-end spikes, off-hours postings, unusual account pairings, entries without standard subledger references.
- ML anomaly detection: Use PyOD (e.g., IsolationForest) on engineered features (amount size, time-of-day, user frequency, account-pair rarity). Score and rank entries.

6) Risk scoring and prioritization (IPA)
- Aggregate signals into:
  - Account Risk Score (weights from deltas, ratios, NLP risks, Benford, JE concentration).
  - Transaction Risk Score (heuristics + ML anomaly score).
- Provide configurable weights and thresholds in YAML; manager can tune to context, explicitly addressing detection risk concerns (Huang & Vasarhelyi Stage 4).

7) Outputs and IPA loop closure (RPA + human review)
- Produce:
  - Excel Planning Pack: tabs for TB analytics, ratios, risk heatmap, Benford, JE exceptions, ML anomaly list, proposed scope and materiality roll-forward.
  - Draft Planning Memo (docx) pre-populated with analytics and suggested risk assessments per account.
  - Exception CSVs for follow-up.
- Manager reviews, adjusts weights/thresholds, approves/waives exceptions. Changes are logged to a config and justification file. The refined settings feed internal-control scoping next, aligning with Zhang’s IPA loop.

---

## Research alignment notes

- Task selection and design:
  - Structured tasks (file setup, TB/GL ingestion, deterministic analytics) → RPA (Huang & Vasarhelyi).
  - Semi-structured tasks (processing prior FS text) → NLP (Zhang).
  - Unstructured judgment (final risk assessment) → auditor, assisted by a cognitive tool that aggregates AI/RPA outputs into a decision support view (Zhang’s IPA loop).
- Data compatibility and standardization:
  - Ensure digital, structured data; standardize labels across inputs (e.g., Amazon vs Amazon.com, Inc.) before automation (Huang & Vasarhelyi).
- Procedure modification:
  - Introduce a standardized TB/GL schema and COA crosswalk; add fields needed for analytics (user, source, timestamp) to improve automation success (Huang & Vasarhelyi Stage 2).
- Implementation and evaluation:
  - In-house Python stack; pilot on one engagement; compare outputs vs manual planning; assess effects on detection risk and monitor error rates (Huang & Vasarhelyi Stages 3–4).
- IPA’s role:
  - Use AI/ML to augment, not replace, auditor judgment. Apply ML where rules are insufficient (GL anomalies, nuanced text), with transparent scoring and human overrides (Zhang).

---

## Starter deliverables you’ll get out-of-the-box

- Account-level:
  - Risk heatmap: accounts ranked by composite risk score.
  - Flags: new/dropped accounts; sign flips; top YoY changes; ratios off-trend; Benford exceptions.
  - NLP tags from prior FS footnotes linked to accounts (e.g., impairment risk tagged to intangibles).
- Transaction-level:
  - Sorted exception list of JEs by risk score; filters for period-end spikes, off-hours postings, round-dollar.
  - Unusual account pairings and entries bypassing subledgers.
- Planning documents:
  - Excel analytics pack and docx planning memo draft with inserted charts/tables and a section summarizing risk drivers.
  - Materiality and scoping suggestions (benchmarks and rationale), configurable and recorded for review.

---

## Minimal viable build (2–3 weeks)

- Week 1:
  - Watcher/CLI, data validation/standardization, core analytics (YoY, common-size, ratios), TB rules, Excel output.
- Week 2:
  - NLP on prior FS footnotes (topic/keyword detection), JE heuristics, Benford analysis, draft planning memo.
- Week 3:
  - ML anomaly detection for GL, risk scoring config, manager review flow (override and log), refine outputs.

---

## Security and governance

- Local processing, open-source only; no external API calls by default.
- Logging for every step (data checks, mapping decisions, overrides).
- Config-driven run with versioned YAML; store risk scoring weights and rationale to support review queries.

---

## Next steps (what I need from you)

- A sample TB and GL export with column headers and 100–1,000 lines.
- Prior-year FS (PDF).
- Your preferred materiality benchmarks and any firm-standard planning ratio set.
- Known high-risk areas from prior years (to calibrate initial weights).

Once you provide sample files, I’ll deliver a runnable CLI scaffold with:
- A standard schema for TB/GL.
- Validations and core analytics.
- A first-pass risk report and draft memo you can review and tune.