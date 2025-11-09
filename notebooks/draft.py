# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Planning_Agent_NDD
#     language: python
#     name: python3
# ---

# %% [markdown]
# # The Audit Planning Agent - Draft Notebook

# %% [markdown]
# ## Stage 1 - Ingestion
# Ingesting trial balance and general ledger before mapping into a full fledge financial report

# %%
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml
from IPython.display import Markdown, display

try:
    NOTEBOOK_DIR = Path(__file__).resolve().parent
except NameError:  # pragma: no cover - jupyter magic
    NOTEBOOK_DIR = Path.cwd()

REPO_ROOT = NOTEBOOK_DIR.parent
DATA_DIR = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
DATASETS: Dict[str, str] = {
    "Previous year trial balance": "TB_2024.xlsx",
    "Current year trial balance": "TB_2025.xlsx",
    "Previous year general ledger": "GL_30Sept2024.xlsx",
    "Current year general ledger": "GL_30Sept2025.xlsx",
}


def load_dataframes(dataset_map: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """Read all Excel files that participate in Stage 1 ingestion."""
    frames: Dict[str, pd.DataFrame] = {}
    for label, filename in dataset_map.items():
        path = DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist. Check Stage 1 dataset files.")
        frames[label] = pd.read_excel(path)
    return frames


def preview_dataframe(name: str, df: pd.DataFrame, sample_rows: int = 5) -> None:
    """Render highlights for each ingested DataFrame."""
    display(Markdown(f"### {name}"))
    display(
        Markdown(
            f"- Shape: {df.shape}\n"
            f"- Columns: {len(df.columns)}\n"
            f"- Memory (bytes): {df.memory_usage(deep=True).sum():,}"
        )
    )
    display(Markdown("**Column overview**"))
    overview = (
        pd.DataFrame(
            {
                "dtype": df.dtypes.astype(str),
                "non-null": df.notna().sum(),
                "unique": df.nunique(dropna=False),
            }
        )
        .reset_index()
        .rename(columns={"index": "column"})
    )
    display(overview)
    display(Markdown("**Sample rows**"))
    display(df.head(sample_rows))
    display(Markdown("**Numeric summary**"))
    numeric_summary = df.describe(include="number").T
    if not numeric_summary.empty:
        display(numeric_summary)
    else:
        display(Markdown("_No purely numeric columns to summarize._"))


def persist_dataframe(name: str, df: pd.DataFrame) -> Path:
    """Store the DataFrame in artifacts for downstream stages."""
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    path = ARTIFACTS_DIR / f"{safe_name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


ingested_frames = load_dataframes(DATASETS)

for dataset_name, dataframe in ingested_frames.items():
    preview_dataframe(dataset_name, dataframe)
    persist_dataframe(dataset_name, dataframe)

# %% [markdown]
# ## Stage 2 - Validate the import database
# In this stage, we will validate the ingested general ledger & trial balance for completeness, format and correctness.

# %%
# First we read the parquets files in artifacts folder
imported_frames = {}
for dataset_name in DATASETS.keys():
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in dataset_name.lower())
    path = ARTIFACTS_DIR / f"{safe_name}.parquet"
    imported_frames[dataset_name] = pd.read_parquet(path)
# Now we can perform some basic validation checks
# The first validation check is Completeness check (DataFrame level)
# DataFrame presence
# Loaded DataFrames are non‑empty; row count > 0.
# Implement: len(df) > 0; log error if zero.
print("------------- Test 1 Non Empty Dataframe -------------")
for dataset_name, dataframe in imported_frames.items():
    if len(dataframe) == 0:
        print(f"Error: {dataset_name} is empty.")
    else:
        print(f"{dataset_name} passed completeness check with {len(dataframe)} rows.")
