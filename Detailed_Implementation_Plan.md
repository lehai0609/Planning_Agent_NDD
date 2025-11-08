# Hybrid Approach Implementation Plan (TB + FS View Rolled from TB with Dimension-Agnostic Analytics)

Version: 1.0  
Target runtime: Python 3.13  
Core libs: pandas, pyarrow, pandera, pydantic, typer, xlsxwriter, plotly

**Implementation Status:** Stages 0-9 complete (RPA layer production-ready)  
**Last Updated:** 2025-11-02

---

## Overview

Purpose: provide an intelligent, notebook-driven audit planning pipeline. The entire workflow is executed within a single Jupyter notebook for clarity, reproducibility, and ease of review.

Scope: automates data ingestion, standardization, FS mapping, planning metric computation, and risk analytics for the audit planning phase. No client-system writes or external integrations.

Workflow model:

* Single notebook (`planning_stage.ipynb`) performs all steps:

  1. **Setup & Config Load** – imports paths, parameters, and client/year config from YAML.
  2. **Data Ingestion** – reads TB/GL from Excel, CSV, or PDF using `pandas`, `pyarrow`, `pdfplumber`.
  3. **Standardization** – normalizes Dr/Cr balances, computes movements, and validates using `pandera`.
  4. **FS Mapping** – maps COA to FS sections with fallback heuristics and logs mapping diagnostics.
  5. **Planning Analytics** – computes materiality, BEN, SAD, and risk flags.
  6. **Visualization & Output** – displays summaries, diagnostics, and charts inline within the notebook.

Project structure:

```
project_root/
  ├── notebook/        # Jupyter notebooks (main: planning_stage.ipynb)
  ├── data/            # Raw TB, GL, and reference datasets
  ├── configs/         # YAML configuration files per client/year
  └── artifacts/       # Generated parquet files, logs, and run manifests
```

Outputs:

* Validated datasets and standardized TB/GL parquet snapshots.
* Inline visual analytics and tables for immediate review within the notebook.
* Optional export of key tables or metrics to `artifacts/` for documentation.

Design principles:

* **Simplicity over architecture** – minimal abstraction, direct readable code.
* **Transparency** – every transform visible and verifiable in notebook cells.
* **Reproducibility** – deterministic data handling with fixed seeds and schema validation.
* **Maintainability** – compact, modular cell structure instead of over-engineered modules.

Environment:

* Python 3.13 with pinned dependencies in `pyproject.toml`.
* Uses open-source libraries only: `pandas`, `pyarrow`, `pandera`, `plotly`, `typer`, `rich`, etc.
* No runtime internet dependency.

Deliverables:

* A single self-contained notebook demonstrating the full audit planning pipeline.
* Clean, validated, and analyzed data ready for use in further audit stages.


---

## Stage 0: Scaffolding (config, paths, types, IO utils)

Objective: establish the minimal project skeleton and runtime environment required to execute the single-notebook audit planning workflow. Focus on simplicity, readability, and quick reproducibility rather than heavy modularization.

## Folder structure

```
project_root/
  ├── notebook/
  │     └── planning_stage.ipynb     # the single notebook controlling all pipeline stages
  ├── data/                          # input TB, GL, and reference datasets
  ├── configs/                       # YAML config per client/year
  └── artifacts/                     # parquet outputs, logs, diagnostics
```

## Environment setup

* Python version: **3.13**
* Dependency management: **uv** or **Poetry**, minimal locked dependencies.
* `pyproject.toml` defines only essential libraries:

  ```toml
  [project]
  name = "planning_agent_ndd"
  version = "0.1.0"
  requires-python = ">=3.12"
  dependencies = [
      "pandas>=2.2.0",
      "pyarrow>=15.0.0",
      "pandera>=0.18.0",
      "plotly>=5.18.0",
      "pdfplumber>=0.11.0",
      "pyyaml>=6.0",
      "rich>=13.7.0"
  ]
  ```

## Notebook structure (`planning_stage.ipynb`)

Each section of the notebook is labeled and collapsible:

1. **Setup** – import dependencies, load `.env`, load YAML configs.
2. **Data Ingestion** – load TB and GL from `/data`, validate presence and format.
3. **Standardization** – unify Dr/Cr, compute movements, enforce schema validation.
4. **FS Mapping** – apply COA–FS mapping rules, flag unmapped accounts.
5. **Planning Analytics** – compute materiality, BEN, SAD, and risk flags.
6. **Visualization & Summary** – show analytics and charts inline with Plotly and Pandas.
7. **Artifact Export (Optional)** – write standardized datasets and logs to `/artifacts`.

## Config files

YAML-based config per client-year, e.g.:

```yaml
client: ABC
fiscal_year: 2025
files:
  tb: data/ABC_2025_TB.xlsx
  gl: data/ABC_2025_GL.xlsx
settings:
  materiality_threshold: 0.05
  currency: VND
```

## Validation and logging

* Schema checks via **Pandera**.
* Inline `assert` and `rich` logging for clarity.
* Each run creates a simple JSON manifest in `artifacts/run_log.json` with timestamps, row counts, and validation results.

## Guiding principles

* Minimal dependencies, no class-based overdesign.
* Prefer explicit over abstract.
* Keep each notebook cell atomic and documented.
* Support quick reruns and visual verification inside the notebook.

Result: a clean, ready-to-run notebook-driven environment requiring no additional scaffolding beyond these four folders and one YAML config per client.


## Stage 1: TB ingestion

Objective: ingest the trial balance (TB) from `/data` into the notebook exactly as provided, keep it raw, and create immutable snapshots in `/artifacts`. No validation, no transformation, no standardization. End the stage by showing a clear preview inside the notebook.

Scope and constraints

* Audience: accountant end‑user. Prioritize clarity and simplicity.
* Ingestion only. Validation and standardization occur in Stage 2 and Stage 3.
* Deterministic, reproducible, and transparent. No hidden cleanup.

Inputs

* Path configured in `configs/<client>/<year>/planning.yml → files.tb`.
* Supported formats: Excel (`.xlsx/.xls`), CSV (`.csv`), Parquet (`.parquet`).
* Optional read hints (used only to open the file, not to transform data):

  * `tb_sheet` (Excel worksheet name)
  * `tb_header` (zero‑based header row index)
  * `tb_encoding` (CSV encoding)
  * `delimiter` or `sep` (CSV delimiter if non‑standard)

Outputs (artifacts + on‑screen)

* Artifacts (immutable):

  * `artifacts/TB_RAW.parquet` – 1:1 snapshot of the ingested table as read by the IO engine.

  * A compact preview: first 20 rows, row/column counts, and the raw column header list exactly as read.

Canonical expectations (documented, not enforced here)

* Typical TB columns may include account code/name and opening/period/closing Dr/Cr sides. Do not enforce presence or names in this stage. Merely record what exists.
* Duplicates, totals/subtotals, or merged hierarchies may appear. Do not alter or remove them here.

Notebook cell outline (no code yet)

1. **Locate config and source**

   * Read client/year config. Resolve absolute path for `files.tb`. Fail early if the file is missing.
