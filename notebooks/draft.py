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
# Ingesting trial balance before mapping into a full fledge financial report

# %%
import pandas as pd
import numpy as np
from IPython.display import display
from pathlib import Path

# Define data folder and input files
data_folder = Path.cwd().parent / "data"
tb_2024_path = data_folder / "TB_2024.xlsx"
tb_2025_path = data_folder / "TB_2025.xlsx"

# Ingest prior-year and current-year trial balance
tb_2024 = pd.read_excel(tb_2024_path)
tb_2025 = pd.read_excel(tb_2025_path)

# Display the first few rows of the trial balance
print("2024 Trial Balance:")
display(tb_2024.head())
# %% [markdown]
# ## Stage 2 - Mapping to Leadsheet
# ### Normalize input and Detect leaf accounts

# %%
# Load the VAS mapping file
vas_mapping_path = Path.cwd().parent / "Mapping VAS.xlsx"
vas_mapping = pd.read_excel(vas_mapping_path, sheet_name="Sheet1")
display(vas_mapping.head())

# Normalizes trial balance data by reusing tb_2024/tb_2025 from Stage 1 with added period labels,
# standardizes account_id fields through trimming / optional digit stripping, and loads the VAS mapping
# file while trimming the prefix column and retaining only necessary mapping columns for subsequent processing.
# --- Normalize and concatenate TBs with period labels ---
ACCOUNT_ID_CANDIDATES = ("account_id", "Account No", "AccountNo", "account no", "Account_no")

def normalize_account_id(x: str, digits_only: bool = False) -> str:
    """
    Normalize account_id as character/text. 
    - Trims whitespace.
    - Optionally removes non-digits if digits_only=True.
    Always returns string.
    """
    s = str(x).strip().replace(" ", "")
    if digits_only:
        s = "".join(c for c in s if c.isdigit())
    return s


def ensure_account_id(df: pd.DataFrame, *, digits_only: bool = False) -> pd.DataFrame:
    """Ensure the dataframe exposes an 'account_id' column using common fallback names."""
    for candidate in ACCOUNT_ID_CANDIDATES:
        if candidate in df.columns:
            df = df.copy()
            if candidate != "account_id":
                df["account_id"] = df[candidate]
            df["account_id"] = df["account_id"].apply(lambda x: normalize_account_id(x, digits_only=digits_only))
            return df
    raise KeyError("No account identifier column found in trial balance dataframe.")


tb_2024_norm = ensure_account_id(tb_2024)
tb_2025_norm = ensure_account_id(tb_2025)

for df, period in ((tb_2024_norm, "2024"), (tb_2025_norm, "2025")):
    df["period"] = period

tb_all = pd.concat([tb_2024_norm, tb_2025_norm], ignore_index=True)
# tb_all now has standardized account_id values and a "period" label


def normalize_prefix(value: str) -> str | None:
    """Normalize mapping prefixes (handle floats like 112.0 -> '112', strip whitespace)."""
    if pd.isna(value):
        return None
    s = str(value).strip()
    if s == "":
        return None
    # remove decimal part for numeric-looking prefixes and strip non-digit separators
    if "." in s:
        s = s.split(".", 1)[0]
    s = "".join(c for c in s if c.isdigit())
    return s or None


mapping_columns = ['1st', 'Leadsheet', 'Item on FSs', 'FSs code']
vas_mapping = vas_mapping[mapping_columns].copy()
vas_mapping = vas_mapping.rename(columns={'1st': 'prefix'})
vas_mapping['prefix'] = vas_mapping['prefix'].apply(normalize_prefix)
vas_mapping = vas_mapping.dropna(subset=['prefix'])
vas_mapping = vas_mapping[vas_mapping['prefix'] != ""]

# Detect leaf account per period (terminal nodes in account hierarchy).
def compute_leaf_flags(series: pd.Series) -> pd.Series:
    codes = series.astype(str).tolist()
    leaf_mask = []
    for code in codes:
        leaf_mask.append(not any(other != code and other.startswith(code) for other in codes))
    return pd.Series(leaf_mask, index=series.index)

# Apply per period using transform to preserve original order without groupby apply warnings.
tb_all['is_leaf'] = tb_all.groupby('period')['account_id'].transform(compute_leaf_flags)
# tb_all now has is_leaf boolean column per period

# %% [markdown]
# Map leaves to leadsheet

# %%
# -- Prefix-based leaf account mapping, longest-prefix-first, vectorized --

# Work only on leaf accounts
tb_leaves = tb_all[tb_all['is_leaf']].copy()

# Sort vas_mapping by descending prefix length (most specific first)
vas_mapping['prefix_len'] = vas_mapping['prefix'].str.len()
vas_mapping_sorted = vas_mapping.sort_values('prefix_len', ascending=False).reset_index(drop=True)
prefix_tuples = list(zip(vas_mapping_sorted['prefix'], 
                         vas_mapping_sorted['Leadsheet'], 
                         vas_mapping_sorted['Item on FSs'], 
                         vas_mapping_sorted['FSs code']))