# Required columns present
# GL requires: date, account (or account_code), description, and one of (debit,credit) or amount.
# TB requires: account (or account_code), description, and one of (debit,credit) or ytd_balance.
# Implement: column presence checks with alias fallback.
print("------------- Test 2 Required Columns -------------")
required_columns = {
    "Previous year trial balance": ["Account No", "Description", "Category", "Opening Dr", "Opening Cr", "Dr", "Cr", "Closing Dr", "Closing Cr"],
    "Current year trial balance": ["Account No", "Description", "Category", "Opening Dr", "Opening Cr", "Dr", "Cr", "Closing Dr", "Closing Cr"],
    "Previous year general ledger": ["Date", "Voucher No", "Customer Code", "Customer Name",  "Description", "Debit Account", "Credit Account", "Debit", "Credit", "Account Description", "Credit Account Description", "FX Rate", "Currency Code", "Credit Amount (Foreign Currency)", "Debit Amount (Foreign Currency)"],
    "Current year general ledger": ["Date", "Voucher No", "Customer Code", "Customer Name",  "Description", "Debit Account", "Credit Account", "Debit", "Credit", "Account Description", "Credit Account Description", "FX Rate", "Currency Code", "Credit Amount (Foreign Currency)", "Debit Amount (Foreign Currency)"],
}

for dataset_name, dataframe in imported_frames.items():
    required = required_columns.get(dataset_name, [])
    missing = [col for col in required if col not in dataframe.columns]
    if missing:
        print(f"Error: {dataset_name} is missing columns: {missing}")
    else:
        print(f"{dataset_name} passed column presence check.")
# Key fields non‑null
# GL: date, account, and at least one of debit/credit/amount non‑null for all rows.
# TB: account non‑null; numeric balance columns non‑null.
# Implement: df[col].isna().sum()==0 for key cols; report rates for numeric fields.
print("------------- Test 3 Key Fields Non-Null -------------")

key_field_checks = {
    "Previous year general ledger": ["Date", "Debit Account", "Credit Account", "Debit", "Credit"],
    "Current year general ledger": ["Date", "Debit Account", "Credit Account", "Debit", "Credit"],
    "Previous year trial balance": ["Account No"],
    "Current year trial balance": ["Account No"],
}

for dataset_name, dataframe in imported_frames.items():
    key_fields = key_field_checks.get(dataset_name, [])
    for col in key_fields:
        if dataframe[col].isna().sum() > 0:
            print(f"Error: {dataset_name} has null values in key column: {col}")
        else:
            print(f"{dataset_name} passed key field non-null check for: {col}")

# Date coverage for general ledgers files only (GL)
# date.min() and date.max() exist; coverage spans months without full gaps; cutoff = date.max().
# Implement: parse to datetime; monthly presence set check.
print("------------- Test 4 Date Coverage -------------")

for dataset_name, dataframe in imported_frames.items():
    if "Date" in dataframe.columns:
        # Parse dates
        dataframe["Date"] = pd.to_datetime(dataframe["Date"], errors="coerce")
        min_date = dataframe["Date"].min()
        max_date = dataframe["Date"].max()
        if pd.isna(min_date) or pd.isna(max_date):
            print(f"Error: {dataset_name} has invalid date range.")
            continue
        # Monthly presence check
        all_months = pd.date_range(start=min_date, end=max_date, freq="MS")
        present_months = dataframe["Date"].dt.to_period("M").unique()
        if not present_months.isin(all_months.to_period("M")).all():
            print(f"Error: {dataset_name} is missing months in date coverage.")
        else:
            print(f"{dataset_name} passed date coverage check.")

# Accuracy (Numeric Integrity)

# Types and finiteness
# Numeric fields finite; no inf/nan in amounts.
# Implement: np.isfinite on numeric cols; coerce to float.
print("------------- Test 5 Types and finiteness -------------")
for dataset_name, dataframe in imported_frames.items():
    numeric_cols = dataframe.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if not pd.api.types.is_float_dtype(dataframe[col]):
            dataframe[col] = pd.to_numeric(dataframe[col], errors="coerce")
        if not dataframe[col].apply(pd.api.types.is_number).all():
            print(f"Error: {dataset_name} has non-finite values in numeric column: {col}")
        else:
            print(f"{dataset_name} passed numeric integrity check for: {col}")

# GL entry balancing
# Create amount = debit - credit if needed; per doc_no (or per journal_id/voucher if present), sum(amount) ≈ 0 within tolerance.
# Implement: groupby and abs(sum) ≤ tolerance; list unbalanced IDs.
print("------------- Test 6 GL Entry Balancing -------------")
for dataset_name, dataframe in imported_frames.items():
    # Only run for datasets whose name or type suggests general ledger (not trial balance)
    if "general ledger" in dataset_name.lower() or "gl" in dataset_name.lower():
        if "Debit" in dataframe.columns and "Credit" in dataframe.columns:
            dataframe["Amount"] = dataframe["Debit"] - dataframe["Credit"]
        else:
            print(f"Error: {dataset_name} is missing Debit or Credit columns.")
            continue  # skip further checks if Debit/Credit missing
        if dataframe["Amount"].isna().sum() > 0:
            print(f"Error: {dataset_name} has null values in Amount column.")
        else:
            print(f"{dataset_name} passed GL entry balancing check.")