2. **Open TB using minimal hints**

   * Choose reader by extension. Apply only IO parameters necessary to open the file. Do not coerce numeric strings, do not trim whitespace, do not rename columns.
3. **Name the dataset**

   * Keep an in‑memory variable named `df_tb_raw` (raw frame). Do not create derived frames.
4. **Snapshot artifacts**

   * Write `df_tb_raw` to `artifacts/TB_RAW.parquet` without schema changes.
   * Generate and save `TB_RAW_COLUMNS.json` (ordered headers and dtypes as read).
   * Update `run_manifest.json` with file metadata and simple shape metrics.
5. **Preview in notebook**

   * Display: row count, column count, ordered column list, and a 20‑row sample.
   * Provide a short note showing where snapshots were saved.

Non‑goals and boundaries

* Do not rename headers to canonical names.
* Do not coerce numbers, change decimal symbols, or strip thousands separators.
* Do not drop blank rows, totals, or subtotals.
* Do not parse account hierarchy or leaf levels.
* Do not run schema checks, mapping diagnostics, or anomaly rules.

Edge cases to handle visibly (without changing data)

* Multi‑row headers in Excel: select the declared header row only and keep labels as‑is.
* Mixed types within columns: accept as read; dtype normalization is deferred to Stage 2.
* Large files: if memory pressure occurs, prefer chunked read for CSV with immediate write‑through to Parquet, still preserving raw content.

Acceptance criteria

* The notebook shows a clear preview of the TB exactly as provided.
* `artifacts/TB_RAW.parquet` exist and match the previewed structure.
* `run_manifest.json` includes file metadata and shape metrics for this run.

Done when

* An accountant can open the notebook, see the raw TB preview, and confirm that a faithful snapshot exists in `/artifacts`, with no alterations to the data. Subsequent stages will rely on these artifacts for validation and standardization.


## Stage 2: TB validation

Objective: evaluate the raw TB from Stage 1 in a read‑only manner and present a clear, accountant‑friendly validation dashboard **inside the notebook only**. No transformations. No renaming. No datatype coercion. No artifacts written.

Status carried from Stage 1

* In‑memory source: `df_tb_raw` (exactly as ingested and previewed).

Scope and constraints

* Display‑only reporting. All checks are descriptive. Nothing is persisted to disk in this stage.
* Keep language simple and operational for accountants.

Inputs

* `df_tb_raw`.
* Optional display hints from config: common header aliases for labeling the dashboard only.

Validation checklist (aligned to the original intent)

### A) `validate_tb_raw` (display‑only)

Purpose: preview schema health without mutating data or halting the notebook.

* **Schema selection by strictness**

  * `relaxed=True` (default for incremental adoption): broader acceptance of column names and types; issues shown as *warnings*.
  * `relaxed=False` (strict view): tighter expectations; issues shown as *errors to be enforced in Stage 3*.
* **Expected fields (by role, not by exact header)**

  * Account identifier column ("account_code"‑like).
  * Zero or more of: opening_dr, opening_cr, period_dr, period_cr, closing_dr, closing_cr.
* **Display result**

  * Summarize first 10 issues (header problems, missing key roles, impossible types). Do **not** raise; mark which items will become hard failures in Stage 3.

### B) `soft_checks_tb` (advisory, no data changes)

1. **Duplicate account identifier**

   * Heuristic detect an account‑code‑like column and report duplicate values count + top examples.
2. **TB tie‑out at leaf level (advisory)**

   * When closing_dr/closing_cr‑like columns are present and hierarchy is detectable by prefix/length patterns, compute debit minus credit at *leaf* rows only (ignore apparent parents). Tolerance: absolute 1.0 (same currency units). Report imbalance total and top offending rows.
   * If leaf detection is ambiguous at raw stage, mark check as *indeterminate—will be re‑run post‑standardization in Stage 3*.
3. **Closing arithmetic consistency**

   * Where columns that look like `closing_dr` and `closing_cr` exist alongside a net `closing` column (rare in raw TBs), verify: `closing ≈ closing_dr − closing_cr` within tolerance 1.0. Report mismatches.
4. **Null coverage on key fields**

   * For the account‑code‑like column: report null/blank count.
   * For an account‑name‑like column: compute % missing; flag *warning* if >10%.
5. **P&L → Retained earnings (4212) reconciliation (advisory)**

   * If a retained‑earnings account (e.g., code contains `4212`) appears and closing Dr/Cr columns exist, present an indicative link:

     * Display the closing balance of 4212.
     * If separate current‑year profit/transfer lines are visible, show their sums; otherwise mark *not observable at raw stage*. Full reconciliation awaits Stage 3 (after standardized signs and 911 transfers logic).

### C) Notebook dashboard (display‑only)

* **Summary block**: rows, columns, duplicate headers, suspected key columns, null overview, strictness mode used.
* **Findings block**: ranked list from B(1)–B(5), each with:

  * Severity (info/warn/error in strict view),
  * Short rationale,
  * Next action pointer (what Stage 3 will enforce or compute).
* **Context preview**: first 20 raw rows of `df_tb_raw`.

Notebook cell outline (no code)

1. Select strictness (`relaxed=True` by default) and describe the consequences for Stage 3.
2. Run header + role detection and present the `validate_tb_raw` summary (first 10 issues only).
3. Run `soft_checks_tb` items B(1)–B(5) with clear labels. If a prerequisite column is missing/ambiguous, show the check as *skipped* with reason.
4. Render the dashboard blocks and the raw preview. Stop—do not write files.

Non‑goals and boundaries

* Do not fix or transform any data.
* Do not enforce or save a canonical schema.
* Do not produce any files or manifests.

Acceptance criteria

* An accountant can understand the TB’s readiness and the likely work needed in Stage 3 purely from the on‑screen dashboard.
* `df_tb_raw` remains unchanged and available for standardization in Stage 3.

Done when

* The notebook shows a clear, prioritized validation dashboard plus a raw preview, with **no** artifacts created in this stage.


## Stage 3: TB standardization + FS dimension tagging
# Stage 3 — TB Standardization + FS Dimension Tagging

**Revised to use Trial Balance period Dr/Cr turnovers for all class 5–8 P&L calculations.**

This stage remains notebook‑driven and compatible with Stage 1 (ingest) and Stage 2 (validation). It standardizes the trial balance (TB) into a clean schema and tags each leaf account with Financial Statement (FS) dimensions according to your FS mapping markdown. It also derives Balance Sheet amounts from closing Dr/Cr and P&L amounts from **period Dr/Cr** for classes 5–8 without needing a separate GL‑911 view.

---

## Inputs and Outputs

**Inputs (in‑memory):**

* `df_tb_raw` from Stage 1.
* Stage‑2 alias map and any warnings (duplications, nulls, hierarchy hints).

**Output dataframe:**

* `df_tb_std` with standardized numeric fields and FS dimensions, persisted to `artifacts/std/tb_std.parquet` with a small JSON sidecar of coverage stats and schema version.

**Contract with later stages:**

* Stage 4 consumes `df_tb_std` to roll BS and IS totals and to render statements.

---

## Minimal column schema (target)

