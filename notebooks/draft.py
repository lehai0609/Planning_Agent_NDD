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