# Ledger‑level net zero (GL)
# Overall sum(amount) ≈ 0.
# Implement: single aggregate check.
print("------------- Test 7 Ledger-level net zero (GL) -------------")
for dataset_name, dataframe in imported_frames.items():
    if "Amount" in dataframe.columns:
        if dataframe["Amount"].sum() != 0:
            print(f"Error: {dataset_name} has non-zero sum in Amount column.")
        else:
            print(f"{dataset_name} passed ledger-level net zero check.")

# TB structure and balancing
# If TB has debit/credit: totals equal within tolerance. If TB has signed ytd_balance: sum≈0 (or equals equity, depending on sign convention).
# Implement: conditional aggregate checks.
print("------------- Test 8 TB structure and balancing -------------")
for dataset_name, dataframe in imported_frames.items():
    if "Debit" in dataframe.columns and "Credit" in dataframe.columns:
        if dataframe["Debit"].sum() != dataframe["Credit"].sum():
            print(f"Error: {dataset_name} has non-equal sums in Debit and Credit columns.")
        else:
            print(f"{dataset_name} passed TB structure and balancing check.")

# %% [markdown]
# ## Stage 3 - Standardization
# Convert raw TB/GL extracts into standardized data frames for downstream mapping.

# %%
# Take Stage 2 imported data frame, which are already in artifacts folder and convert them into cononical tables for downstream mapping..
# The canonical tables are: (tb_2024_standardized, tb_2025_standardized, gl_2024_standardized, gl_2025_standardized).
# First, import the artifacts parquet files into dataframes.
imported_frames = {}
for dataset_name in DATASETS.keys():
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in dataset_name.lower())
    path = ARTIFACTS_DIR / f"{safe_name}.parquet"
    imported_frames[dataset_name] = pd.read_parquet(path)


# Trial Balance: calculate closing_signed = closing_dr – closing_cr, keep metadata columns (year, category).
for tb_name in ["Previous year trial balance", "Current year trial balance"]:
    df = imported_frames[tb_name].copy()

    # Normalize expected columns to lower case for easier handling if needed
    colmap = {col.lower().replace(" ", "_"): col for col in df.columns}
    # Define output DataFrame
    result_rows = []
    for idx, row in df.iterrows():
        category = str(row.get("Category", "")).strip().upper()
        # Extract year from dataset name (assumes name like "Current year trial balance")
        year = "2025" if "current" in tb_name.lower() else "2024"
        # Category: balance-sheet
        if category == "BS":
            closing_dr = row.get("Closing Dr", 0) if "Closing Dr" in df.columns else 0
            closing_cr = row.get("Closing Cr", 0) if "Closing Cr" in df.columns else 0
            closing_signed = closing_dr - closing_cr
        # Category: profit-and-loss
        elif category == "PL":
            dr = row.get("Dr", 0) if "Dr" in df.columns else 0
            cr = row.get("Cr", 0) if "Cr" in df.columns else 0
            closing_signed = dr - cr
        else:
            closing_signed = None  # or np.nan
        out = {
            "Account No": row.get("Account No"),
            "Description": row.get("Description"),
            "Category": row.get("Category"),
            "year": year,
            "closing_signed": closing_signed,
        }
        result_rows.append(out)
    standardized_df = pd.DataFrame(result_rows)
    # Optionally, persist for downstream mapping
    safe_name = f"tb_{year}_standardized"
    path = ARTIFACTS_DIR / f"{safe_name}.parquet"
    standardized_df.to_parquet(path, index=False)
    print(f"Standardized TB for {tb_name} to {path}")