* **Keys:** `fiscal_year:int`, `account_id:str`, `account_name:str`, `account_parent:str`, `account_level:int`, `is_leaf:bool`.
* **TB numerics:** `opening_dr, opening_cr, period_dr, period_cr, closing_dr, closing_cr` (float; NaN→0 during arithmetic).
* **Derived numerics:**

  * `closing_signed = closing_dr − closing_cr`
  * `movement_signed = period_dr − period_cr`
  * `closing_debit = max(closing_signed, 0)`, `closing_credit = max(−closing_signed, 0)`
  * `movement_debit = max(movement_signed, 0)`, `movement_credit = max(−movement_signed, 0)`
  * `bs_amount:float` (class 1–4 only, from closing Dr/Cr)
  * `pl_amount:float` (class 5–8 only, from period Dr/Cr)
* **FS dims:** `fs_statement:{BS|IS|CF|UNMAPPED}`, `fs_section:str`, `fs_line:str`, `fs_pick:{debit|credit|net}`, `match_type:{exact|prefix|range|name|fallback}`, `match_ratio:float`.

---

## Cell Plan (no code)

### 3.0 Bring forward raw and bind roles

1. Copy `df_tb_raw`. Do not mutate the Stage‑1 frame.
2. Bind columns to canonical roles using Stage‑2 alias results:
   `account_id`, `account_name`, `opening_dr`, `opening_cr`, `period_dr`, `period_cr`, `closing_dr`, `closing_cr`.
3. Assert `account_id` non‑null. If any nulls, stop with a clear message listing offending rows.

### 3.1 Numeric normalization and basic checks

4. Coerce all Dr/Cr role columns to numeric. Fill NaN with 0 for arithmetic only.
5. Compute `closing_signed`, `movement_signed`, and their debit/credit splits as listed above.
6. If any net `closing` exists in the raw, check `closing ≈ closing_dr − closing_cr` within tolerance 1.0. Escalate to **error** here.

### 3.2 Deduplicate and hierarchy helpers

7. Normalize `account_id` to zero‑padded string; trim `account_name`.
8. Collapse duplicates by `(fiscal_year, account_id)` by summing numeric fields; keep first `account_name`. Log count reduced.
9. Build hierarchy fields:

   * `account_parent` = first 3 digits of `account_id` (or your local rule)
   * `account_level` = length of `account_id`
   * `is_leaf` = code not a prefix of any other code present

### 3.3 Balance Sheet derivation (classes 1–4)

10. For **classes 1–4 only**, set `bs_amount` from **closing Dr/Cr** and apply your mapping’s no‑offsetting rules:

* Receivables/Payables split by side:

  * 131 **debit side** → Trade receivables; 131 **credit side** → Advances from customers.
  * 331 **credit side** → Trade payables; 331 **debit side** → Advances to suppliers.
  * 333 **credit side** → Taxes and levies payable.
* Inventory allowance 2294 and all **accumulated depreciation 214x** are **separate negative lines**; do not net against cost.
* PPE/Intangibles/Investments: cost accounts use **debit closing**; contra accounts remain separate.

### 3.4 Profit & Loss derivation (classes 5–8) — **revised to use TB period Dr/Cr**

11. Ignore `closing_*` for classes 5–8. Use **period turnovers**:

* For **credit‑nature** income accounts, set per‑account `pl_amount = period_cr − period_dr`.

  * Revenue 511/512
  * Financial income 515
  * Other income 711
* For **debit‑nature** expense accounts, set per‑account `pl_amount = period_dr − period_cr`.

  * COGS 632; Financial expense 635; Selling 641; G&A 642; Other expense 811; CIT 821 (split 8211 current, 8212 deferred, if present)

12. Build **net revenue** FS line: `(511 + 512 credits) − (521 + 531 + 532 debits)` using period turnovers. In practice implement by tagging 521/531/532 as negative contributors to the same FS line, or by a post‑aggregation adjustment.
13. Respect any account‑level exceptions defined in the mapping markdown (e.g., sub‑codes that route to different FS lines).
14. Optional cross‑check if a GL‑911 view is available: aggregate 911‑paired turnovers and compare totals to TB‑derived `pl_amount` at line or section level; report deltas but do not block Stage 3.

### 3.5 FS tagging using the provided mapping

15. Populate `fs_statement`, `fs_section`, `fs_line`, and `fs_pick` by this order:

1) Exact account match in mapping.
2) Longest‑prefix match (e.g., 5111 → 511* rule) where allowed.
3) Declared ranges from the mapping file.
4) Name contains/fuzzy fallback if mapping allows it.
5) Leading‑digit fallback only if none above apply.

16. Record `match_type` and `match_ratio` so unmapped coverage is transparent.
17. Enforce side‑aware routing where the mapping requests it (e.g., 131 debit → receivables vs 131 credit → advances from customers).

### 3.6 Controls and tie‑outs

18. **Leaf tie‑out**: on **leaf** rows, check `Σ closing_debit − Σ closing_credit ≈ 0` (tol 1.0). List top offenders.
19. **No‑offset checks**: confirm separate negative lines for 214x and 2294 exist and are not netted with their base accounts.
20. **BS balance preview**: `Assets − (Liabilities + Equity)` on tagged rows; show delta only.
21. **P&L internal checks**:

* Sum of per‑account `pl_amount` equals sum of section lines (e.g., Operating profit build‑up) under the mapping.
* `Net revenue` equals `(511+512 credits) − (521/531/532 debits)` from period turnovers.
* If 821 exists, verify sign convention: debit increases expense; ensure no negatives show unless mapping forces them.

### 3.7 Persist and summarize

22. Keep only standardized columns listed in the schema and persist to `artifacts/std/tb_std.parquet`. Write sidecar stats: row count, duplicate collapse count, unmapped count by `match_type`, BS balance delta, and P&L section totals.
23. Notebook prints a compact summary table:

* Row counts before/after dedup.
* Leaf tie‑out delta.
* Mapping coverage (% mapped by exact/prefix/range/name/fallback).
* `Net revenue`, `Gross profit`, `Operating profit`, `Profit before tax`, `CIT`, `Profit after tax` if your mapping defines these rollups.

---

## Acceptance Criteria

* `df_tb_std` contains all target columns and persists to parquet with schema version and coverage stats.
* **Classes 1–4:** `bs_amount` derived from closing Dr/Cr with receivable/payable side splits and separate negative lines for 214x and 2294.
* **Classes 5–8:** `pl_amount` populated from **period Dr/Cr** with correct sign by nature; net revenue computed as revenue credits less sales deductions debits.
* FS dimensions assigned according to the mapping markdown with `match_type` recorded; unmapped ratio reported.
* Controls pass or produce explicit, readable exception listings within the notebook.

---

## Compatibility Notes and Simplicity Guardrails

* Stage 3 never edits `df_tb_raw`. It reads raw, writes `df_tb_std`, and prints small previews only.
* Code stays in short notebook cells with clear headings. Prefer simple Pandas group‑bys and dictionary lookups for mapping. Avoid frameworks, classes, or custom decorators.
* All business rules trace back to the FS mapping markdown. Any rule not in that mapping should be flagged rather than hard‑coded.


# Stage 4 — Financial Statement Assembly, Tie‑outs, and Reporting

