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
from IPython.display import Markdown, display

try:
    NOTEBOOK_DIR = Path(__file__).resolve().parent
except NameError:  # pragma: no cover - jupyter magic
    NOTEBOOK_DIR = Path.cwd()

REPO_ROOT = NOTEBOOK_DIR.parent
DATA_DIR = REPO_ROOT / "data"
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


ingested_frames = load_dataframes(DATASETS)

for dataset_name, dataframe in ingested_frames.items():
    preview_dataframe(dataset_name, dataframe)

# %% [markdown]
# ## Stage 2 - Validate