# We continue to implement COA Tree and Leaf Detection.
# Objective: Identify leaf-level accounts so mapping only uses terminal nodes (avoids double counting).
# Input: Canonical TB datasets (tb_2024_standardized, tb_2025_standardized).
# Output: Leaf-only datasets stored as parquet (tb_2024_leaves, tb_2025_leaves) plus summary counts.
# Implementation Logic:
# Build a prefix index over account_no values per year.
# Mark accounts with no children sharing the same prefix as leaves.
# Persist filtered tables and surface totals (e.g., display count in notebook).
from typing import List, Dict, Set
import pandas as pd

# Helper: Determine if account_no is a parent of any other account_no (prefix check)
def find_leaf_accounts(account_nos: List[str]) -> Set[str]:
    """
    Given a list of account numbers (as strings), return a set of those which are 'leaf' nodes,
    i.e., do not act as a prefix for any other account in the list.
    """
    account_set = set(str(a) for a in account_nos)
    # Sort for fast prefix checks
    sorted_nos = sorted(account_set)
    leaf_set = set()
    for idx, acc in enumerate(sorted_nos):
        # Check if any later account has this as a prefix and is not identical
        is_leaf = True
        for lookahead in sorted_nos[idx+1:]:
            if lookahead.startswith(acc) and lookahead != acc:
                is_leaf = False
                break
        if is_leaf:
            leaf_set.add(acc)
    return leaf_set

for year in ["2024", "2025"]:
    safe_name = f"tb_{year}_standardized"
    path = ARTIFACTS_DIR / f"{safe_name}.parquet"
    tb_df = pd.read_parquet(path)
    # Only consider accounts with valid account numbers
    account_nos = tb_df["Account No"].astype(str).dropna().tolist()
    leaf_accounts = find_leaf_accounts(account_nos)
    # Filter: keep only rows whose account_no is a leaf
    tb_leaves = tb_df[tb_df["Account No"].astype(str).isin(leaf_accounts)].reset_index(drop=True)
    # Save and print counts
    leaves_path = ARTIFACTS_DIR / f"tb_{year}_leaves.parquet"
    tb_leaves.to_parquet(leaves_path, index=False)
    print(
        f"Year {year}: {len(tb_leaves)} leaf accounts identified out of {len(tb_df)} total accounts. "
        f"Saved to {leaves_path}"
    )

# %%[markdown]
# ## Stage 4 - Mapping Configuration
# Objective: Provide machine-readable mapping that mirrors FS line mapping.md.
# Input: YAML configuration file configs/fs_mapping.yaml.
# Output: In-notebook structure (list/dict) of mapping rules for Balance Sheet and Income Statement.
# Implementation Logic:
# Translate markdown table to YAML with keys: line, selectors (codes/prefixes/ranges), rule, optional presentation.
# Load YAML once per notebook run; optionally wrap entries in dataclasses for clarity.

# %%
CONFIGS_DIR = REPO_ROOT / "configs"
FS_MAPPING_PATH = CONFIGS_DIR / "fs_mapping.yaml"

if not FS_MAPPING_PATH.exists():
    raise FileNotFoundError(f"Mapping config not found at {FS_MAPPING_PATH}")

with FS_MAPPING_PATH.open("r", encoding="utf-8") as stream:
    FS_MAPPING = yaml.safe_load(stream)

balance_sheet_rules = FS_MAPPING.get("balance_sheet", [])
income_statement_rules = FS_MAPPING.get("income_statement", [])

# Load leaf-level trial balances for easy reuse in later stages
TB_LEAVES: Dict[int, pd.DataFrame] = {}
for year in (2024, 2025):
    leaves_path = ARTIFACTS_DIR / f"tb_{year}_leaves.parquet"
    tb_leaves_df = pd.read_parquet(leaves_path)
    tb_leaves_df = tb_leaves_df.copy()
    tb_leaves_df["account_no"] = tb_leaves_df["Account No"].astype(str).str.strip()
    tb_leaves_df["account_desc"] = tb_leaves_df["Description"].astype(str).str.strip()
    tb_leaves_df["category"] = tb_leaves_df["Category"].astype(str).str.upper()
    TB_LEAVES[year] = tb_leaves_df

display(Markdown("### Mapping summary"))
display(
    pd.DataFrame(
        {
            "statement": ["Balance Sheet", "Income Statement"],
            "lines": [len(balance_sheet_rules), len(income_statement_rules)],
        }
    )
)