Notebook‑driven. Compatible with revised Stages 0–3. Uses `tb_std.parquet` from Stage 3.

---

## Goals

1. Roll up **Balance Sheet (BS)** and **Income Statement (IS)** from `df_tb_std`.
2. Enforce key controls: BS balances, P&L arithmetic, equity link‑through, and no‑offset rules.
3. Produce human‑readable outputs for review: compact tables in‑notebook plus an Excel export.

---

## Inputs and Outputs

**Inputs**

* `artifacts/std/tb_std.parquet` → `df_tb_std` with: keys, TB numerics, derived numerics, `bs_amount` (classes 1–4), `pl_amount` (classes 5–8), and FS dims (`fs_statement`, `fs_section`, `fs_line`, `fs_pick`, `match_type`, `match_ratio`).
* FS mapping markdown already applied in Stage 3 (we reuse its FS dims, not re‑map).
* Optional config (YAML or dict in the notebook): display order for sections/lines, rounding, and materiality thresholds.

**Outputs**

* `df_fs_lines`: one row per FS line with rolled amounts.
* `df_fs_sections`: one row per FS section with subtotals.
* `df_fs_statements`: statement‑level totals and control deltas.
* Excel: `artifacts/fs/financial_statements.xlsx` with BS and IS sheets and a Controls sheet.
* Sidecar JSON: `artifacts/fs/fs_controls.json` with control results and coverage metrics.

---

## Data Contracts and Conventions

* Stage 3 produced **positive** `bs_amount` aligned to each FS line’s nature (e.g., receivables debit‑side, payables credit‑side) and **positive** `pl_amount` aligned to economic sign (revenue positive, expenses positive). Presentation uses positive numbers; contra accounts appear as separate lines.
* FS dims from Stage 3 are the single source of truth for line routing. Stage 4 does not modify tagging, only aggregates.
* Materiality: a single display threshold (e.g., 1.0) for visual suppress only. Do not apply thresholds to controls.

---

## Cell Plan (no code)

### 4.0 Load and prep

1. Load `tb_std.parquet` → `df_tb_std`. Print shape and a 20‑row preview of `[account_id, account_name, bs_amount, pl_amount, fs_statement, fs_section, fs_line, match_type]`.
2. Freeze a **report context** dict: `fiscal_year`, rounding decimals (e.g., 0 for VND), materiality, and an ordered list of sections/lines if not embedded in mapping.

### 4.1 Integrity prechecks

3. Verify must‑have columns exist. If missing, stop with a readable error suggesting to re‑run Stage 3.
4. Confirm **leaf tie‑out** already passed in Stage 3, but recompute a quick check: sum(closing_debit) ≈ sum(closing_credit) within tol 1.0. Log delta.
5. Compute quick coverage: `pct_unmapped = mean(fs_statement=="UNMAPPED")`. If > 0, list top 15 exposures by absolute `closing_signed` or `movement_signed`.

### 4.2 Build FS Line roll‑ups

6. Split the frame: `df_bs_src = df_tb_std[df_tb_std.fs_statement=="BS"]`, `df_is_src = df_tb_std[df_tb_std.fs_statement=="IS"]`.
7. **BS lines**: group `df_bs_src` by `[fs_section, fs_line]` and sum `bs_amount` → `df_bs_lines`.
8. **IS lines**: group `df_is_src` by `[fs_section, fs_line]` and sum `pl_amount` → `df_is_lines`.
9. Attach ordering keys from mapping or a local ordering table to keep human‑friendly sequence.

### 4.3 Balance Sheet assembly

10. Create `df_bs_sections`: group `df_bs_lines` by `fs_section` to produce subtotals.
11. Compute statement‑level totals: `Total Assets` vs `Total Liabilities + Equity`. Produce `bs_delta = Assets − (Liabilities + Equity)`.
12. **No‑offset validation**: confirm presence of separate lines for `Allowance/Provisions` and `Accumulated depreciation` with non‑positive display where expected. List any violations.
13. Optional analytics: receivable aging is out of scope here; keep only a disclosure that receivable/payable are not netted.

### 4.4 Income Statement assembly

14. From `df_is_lines`, compute conventional sub‑totals if your mapping declares them, else derive using standard identities:

* **Net revenue** = Revenue (511/512) − Sales deductions (521/531/532)
* **Gross profit** = Net revenue − COGS (632)
* **Operating profit** = Gross profit − Selling (641) − G&A (642) − other operating lines if mapping flags them as operating
* **Finance result** = Financial income (515) − Financial expense (635)
* **Other result** = Other income (711) − Other expense (811)
* **Profit before tax (PBT)** = Operating profit + Finance result + Other result
* **CIT expense** = 8211 (current) + 8212 (deferred)
* **Profit after tax (PAT)** = PBT − CIT

15. Store these subtotals in `df_is_sections` and a statement summary in `df_is_stmt`.

### 4.5 Equity linkage and period reconciliation

16. Extract Retained earnings account(s) (e.g., 421/4212) from `df_tb_std` and compute:

* `opening_re = opening_dr − opening_cr` per retained‑earnings code
* `closing_re = closing_dr − closing_cr`

17. Build a simple roll‑forward check: `opening_re + PAT + owner_changes ≈ closing_re`. Since owner changes are not yet modeled, compute `owner_changes = closing_re − opening_re − PAT` and present it as a diagnostic. If magnitude exceeds materiality × N (e.g., 5×), flag.

### 4.6 Controls summary

18. Controls to compute and record:

* **C1 BS balance**: `bs_delta` must be within tol 1.0.
* **C2 P&L arithmetic**: recompute PAT from `df_is_lines` components; must equal PAT in summary.
* **C3 Mapping coverage**: % unmapped lines, plus a table by `match_type`.
* **C4 Equity link**: `owner_changes` computed; report value and flag if large.
* **C5 Sign sanity**: lines expected non‑negative (e.g., Revenue) and expected non‑positive (e.g., Accumulated depreciation) checked for sign, then listed if violated.

### 4.7 Presentation and export

19. **Notebook tables**: render compact BS and IS tables with ordered sections, a column for amount, and optional percentage of total.
20. **Excel export**:

* Sheet `Balance Sheet`: sections and lines in order, with thousands separators and bracket negatives.
* Sheet `Income Statement`: same formatting, add sub‑totals as bold rows.
* Sheet `Controls`: list C1–C5 with pass/fail and key numbers.

21. Persist Parquet for downstream use: `artifacts/fs/fs_lines.parquet` (union of BS+IS lines), `artifacts/fs/fs_sections.parquet`, `artifacts/fs/fs_statements.parquet`.

### 4.8 Exceptions register

22. If any control fails, write `artifacts/fs/exceptions.csv` with columns: `control_id`, `item`, `value`, `threshold`, `notes`. The notebook prints a concise summary with the path.

---

## Acceptance Criteria

* BS and IS roll‑ups exist with ordered sections/lines and pass C1–C3. C4 reported with diagnostic owner changes.
* No‑offset rules respected: contra lines shown separately and not netted.
* Excel file saved with three sheets and correct totals; Parquet outputs persisted.
* Notebook shows: coverage table, BS delta, P&L sub‑totals, and equity diagnostic.