def longest_prefix_lookup(acc_id: str):
    acc_id_str = str(acc_id)
    for prefix, leadsheet, item_on_fs, fs_code in prefix_tuples:
        if acc_id_str.startswith(prefix):
            return {
                "matched_prefix": prefix,
                "Leadsheet": leadsheet,
                "Item on FSs": item_on_fs,
                "FSs code": fs_code,
                "map_method": "prefix",
            }
    # No prefix found
    return {
        "matched_prefix": None,
        "Leadsheet": None,
        "Item on FSs": None,
        "FSs code": None,
        "map_method": None,
    }

# Apply mapping to each leaf account (vectorized via DataFrame.apply)
leaf_map_df = tb_leaves['account_id'].apply(longest_prefix_lookup).apply(pd.Series)
tb_leaves = tb_leaves.join(leaf_map_df)

# Collect unmapped leaf accounts for review
unmapped_leaves = tb_leaves[tb_leaves['matched_prefix'].isnull()].copy()

display(unmapped_leaves)
display(tb_leaves.head())

# %% [markdown]
# ## Stage 3 - Financial Statement Aggregation

# %%
from collections import OrderedDict

# --- Stage 3 · Prepare measures on mapped leaf data ---
tb_leaves_measured = tb_leaves.copy()
amount_source_columns = OrderedDict(
    [
        ("dr", "Dr"),
        ("cr", "Cr"),
        ("opening_dr", "Opening Dr"),
        ("opening_cr", "Opening Cr"),
        ("closing_dr", "Closing Dr"),
        ("closing_cr", "Closing Cr"),
    ]
)

for alias, source_col in amount_source_columns.items():
    if source_col in tb_leaves_measured.columns:
        tb_leaves_measured[source_col] = tb_leaves_measured[source_col].fillna(0.0)
        tb_leaves_measured[alias] = tb_leaves_measured[source_col]
    else:
        tb_leaves_measured[alias] = 0.0

tb_leaves_measured["bs_amount"] = tb_leaves_measured["closing_dr"] - tb_leaves_measured["closing_cr"]
tb_leaves_measured["pl_amount"] = tb_leaves_measured["dr"] - tb_leaves_measured["cr"]
tb_leaves_measured["opening_amount"] = (
    tb_leaves_measured["opening_dr"] - tb_leaves_measured["opening_cr"]
)

# Filter to mapped rows only (retain unmatched separately for diagnostics).
mapped_leaves = tb_leaves_measured[tb_leaves_measured["FSs code"].notna()].copy()
mapped_leaves["FSs code"] = mapped_leaves["FSs code"].astype(str).str.strip()
mapped_leaves = mapped_leaves[mapped_leaves["FSs code"] != ""]

# --- Stage 3 · Aggregate by financial statement code ---
group_keys = ["period", "FSs code", "Leadsheet", "Item on FSs"]
fs_bs = (
    mapped_leaves.groupby(group_keys, dropna=False, as_index=False)["bs_amount"].sum()
)
fs_pl = (
    mapped_leaves.groupby(group_keys, dropna=False, as_index=False)["pl_amount"].sum()
)

# Helper to pivot statement data wide by period (rows keyed by FS code).
def pivot_statement(df: pd.DataFrame, value_col: str, value_label: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["FSs code", value_label])

    value = (
        df.pivot_table(
            index=["FSs code", "Leadsheet", "Item on FSs"],
            columns="period",
            values=value_col,
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .sort_values("FSs code")
    )
    value.columns = [
        "FSs code",
        "Leadsheet",
        "Item on FSs",
        *[f"{value_label}_{col}" for col in value.columns[3:]],
    ]
    return value

bs_pivot = pivot_statement(fs_bs, "bs_amount", "bs_amount")
pl_pivot = pivot_statement(fs_pl, "pl_amount", "pl_amount")

# --- Stage 3 · Optional template alignment ---
artifacts_dir = Path.cwd().parent / "artifacts"
artifacts_dir.mkdir(parents=True, exist_ok=True)

balance_sheet_output_path = artifacts_dir / "fs_balance_sheet_pivot.xlsx"
income_statement_output_path = artifacts_dir / "fs_income_statement_pivot.xlsx"

with pd.ExcelWriter(balance_sheet_output_path, engine="xlsxwriter") as writer:
    bs_pivot.to_excel(writer, sheet_name="BalanceSheet", index=False)

with pd.ExcelWriter(income_statement_output_path, engine="xlsxwriter") as writer:
    pl_pivot.to_excel(writer, sheet_name="IncomeStatement", index=False)

print(f"Balance sheet pivot exported to {balance_sheet_output_path}")
print(f"Income statement pivot exported to {income_statement_output_path}")