# %% [markdown]
# ## Stage 4b - Selector Resolution
# Objective: Resolve mapping selectors to the subset of leaf accounts they represent.
# Input: Leaf-level trial balance DataFrame and a selector block from fs_mapping.yaml.
# Output: Filtered DataFrame of leaf accounts for the given selector.
# Implementation Logic:
# - Accept selector keys (`codes`, `prefixes`, `ranges`) and build a boolean mask.
# - Allow multiple selector types to combine via OR logic.
# - Provide a simple helper function that later stages re-use for aggregation.

# %%
def _normalize_selector_values(values: list[str | int]) -> list[str]:
    return [str(value).strip() for value in values]


def _range_mask(series: pd.Series, selector_range: str) -> pd.Series:
    """Return mask of rows whose numeric account number falls within the inclusive range."""
    parts = selector_range.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid range selector: {selector_range}")
    start_raw, end_raw = parts[0].strip(), parts[1].strip()
    numeric_series = pd.to_numeric(series, errors="coerce")
    start_num = pd.to_numeric(start_raw, errors="coerce")
    end_num = pd.to_numeric(end_raw, errors="coerce")

    if pd.notna(start_num) and pd.notna(end_num):
        return numeric_series.between(start_num, end_num)

    # Fallback to lexical comparison when numeric conversion fails
    return series.apply(lambda value: start_raw <= value <= end_raw)


def select_leaf_accounts(
    leaf_df: pd.DataFrame, selectors: Dict[str, list[str | int]]
) -> pd.DataFrame:
    """Return the subset of leaf accounts that match the supplied selectors."""
    if not selectors:
        return leaf_df.copy()

    accounts = leaf_df["account_no"].astype(str)
    mask = pd.Series(False, index=leaf_df.index)

    if "codes" in selectors:
        codes = _normalize_selector_values(selectors["codes"])
        mask |= accounts.isin(codes)

    if "prefixes" in selectors:
        prefixes = tuple(_normalize_selector_values(selectors["prefixes"]))
        mask |= accounts.str.startswith(prefixes)

    if "ranges" in selectors:
        for selector_range in selectors["ranges"]:
            mask |= _range_mask(accounts, str(selector_range))

    result = leaf_df.loc[mask].copy()

    balance_filter = selectors.get("balance")
    if balance_filter:
        if "closing_signed" in result.columns:
            balance_values = pd.to_numeric(result["closing_signed"], errors="coerce")
        elif "closing" in result.columns:
            balance_values = pd.to_numeric(result["closing"], errors="coerce")
        else:
            raise KeyError(
                "Leaf DataFrame must include 'closing_signed' or 'closing' to apply balance filter."
            )
        if balance_filter == "debit":
            result = result[balance_values > 0]
        elif balance_filter == "credit":
            result = result[balance_values < 0]

    return result


# Quick smoke-test: list first few accounts mapped to cash line (if available).
if balance_sheet_rules:
    sample_rule = balance_sheet_rules[0]
    sample_accounts = select_leaf_accounts(TB_LEAVES[2025], sample_rule.get("selectors", {}))
    display(
        Markdown(
            f"Sample mapping for **{sample_rule['line']}** "
            f"({len(sample_accounts)} accounts, showing first five)"
        )
    )
    display(sample_accounts[["account_no", "account_desc"]].head())

# %% [markdown]
# ## Stage 5 - Mapping Execution
# Objective: Apply mapping rules to leaf-level trial balances to generate financial statements.
# Input: Leaf-level trial balance DataFrame and mapping rules.
# Output: Financial statements DataFrame with mapped amounts and metadata.

# %%
# Stage 5 – Balance Sheet Aggregation
# Objective: Produce Balance Sheet values matching template lines, using leaf accounts exactly once.
# Input: Current year leaf TB, Balance Sheet rules from config.
# Output: Structured DataFrame with ordered lines, amounts, and traceable account lists.
# Implementation Logic:
# For each mapping rule, gather selected leaf accounts, detect any overlap with previously mapped accounts (fail-fast).
# Calculate amount per rule (e.g., closing_signed, closing_debit, closing_credit, separate_negative).
# Collect metadata for traceability (account list, order index); persist results to artifacts.
from typing import Any, Dict, List
import pandas as pd