---

## Simplicity Guardrails

* Keep each operation a small cell. Prefer straightforward Pandas groupby and joins.
* Do not re‑implement mapping logic. Use Stage 3 dims.
* Avoid class‑based architectures and decorators. No hidden state; recompute from `tb_std` when needed.
* All thresholds and display order live in a small dict/YAML at the top of the notebook.

---

## Quick Checklist (for the notebook)

* [ ] Load `tb_std` and set report context.
* [ ] Run prechecks and unmapped exposure list.
* [ ] Aggregate BS and IS lines from `bs_amount` and `pl_amount`.
* [ ] Build statement subtotals and compute BS delta, PAT, and equity diagnostic.
* [ ] Render tables in notebook; export Excel and Parquet.
* [ ] Emit exceptions register if any control fails.


## Stage 5: Materiality (dimension-aware)

1) Objective and purpose
- Compute planning, performance, and trivial materiality thresholds based on policy and selected basis; attach to metadata and file materiality.json.

2) Files to create
- src/auditplan/analytics/materiality.py

3) Classes, functions, signatures
- def compute_materiality(tb_std: pd.DataFrame, policy: MaterialityPolicy, basis: str, dims: list[str] | None = None, logger: logging.Logger | None = None) -> dict
- def annotate_materiality(tb_std: pd.DataFrame, materiality: dict, value_col: str = "closing") -> pd.DataFrame

4) Detailed logic and algorithms
- Basis determination:
  - "assets": sum of BS Assets absolute amount.
  - "revenue": sum of IS Revenue absolute amount.
  - "pti": if available as a line in IS (Profit before tax) else fallback to net income absolute.
  - "equity": BS Equity absolute.
- compute_materiality:
  - Calculate base_value from fs_view (if available) or from tb_std filtered by fs_section.
  - planning = base_value * policy.rates.planning
  - performance = planning * policy.rates.performance
  - trivial = planning * policy.rates.trivial
  - Return dict with basis, base_value, planning, performance, trivial, fiscal_year.
- annotate_materiality:
  - Add column materiality_band to tb_std: "trivial_or_less", "between_trivial_and_performance", "above_performance".
  - Compare abs(closing) against thresholds.

5) Data schemas
- materiality.json:
  - { "basis": "assets|revenue|pti|equity", "base_value": float, "planning": float, "performance": float, "trivial": float, "fiscal_year": int }
- tb_std annotated: adds materiality_band:str.

6) Dependencies
- Stages 3–4 (fs_view helpful but not strictly required).

7) Acceptance criteria
- materiality.json exists; thresholds compute; tb_std annotated has materiality_band with 3-value domain.

8) Example snippet
```python
from auditplan.analytics.materiality import compute_materiality, annotate_materiality
mat = compute_materiality(df_std, cfg.materiality, cfg.materiality.basis, logger=logger)
write_json(mat, artifact_path(cfg.client, cfg.fiscal_year, "analytics", "materiality.json"))
df_std_mat = annotate_materiality(df_std, mat)
to_parquet(df_std_mat, artifact_path(cfg.client, cfg.fiscal_year, "std", "tb_std_annotated.parquet"), "1.0")
```

Effort: S (1-2h)

---

## Stage 6: Dimension-agnostic analytics engine

1) Objective and purpose
- Provide reusable analytics across arbitrary dimensions: YoY deltas, common-size, size %, z-scores.

2) Files to create
- src/auditplan/analytics/metrics.py

3) Classes, functions, signatures
- def compute_yoy(df: pd.DataFrame, group_cols: list[str], year_col: str = "fiscal_year", value_col: str = "closing") -> pd.DataFrame
- def compute_common_size(df: pd.DataFrame, within_cols: list[str], value_col: str = "closing", size_col_name: str = "size_pct") -> pd.DataFrame
- def compute_zscore(df: pd.DataFrame, group_cols: list[str], value_col: str = "closing", z_col_name: str = "z") -> pd.DataFrame
- def run_analytics(df: pd.DataFrame, index_cols: list[str]) -> pd.DataFrame

4) Detailed logic and algorithms
- compute_yoy:
  - Sort by group_cols + year_col; groupby group_cols; compute value, lag_1; yoy_abs = value - lag; yoy_pct = safe_div(yoy_abs, abs(lag)).
  - Fill yoy_pct NaN where lag=0 to 0.0; keep prior year nulls.
- compute_common_size:
  - Groupby within_cols + year; denom = group sum; size_pct = value / denom; handle denom=0 -> 0.0.
- compute_zscore:
  - Groupby group_cols; z = (value - mean)/std; if std=0 -> 0.0.
- run_analytics:
  - Accept index_cols e.g., ["account_id","fs_statement"] or any dimension; compute metrics and merge.
  - Output columns: index_cols + year_col + value_col + yoy_abs + yoy_pct + size_pct + z.

Error handling:
- Use numpy.nan_to_num for divisions by zero with clear logging on counts of protected divisions.

5) Data schemas
- tb_analytics.parquet:
  - dynamic columns: includes at least index_cols, fiscal_year:int, value:float, yoy_abs:float, yoy_pct:float, size_pct:float, z:float.

6) Dependencies
- Stages 3–5.

7) Acceptance criteria
- tb_analytics.parquet exists; yoy for current year computed; no NaN in yoy_pct except where expected (missing PY).

8) Example snippet
```python
from auditplan.analytics.metrics import run_analytics
index_cols = ["account_id", "fs_statement", "fs_section"]
analytics = run_analytics(df_std, index_cols)
to_parquet(analytics, artifact_path(cfg.client, cfg.fiscal_year, "analytics", "tb_analytics.parquet"), "1.0")
```

Effort: M (2–4h)

---

## Stage 7: Dimension-agnostic rules engine

1) Objective and purpose
- Flag deterministic conditions (new/dropped accounts, sign flips, unusual negatives) parameterized by dimensions.

2) Files to create
- src/auditplan/rules/tb_rules.py

3) Classes, functions, signatures
- def flag_new_dropped(df: pd.DataFrame, id_col: str, year_col: str = "fiscal_year") -> pd.DataFrame  # returns id_col, status in {"new","dropped","continuing"}
- def flag_sign_flip(df: pd.DataFrame, id_col: str, year_col: str = "fiscal_year", value_col: str = "closing") -> pd.DataFrame
- def flag_unusual_negative(df: pd.DataFrame, group_cols: list[str], value_col: str = "closing") -> pd.DataFrame
- def combine_flags(df: pd.DataFrame, flags: list[pd.DataFrame]) -> pd.DataFrame

4) Detailed logic and algorithms
- new/dropped:
  - Compute sets of ids in CY vs PY; left_only -> new; right_only -> dropped; else continuing.
- sign_flip:
  - For each id, compare sign(value) in CY vs PY; if opposite and both non-zero -> sign_flip=True.
- unusual_negative:
  - Within each class or fs_section where sign convention implies positive (e.g., Assets), flag rows with value < 0 and abs(value) > trivial or > percentile threshold; simple rule: value < 0.
- Output:
  - flags table: id_col, fiscal_year, new:bool, dropped:bool, sign_flip:bool, unusual_negative:bool, flags_count:int, flags:list[str].

5) Data schemas
- tb_flags.parquet:
  - account_id:str, fiscal_year:int, new:bool, dropped:bool, sign_flip:bool, unusual_negative:bool, flags_count:int, flags:str (comma-separated)

6) Dependencies
- Stages 3, 6 (z-scores optional; not required here).

7) Acceptance criteria
- Flags produced; totals for "new" match set difference; sign_flip only where PY exists.

8) Example snippet
```python
from auditplan.rules.tb_rules import flag_new_dropped, flag_sign_flip, flag_unusual_negative, combine_flags
f1 = flag_new_dropped(df_std, "account_id")
f2 = flag_sign_flip(df_std, "account_id")
f3 = flag_unusual_negative(df_std, ["fs_section"])
flags = combine_flags(df_std, [f1, f2, f3])
to_parquet(flags, artifact_path(cfg.client, cfg.fiscal_year, "analytics", "tb_flags.parquet"), "1.0")
```

Effort: S (1-2h)

---

## Stage 8: Excel reporting (TB + FS views)

1) Objective and purpose
- Generate an Excel planning pack with TB standardized, FS view, analytics, and flags. Add conditional formatting and basic charts.

2) Files to create
- src/auditplan/reports/excel.py

3) Classes, functions, signatures
- def build_excel_pack(client: str, year: int, tb_std: pd.DataFrame, fs_view: pd.DataFrame, analytics: pd.DataFrame, flags: pd.DataFrame, materiality: dict, out_path: str, logger: logging.Logger) -> None

4) Detailed logic and algorithms
- Create workbook with XlsxWriter:
  - Sheets:
    - "TB_Std": write tb_std with filters; freeze panes; thousands format.
    - "FS_View": write fs_view; pivot-like layout optional; totals row per section/year.
    - "Analytics": write analytics (subset: account_id, name, year, amount, yoy_pct, size_pct, z).
    - "Flags": write flags with filters and conditional formatting (flags_count > 0).
    - "Summary": materiality thresholds; key balance checks; simple KPI table.
  - Conditional formatting:
    - YoY% > thresholds.yoy_pct -> yellow/red.
    - abs(amount) > performance -> red.
  - Charts (optional for v1): YoY bar for top 10 accounts by size.

Error handling:
- Wrap workbook writes in try/finally to close workbook; on error, delete partial file and log exception.

5) Data schemas
- None new; uses inputs.

6) Dependencies
- Stages 3–7.

7) Acceptance criteria
- planning_pack.xlsx exists and opens; sheet counts as expected; conditional formatting present.
- Row counts match source tables.

8) Example snippet
```python
out_xlsx = artifact_path(cfg.client, cfg.fiscal_year, "outputs", "planning_pack.xlsx")
build_excel_pack(cfg.client, cfg.fiscal_year, df_std, fs_view, analytics, flags, mat, out_xlsx, logger)
```

Effort: M (2–4h)

---

## Stage 9: CLI orchestration

1) Objective and purpose
- Provide Typer CLI to run stages individually or as a pipeline, with structured logging and artifact management.

2) Files to modify/create
- src/auditplan/cli.py (create new)
- src/auditplan/rules/tb_rules.py (add FLAGS_SCHEMA_VERSION constant)

3) Commands and signatures
- def app() -> Typer
- @app.command() def run(config_path: str = "configs/default.yaml") -> None
- @app.command() def ingest(config_path: str = "configs/default.yaml") -> None
- @app.command() def validate(config_path: str = "configs/default.yaml") -> None
- @app.command() def standardize(config_path: str = "configs/default.yaml") -> None
- @app.command() def fsview(config_path: str = "configs/default.yaml") -> None
- @app.command() def analytics(config_path: str = "configs/default.yaml") -> None
- @app.command() def rules(config_path: str = "configs/default.yaml") -> None
- @app.command() def report(config_path: str = "configs/default.yaml") -> None
- @app.command() def version() -> None

Note: Logger initialized via get_logger_with_context(client=cfg.client, year=cfg.fiscal_year, run_id=uuid4())

4) Detailed logic and orchestration flow
- run:
  - Load cfg; init logger with get_logger_with_context(cfg.client, cfg.fiscal_year, run_id); ensure dirs.
  - Stage 1: load_tb_raw -> write parquet with TB_RAW_SCHEMA_VERSION and input_path metadata.
  - Stage 2: validate_tb_raw + soft_checks_tb + write_validation_report.
  - Stage 3: to_tb_std + load_or_generate_coa_map (auto-generates VN COA if config.coa_map empty) + tag_fs_dimensions (from auditplan.standardize.coa) -> write parquet with TB_STD_SCHEMA_VERSION.
  - Stage 4: build_fs_view + check_fs_balance (persist result to meta/fs_balance.json) -> write parquet with FS_VIEW_SCHEMA_VERSION.
  - Stage 5: compute_materiality -> write materiality.json using write_json(path, obj).
  - Stage 6: run_analytics with explicit index_cols and value_col -> write parquet with ANALYTICS_SCHEMA_VERSION.
  - Stage 7: flag_new_dropped + flag_sign_flip + flag_unusual_negative -> combine_flags -> write parquet with FLAGS_SCHEMA_VERSION.
  - Stage 8: build_excel_pack.
  - Write meta/run.json with run_id, timestamps, schema versions, config_hash, tb_input_hash.
  - Catch exceptions; log and exit non-zero.

5) Dependencies
- All prior stages implemented.

6) Acceptance criteria
- auditplan run completes without error on sample data; all artifacts present.
- Non-zero exit code and clear message upon failure.