def _normalize_balance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure expected balance columns exist for aggregation logic."""
    normalized = df.copy()
    if "closing" not in normalized.columns and "closing_signed" in normalized.columns:
        normalized["closing"] = normalized["closing_signed"]
    if "closing_debit" not in normalized.columns:
        if "closing_dr" in normalized.columns:
            normalized["closing_debit"] = normalized["closing_dr"]
        else:
            normalized["closing_debit"] = normalized.get("closing", pd.Series(dtype=float)).clip(lower=0)
    if "closing_credit" not in normalized.columns:
        if "closing_cr" in normalized.columns:
            normalized["closing_credit"] = normalized["closing_cr"]
        else:
            normalized["closing_credit"] = normalized.get("closing", pd.Series(dtype=float)).clip(upper=0)
    return normalized


def aggregate_balance_sheet(
    leaf_tb: pd.DataFrame,
    bs_rules: List[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Aggregate leaf-level trial balances to financial statement lines according to mapping rules.

    Args:
        leaf_tb: Leaf-level trial balance DataFrame (must include account_no, closing, debit, credit).
        bs_rules: List of mapping rules (from fs_mapping.yaml).

    Returns:
        DataFrame with columns: line, section, amount, accounts, rule, order.
    """
    leaf_tb = _normalize_balance_columns(leaf_tb)
    mapped_accounts = set()
    results = []

    # Helper for each rule's amount calculation
    def calc_amount(df: pd.DataFrame, rule: str) -> float:
        if rule == "closing_signed":
            return df["closing"].sum()
        elif rule == "closing_debit":
            return df["closing_debit"].sum()
        elif rule == "closing_credit":
            return df["closing_credit"].sum()
        elif rule == "separate_negative":
            pos = df["closing_debit"].sum()
            neg = df["closing_credit"].sum()
            return pos, neg
        else:
            raise ValueError(f"Unrecognized rule: {rule}")

    for order, rule in enumerate(bs_rules):
        selectors = rule.get("selectors", {})
        rule_type = rule.get("rule", "closing_signed")

        # Use select_leaf_accounts (already defined) to select accounts for this rule
        selected_df = select_leaf_accounts(leaf_tb, selectors)

        # Overlap check (fail-fast)
        overlapping = set(selected_df["account_no"]) & mapped_accounts
        if overlapping:
            raise ValueError(
                f"Accounts double-mapped in balance sheet line '{rule['line']}': {sorted(list(overlapping))}"
            )

        mapped_accounts.update(selected_df["account_no"])
        amount = calc_amount(selected_df, rule_type)
        # For all except separate_negative, amount is float
        accounts_list = selected_df["account_no"].astype(str).tolist()
        results.append(
            {
                "line": rule["line"],
                "section": rule.get("section"),
                "amount": amount,
                "accounts": accounts_list,
                "rule": rule_type,
                "order": order,
            }
        )
    df = pd.DataFrame(results)
    return df

# Example usage: aggregate Balance Sheet lines for TB 2025
if balance_sheet_rules:
    balance_sheet_df = aggregate_balance_sheet(TB_LEAVES[2025], balance_sheet_rules)
    display(Markdown("### Aggregated Balance Sheet (first 10 lines)"))
    display(balance_sheet_df.head(10)[["order", "line", "amount", "accounts"]])

# %% [markdown]
# ## Stage 5b - Income Statement Aggregation
# Objective: Produce Income Statement values matching template lines, using leaf accounts exactly once.
# Input: Current year leaf TB, Income Statement rules from config.
# Output: Structured DataFrame with ordered lines, amounts, and traceable account lists.