7) Example CLI snippet
```python
import typer
from uuid import uuid4
from datetime import datetime

# Core utilities
from auditplan.utils.config import load_config
from auditplan.utils.logging import get_logger_with_context
from auditplan.utils.paths import ensure_artifact_dirs, artifact_path
from auditplan.utils.io import read_parquet, to_parquet, write_json, compute_file_hash

# Stage 1: Ingestion
from auditplan.ingest.tb import load_tb_raw

# Stage 2: Validation
from auditplan.validate.validators import validate_tb_raw, soft_checks_tb, write_validation_report
from auditplan.validate.schemas import TB_RAW_SCHEMA_VERSION, ANALYTICS_SCHEMA_VERSION

# Stage 3: Standardization
from auditplan.standardize.tb import to_tb_std, TB_STD_SCHEMA_VERSION
from auditplan.standardize.coa import load_or_generate_coa_map, tag_fs_dimensions

# Stage 4: FS Rollup
from auditplan.analytics.fs_rollup import build_fs_view, check_fs_balance, FS_VIEW_SCHEMA_VERSION

# Stage 5: Materiality
from auditplan.analytics.materiality import compute_materiality

# Stage 6: Analytics
from auditplan.analytics.metrics import run_analytics

# Stage 7: Rules
from auditplan.rules.tb_rules import flag_new_dropped, flag_sign_flip, flag_unusual_negative, combine_flags, FLAGS_SCHEMA_VERSION

# Stage 8: Reporting
from auditplan.reports.excel import build_excel_pack

app = typer.Typer()

@app.command()
def run(config_path: str = "configs/default.yaml"):
    """Run the complete audit planning pipeline."""
    cfg = load_config(config_path)
    run_id = str(uuid4())
    logger = get_logger_with_context(client=cfg.client, year=cfg.fiscal_year, run_id=run_id)
    ensure_artifact_dirs(cfg.client, cfg.fiscal_year)
    
    started_at = datetime.utcnow().isoformat()
    
    try:
        # Stage 1: Ingestion
        logger.info("stage1_start", extra={"stage": "ingestion"})
        df_raw = load_tb_raw(cfg, logger)
        to_parquet(
            df_raw, 
            artifact_path(cfg.client, cfg.fiscal_year, "raw", "tb_raw.parquet"), 
            TB_RAW_SCHEMA_VERSION,
            metadata={"input_path": cfg.tb_input_path}
        )
        
        # Stage 2: Validation
        logger.info("stage2_start", extra={"stage": "validation"})
        df_raw = validate_tb_raw(df_raw, logger)
        soft_report = soft_checks_tb(df_raw, logger)
        write_validation_report(soft_report, cfg.client, cfg.fiscal_year)
        
        # Stage 3: Standardization
        logger.info("stage3_start", extra={"stage": "standardization"})
        df_std = to_tb_std(df_raw, cfg, logger)
        coa_map = load_or_generate_coa_map(cfg, df_std, logger)
        df_std = tag_fs_dimensions(df_std, coa_map, logger)
        to_parquet(
            df_std, 
            artifact_path(cfg.client, cfg.fiscal_year, "std", "tb_std.parquet"), 
            TB_STD_SCHEMA_VERSION
        )
        
        # Stage 4: FS View
        logger.info("stage4_start", extra={"stage": "fs_rollup"})
        fs_view = build_fs_view(df_std, value_col="closing", logger=logger)
        fs_balance = check_fs_balance(fs_view, logger)
        to_parquet(
            fs_view, 
            artifact_path(cfg.client, cfg.fiscal_year, "analytics", "fs_view.parquet"), 
            FS_VIEW_SCHEMA_VERSION
        )
        write_json(
            artifact_path(cfg.client, cfg.fiscal_year, "meta", "fs_balance.json"),
            fs_balance
        )
        
        # Stage 5: Materiality
        logger.info("stage5_start", extra={"stage": "materiality"})
        mat = compute_materiality(df_std, cfg.materiality, cfg.materiality.basis, logger=logger)
        write_json(
            artifact_path(cfg.client, cfg.fiscal_year, "analytics", "materiality.json"),
            mat
        )
        
        # Stage 6: Analytics
        logger.info("stage6_start", extra={"stage": "analytics"})
        analytics = run_analytics(
            df_std, 
            index_cols=["account_id", "fs_statement", "fs_section"],
            value_col="closing",
            logger=logger
        )
        to_parquet(
            analytics, 
            artifact_path(cfg.client, cfg.fiscal_year, "analytics", "tb_analytics.parquet"), 
            ANALYTICS_SCHEMA_VERSION
        )
        
        # Stage 7: Rules
        logger.info("stage7_start", extra={"stage": "rules"})
        f1 = flag_new_dropped(df_std, "account_id")
        f2 = flag_sign_flip(df_std, "account_id")
        f3 = flag_unusual_negative(df_std, ["fs_section"])
        flags = combine_flags(df_std, [f1, f2, f3])
        to_parquet(
            flags, 
            artifact_path(cfg.client, cfg.fiscal_year, "analytics", "tb_flags.parquet"), 
            FLAGS_SCHEMA_VERSION
        )
        
        # Stage 8: Excel Reporting
        logger.info("stage8_start", extra={"stage": "reporting"})
        out_xlsx = artifact_path(cfg.client, cfg.fiscal_year, "outputs", "planning_pack.xlsx")
        build_excel_pack(
            cfg.client, cfg.fiscal_year, 
            df_std, fs_view, analytics, flags, mat, 
            out_xlsx, logger
        )
        
        # Write run metadata
        finished_at = datetime.utcnow().isoformat()
        run_meta = {
            "run_id": run_id,
            "client": cfg.client,
            "year": cfg.fiscal_year,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": "success",
            "schemas": {
                "tb_raw": TB_RAW_SCHEMA_VERSION,
                "tb_std": TB_STD_SCHEMA_VERSION,
                "fs_view": FS_VIEW_SCHEMA_VERSION,
                "analytics": ANALYTICS_SCHEMA_VERSION,
                "flags": FLAGS_SCHEMA_VERSION
            },
            "config_path": config_path,
            "config_hash": compute_file_hash(config_path),
            "tb_input_hash": compute_file_hash(cfg.tb_input_path)
        }
        write_json(
            artifact_path(cfg.client, cfg.fiscal_year, "meta", "run.json"),
            run_meta
        )
        
        logger.info("run_complete", extra={"run_id": run_id})
        
    except Exception as e:
        logger.exception("run_failed", extra={"run_id": run_id})
        raise typer.Exit(code=1)

@app.command()
def version():
    """Display version information."""
    typer.echo("auditplan v1.0")
    typer.echo("Hybrid RPA Audit Planning Agent")

if __name__ == "__main__":
    app()
```

Effort: S (1-2h)

---

## Cross-cutting: Error handling, logging points, schema versioning, data quality checks

- Error handling patterns:
  - Validate configs on load; raise ValueError with missing keys details.
  - DataQualityError for missing monetary amounts or extreme unmapped cases (configurable).
  - SchemaError for Pandera validation issues; print first N errors.
  - Wrap CLI run in try/except; log exception with traceback; exit code 1.

- Logging points (INFO unless noted):
  - Stage 1: rows loaded, columns mapped, nulls per key (WARN if >10%).
  - Stage 2: validation passed; duplicates count; tie-out delta (WARN if > tolerance).
  - Stage 3: duplicates aggregated; unmapped count and top 5 unmapped examples.
  - Stage 4: FS balance deltas (WARN if > tolerance); counts per statement.
  - Stage 5: materiality numbers; basis and base_value.
  - Stage 6: analytics computed; counts with missing PY; protected division count.
  - Stage 7: flags summary counts.
  - Stage 8: Excel written path; sheet row counts.
  - Run meta: write run.json with timestamps, schema versions, config snapshot hash, input file hash.

- Schema versioning:
  - Embed schema_version in parquet metadata via to_parquet. Include mapping versions if changed in the future.
  - When changing schema, bump versions and add migration notes.

- Data quality checks:
  - Required columns present after mapping.
  - No empty TB (rows == 0).
  - For TB with debit/credit, tie-out near zero.
  - TB_STD closing not null across all rows.
  - Unmapped FS ratio reported.

---

## Data Schemas (Consolidated)

TB Raw (tb_raw.parquet, v1.0)
- fiscal_year:int [required]
- account_id:str [required]
- account_name:str [required]
- class:str [nullable]
- sub_class:str [nullable]
- opening:float [nullable]
- movement:float [nullable]
- closing:float [nullable]
- debit:float [nullable]
- credit:float [nullable]
- source:str = "tb"

TB Standard (tb_std.parquet, v1.0)
- fiscal_year:int [required]
- account_id:str [required]
- account_name:str [required]
- class:str [nullable]
- sub_class:str [nullable]
- opening:float [nullable]
- movement:float [nullable]
- closing:float [required, non-null]
- sign:int in {1,-1} [required]
- source:str="tb"
- fs_statement:str in {"BS","IS","CF","UNMAPPED"}
- fs_section:str
- fs_line:str

FS View (fs_view.parquet, v1.0)
- fiscal_year:int
- fs_statement:str
- fs_section:str
- fs_line:str
- amount:float
- source:str="fs_from_tb"

Analytics (tb_analytics.parquet, v1.0)
- dynamic dims (e.g., account_id, fs_statement, fs_section)
- fiscal_year:int
- value:float (closing)
- yoy_abs:float
- yoy_pct:float
- size_pct:float
- z:float

Flags (tb_flags.parquet, v1.0)
- account_id:str
- fiscal_year:int
- new:bool
- dropped:bool
- sign_flip:bool
- unusual_negative:bool
- flags_count:int
- flags:str

materiality.json
- basis:str
- base_value:float
- planning:float
- performance:float
- trivial:float
- fiscal_year:int

---

## Acceptance Test Matrix (Per Stage)

- Stage 0
  - Pass if utilities import and simple parquet roundtrip works with metadata.

- Stage 1
  - Pass if tb_raw.parquet has >0 rows and required columns.

- Stage 2
  - Pass if Pandera validation succeeds; duplicate and tie-out checks logged.

- Stage 3
  - Pass if tb_std.parquet has non-null closing; fs dimensions present; aggregation reduced duplicates.

- Stage 4
  - Pass if fs_view.parquet exists and BS balance delta <= 1; log computed net income.

- Stage 5
  - Pass if materiality.json created and tb_std_annotated.parquet has materiality_band populated.

- Stage 6
  - Pass if tb_analytics.parquet exists with yoy metrics and no infinite values.

- Stage 7
  - Pass if tb_flags.parquet exists; totals for "new" and "dropped" align with set differences.

- Stage 8
  - Pass if planning_pack.xlsx opens and contains expected sheets with non-zero rows.

- Stage 9
  - Pass if auditplan run completes and all above artifacts are present.

---

## Example Algorithms (Selected)

YoY computation (group and lag)
```python
def compute_yoy(df, group_cols, year_col="fiscal_year", value_col="closing"):
    df = df.copy()
    df.sort_values(group_cols + [year_col], inplace=True)
    df["lag"] = df.groupby(group_cols)[value_col].shift(1)
    df["yoy_abs"] = df[value_col] - df["lag"]
    denom = df["lag"].abs().replace(0, pd.NA)
    df["yoy_pct"] = (df["yoy_abs"] / denom).fillna(0.0)
    return df.drop(columns=["lag"])
```

FS balance check
```python
def check_fs_balance(fs_view, logger):
    bs = fs_view[fs_view.fs_statement == "BS"]
    by_sec = bs.groupby(["fiscal_year", "fs_section"], as_index=False)["amount"].sum()
    pivot = by_sec.pivot(index="fiscal_year", columns="fs_section", values="amount").fillna(0)
    assets = pivot.get("Assets", 0)
    l = pivot.get("Liabilities", 0)
    e = pivot.get("Equity", 0)
    delta = (assets - (l + e)).abs()
    for year, d in delta.items():
        level = "warning" if d > 1.0 else "info"
        getattr(logger, level)(f"BS balance delta for {year}: {d}")
    return {"balance_delta": delta.to_dict()}
```

---

## Risks and Guardrails

- Risk: Ambiguous COA mapping leads to many UNMAPPED accounts.
  - Guardrail: Log top unmapped; export list for manual mapping; treat UNMAPPED in FS but continue.

- Risk: TB source provides only closing balances without class; sign conventions unclear.
  - Guardrail: Do not flip signs; use absolute for analytics; present sign in Excel per section.

- Risk: Division by zero in analytics.
  - Guardrail: Safe divisions; log count of protected operations.

- Risk: Excel file write interruption.
  - Guardrail: Write to temp name then rename; always close workbook in finally.

- Risk: Schema changes break downstream.
  - Guardrail: Versioned schemas; embed schema_version metadata; add simple migration script if needed.

---

## When to consider the advanced path

- If >30% accounts remain UNMAPPED across clients: add fuzzy matching via rapidfuzz and reviewer-assisted crosswalk management.
- If performance drops with large TBs (>100k rows): adopt DuckDB for groupbys and parquet scans.
- If multiple dimensions (entity/segment) appear: extend schema with generic dim_* columns and dynamic config-driven rollups.

Optional advanced path (outline only)
- Add COA management UI (CSV export/import with validation).
- Introduce Great Expectations data docs for richer validation reports.
- Expand Excel with pivot tables and Plotly charts embedded as images.

---

## Implementation Sequence and Rough Effort

- Stage 0: Scaffolding — S (1-3h) **[COMPLETED]**
- Stage 1: TB ingestion — S (1-2h) **[COMPLETED]**
- Stage 2: TB validation — S (1-2h) **[COMPLETED]**
- Stage 3: Standardization + FS tagging — M (2–4h) **[COMPLETED]**
  - **Key improvement**: Auto-generation of COA mappings using Vietnamese COA dictionary (src/auditplan/standardize/vn_coa.py)
  - Class 1 filtering correctly implemented, achieving 100% mapping coverage for parent accounts
  - COA map persisted to configs/coa_map_generated.yaml for review and customization
- Stage 4: FS rollup — S (1-2h) **[COMPLETED]**
  - Balance check implemented with tolerance
  - Both CY and PY processing validated
- Stage 5: Materiality — S (1-2h) **[COMPLETED]**
  - Basis-driven materiality computation (assets, revenue, PTI, equity)
  - Multi-threshold calculation (planning, performance, trivial)
- Stage 6: Analytics engine — M (2–4h) **[COMPLETED]**
  - Dimension-agnostic YoY, common-size, z-score computation
  - Safe division with null/zero handling
- Stage 7: Rules engine — S (1-2h) **[COMPLETED]**
  - New/dropped account detection
  - Sign flip identification (CY vs PY)
  - Unusual negative flagging
  - Composable flag combination with counts
- Stage 8: Excel reporting — M (2–4h) **[NEXT]**
- Stage 9: CLI orchestration — S (1-2h)

**Total estimated effort:** 14–28 hours for a single developer working sequentially.
**Progress:** Stages 0-7 completed (17-23h of estimated 14-28h total)

---

## TL;DR (Summary)

- Build a config-driven TB pipeline: ingest → validate → standardize with FS tags → roll FS view → compute materiality → run dimension-agnostic analytics and rules → export Excel.
- Use Pandera for schemas, parquet for artifacts with schema_version metadata, and Typer for CLI orchestration.
- Keep mapping simple (exact or difflib), safe analytics (division guards), robust logging, and clear acceptance checks per stage.
- The dimension-agnostic design future-proofs the codebase: analytics/rules work on TB accounts today and FS lines tomorrow with zero refactoring.