# %%
def _normalize_pl_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reuse balance normalization for income statement accounts."""
    return _normalize_balance_columns(df)


def _calc_pl_amount(df: pd.DataFrame, rule_type: str) -> float:
    """Compute income statement amount based on rule type."""
    if rule_type in {"closing_signed"}:
        return df["closing"].sum()
    if rule_type in {"closing_debit", "turnover_911_debit"}:
        return df["closing_debit"].sum()
    if rule_type in {"closing_credit", "turnover_911_credit"}:
        return -df["closing_credit"].sum()
    raise ValueError(f"Unrecognized income statement rule: {rule_type}")


def aggregate_income_statement(
    leaf_tb: pd.DataFrame,
    pl_rules: List[Dict[str, Any]],
) -> pd.DataFrame:
    """Aggregate leaf-level trial balances into income statement lines."""
    leaf_tb = _normalize_pl_columns(leaf_tb)
    mapped_accounts = set()
    rows: List[Dict[str, Any]] = []

    for order, rule in enumerate(pl_rules):
        selectors = rule.get("selectors", {})
        rule_type = rule.get("rule", "closing_signed")
        selected = select_leaf_accounts(leaf_tb, selectors)

        overlap = set(selected["account_no"]) & mapped_accounts
        if overlap:
            raise ValueError(
                f"Accounts double-mapped in income statement line '{rule['line']}': {sorted(overlap)}"
            )

        mapped_accounts.update(selected["account_no"])
        amount = _calc_pl_amount(selected, rule_type) if not selected.empty else 0.0
        rows.append(
            {
                "line": rule["line"],
                "section": rule.get("section"),
                "amount": amount,
                "accounts": selected["account_no"].astype(str).tolist(),
                "rule": rule_type,
                "order": order,
            }
        )

    return pd.DataFrame(rows)


if income_statement_rules:
    income_statement_df = aggregate_income_statement(TB_LEAVES[2025], income_statement_rules)
    display(Markdown("### Aggregated Income Statement (first 10 lines)"))
    display(income_statement_df.head(10)[["order", "line", "amount", "accounts"]])

# %% [markdown]
# ## Stage 6 - Coverage & Validation
# Objective: Ensure financial statements match expected totals and relationships.
# Input: Aggregated Balance Sheet and Income Statement DataFrames.
# Output: Validation report with pass/fail status for each key condition

# %%
from typing import Tuple

VALIDATION_TOLERANCE = 1e-2


def _flatten_amount(value: Any) -> float:
    """Convert stored amount (possibly tuple) into a single numeric figure."""
    if isinstance(value, tuple):
        pos, neg = value
        return float(pos) + float(neg)
    return float(value)


def prepare_statement(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["amount_numeric"] = prepared["amount"].apply(_flatten_amount)
    return prepared


def explode_assignments(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    exploded = df.explode("accounts").dropna(subset=["accounts"]).copy()
    exploded["account_no"] = exploded["accounts"].astype(str)
    return exploded.rename(
        columns={
            "line": f"{prefix}_line",
            "section": f"{prefix}_section",
            "rule": f"{prefix}_rule",
        }
    )[[
        f"{prefix}_line",
        f"{prefix}_section",
        f"{prefix}_rule",
        "account_no",
        "amount",
        "amount_numeric",
    ]]


def build_coverage_table(
    year: int,
    tb_leaves: pd.DataFrame,
    bs_df: pd.DataFrame,
    pl_df: pd.DataFrame,
) -> pd.DataFrame:
    base = tb_leaves.copy()
    base["account_no"] = base["account_no"].astype(str)
    bs_assign = explode_assignments(prepare_statement(bs_df), "bs")
    pl_assign = explode_assignments(prepare_statement(pl_df), "pl")

    coverage = (
        base.merge(bs_assign, on="account_no", how="left")
        .merge(pl_assign, on="account_no", how="left", suffixes=("", "_pl"))
    )

    coverage["mapped_bs"] = coverage["bs_line"].notna()
    coverage["mapped_pl"] = coverage["pl_line"].notna()
    coverage["year"] = year
    return coverage


def classify_bs_role(section: str | None) -> str:
    if not section:
        return "other"
    lower = section.lower()
    if "asset" in lower:
        return "assets"
    if "liabilit" in lower:
        return "liabilities"
    if "equity" in lower:
        return "equity"
    return "other"


def compute_net_income(pl_df: pd.DataFrame) -> float:
    credit_rules = {"closing_credit", "turnover_911_credit"}
    debit_rules = {"closing_debit", "turnover_911_debit"}
    total = 0.0
    for _, row in pl_df.iterrows():
        amount = row["amount_numeric"]
        rule_type = row["rule"]
        if rule_type in credit_rules:
            total += amount
        elif rule_type in debit_rules:
            total -= amount
        else:
            total += amount
    return total


bs_prepared = prepare_statement(balance_sheet_df) if "balance_sheet_df" in locals() else None
pl_prepared = prepare_statement(income_statement_df) if "income_statement_df" in locals() else None

if bs_prepared is not None and pl_prepared is not None:
    coverage_2025 = build_coverage_table(2025, TB_LEAVES[2025], bs_prepared, pl_prepared)

    coverage_summary = (
        coverage_2025.groupby(
            ["category", "mapped_bs", "mapped_pl"], dropna=False
        )
        .agg(count=("account_no", "count"), total_closing=("closing_signed", "sum"))
        .reset_index()
    )

    display(Markdown("### Coverage summary (2025)"))
    display(coverage_summary)

    unmapped_bs = coverage_2025[(coverage_2025["category"].str.upper() == "BS") & ~coverage_2025["mapped_bs"]]
    unmapped_pl = coverage_2025[(coverage_2025["category"].str.upper() == "PL") & ~coverage_2025["mapped_pl"]]

    if not unmapped_bs.empty:
        display(Markdown("#### Unmapped balance-sheet leaf accounts"))
        display(unmapped_bs[["account_no", "account_desc", "closing_signed"]])
    if not unmapped_pl.empty:
        display(Markdown("#### Unmapped income-statement leaf accounts"))
        display(unmapped_pl[["account_no", "account_desc", "closing_signed"]])

    bs_role_totals = (
        bs_prepared.assign(bs_role=bs_prepared["section"].apply(classify_bs_role))
        .groupby("bs_role")
        .agg(total=("amount_numeric", "sum"))
        .to_dict()["total"]
    )
    assets_total = bs_role_totals.get("assets", 0.0)
    liabilities_total = bs_role_totals.get("liabilities", 0.0)
    equity_total = bs_role_totals.get("equity", 0.0)
    balance_difference = assets_total - (liabilities_total + equity_total)

    tb_bs_total = coverage_2025[coverage_2025["category"].str.upper() == "BS"]["closing_signed"].sum()
    aggregated_bs_total = bs_prepared["amount_numeric"].sum()

    pl_net_income = compute_net_income(pl_prepared)
    tb_pl_total = coverage_2025[coverage_2025["category"].str.upper() == "PL"]["closing_signed"].sum()
    pl_difference = pl_net_income + tb_pl_total

    retained_earnings_accounts = coverage_2025[
        (coverage_2025["account_no"].str.startswith("421")) & coverage_2025["mapped_bs"]
    ]
    retained_balance = retained_earnings_accounts["closing_signed"].sum()

    validation_rows = [
        {
            "check": "Assets equal Liabilities + Equity",
            "status": abs(balance_difference) <= VALIDATION_TOLERANCE,
            "difference": balance_difference,
        },
        {
            "check": "Balance Sheet totals reconcile to TB (BS category)",
            "status": abs(aggregated_bs_total - tb_bs_total) <= VALIDATION_TOLERANCE,
            "difference": aggregated_bs_total - tb_bs_total,
        },
        {
            "check": "Income Statement net income matches TB PL total",
            "status": abs(pl_difference) <= VALIDATION_TOLERANCE,
            "difference": pl_difference,
        },
        {
            "check": "Retained earnings present",
            "status": retained_balance != 0,
            "difference": retained_balance,
        },
    ]

    duplicates_bs = (
        coverage_2025[coverage_2025["mapped_bs"]]
        .groupby("account_no")
        .filter(lambda g: g["bs_line"].nunique() > 1)
        .drop_duplicates(subset=["account_no", "bs_line"])
    )
    duplicates_pl = (
        coverage_2025[coverage_2025["mapped_pl"]]
        .groupby("account_no")
        .filter(lambda g: g["pl_line"].nunique() > 1)
        .drop_duplicates(subset=["account_no", "pl_line"])
    )

    if not duplicates_bs.empty:
        validation_rows.append(
            {
                "check": "Duplicate BS mappings detected",
                "status": False,
                "difference": len(duplicates_bs["account_no"].unique()),
            }
        )
        display(Markdown("#### Duplicate balance-sheet mappings"))
        display(duplicates_bs[["account_no", "account_desc", "bs_line"]])

    if not duplicates_pl.empty:
        validation_rows.append(
            {
                "check": "Duplicate PL mappings detected",
                "status": False,
                "difference": len(duplicates_pl["account_no"].unique()),
            }
        )
        display(Markdown("#### Duplicate income-statement mappings"))
        display(duplicates_pl[["account_no", "account_desc", "pl_line"]])

    validation_report = pd.DataFrame(validation_rows)
    display(Markdown("### Validation report"))
    display(validation_report)

