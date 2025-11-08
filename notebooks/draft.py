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
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable
import hashlib
import json
import shutil

import pandas as pd
import pdfplumber
import yaml

ARTIFACTS_DIR = Path("artifacts")
PARQUET_DIR = ARTIFACTS_DIR / "parquet"
RAW_DIR = ARTIFACTS_DIR / "raw"
MANIFEST_PATH = ARTIFACTS_DIR / "manifests" / "manifest.jsonl"
LOG_PATH = ARTIFACTS_DIR / "run_log.json"

# %%
def load_config(path: Path) -> dict:
    """Load YAML configuration for the active engagement."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# %%
def now_iso() -> str:
    """Return current UTC timestamp in ISO format for logging."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def append_log(event: str, payload: dict) -> None:
    """Append a structured log entry to the run_log.json file."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": now_iso(), "event": event, "payload": payload}
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# %%
def file_digest(path: Path) -> str:
    """Compute SHA256 digest for the provided file."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot_to_artifacts(src: Path, dst_root: Path) -> Path:
    """Copy source file to the artifacts raw directory with a hash appended."""
    dst_root.mkdir(parents=True, exist_ok=True)
    checksum = file_digest(src)
    dst = dst_root / f"{src.stem}_{checksum[:8]}{src.suffix}"
    shutil.copy2(src, dst)
    return dst


def ensure_columns(df: pd.DataFrame, required: Iterable[str], context: str) -> None:
    """Raise a clear error when required columns are missing after mapping."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{context} missing columns: {', '.join(missing)}")


# %%
def _read_tabular_file(path: Path, sheet: str | None = None, header_row: int | None = 0) -> pd.DataFrame:
    """Read Excel or CSV files using pandas and basic heuristics."""
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0, header=header_row)
    if suffix == ".csv":
        return pd.read_csv(path, header=header_row)
    raise ValueError(f"Unsupported file type for ingestion: {path}")


# %%
def ingest_tb(cfg: dict) -> Path:
    """Ingest the trial balance, normalize columns, and persist to parquet."""
    tb_cfg = cfg["inputs"]["tb"]
    tb_path = Path(tb_cfg["path"])
    snapshot = snapshot_to_artifacts(tb_path, RAW_DIR / "tb")
    df = _read_tabular_file(tb_path, sheet=tb_cfg.get("sheet"), header_row=tb_cfg.get("header_row", 0))
    tb_columns = cfg.get("columns", {}).get("tb", {})
    df = df.rename(columns=tb_columns)
    ensure_columns(df, ["account_id", "account_name", "balance"], "trial balance ingestion")
    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)
        if cfg.get("ingestion", {}).get("sign_convention") == "credit_negative":
            df["balance"] = -df["balance"]
    if "account_id" in df.columns:
        df["account_id"] = df["account_id"].astype(str)
    metadata = {
        "client": cfg["client"],
        "fiscal_year": cfg["fiscal_year"],
        "currency": cfg.get("currency"),
        "source_file": tb_path.name,
        "file_hash": file_digest(tb_path),
        "ingested_at": now_iso(),
        "snapshot": str(snapshot),
    }
    for key, value in metadata.items():
        if key not in df.columns and value is not None:
            df[key] = value
    tb_dest = PARQUET_DIR / "tb" / f"{cfg['client']}_{cfg['fiscal_year']}_tb.parquet"
    tb_dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(tb_dest, index=False)
    append_log(
        "ingest.tb.complete",
        {
            "client": cfg["client"],
            "fiscal_year": cfg["fiscal_year"],
            "rows": len(df),
            "columns": df.columns.tolist(),
            "source": str(tb_path),
            "snapshot": str(snapshot),
            "parquet": str(tb_dest),
        },
    )
    return tb_dest


# %%
def ingest_gl(cfg: dict) -> Path:
    """Ingest the general ledger, normalize columns, and persist to parquet."""
    gl_cfg = cfg["inputs"]["gl"]
    gl_path = Path(gl_cfg["path"])
    snapshot = snapshot_to_artifacts(gl_path, RAW_DIR / "gl")
    df = _read_tabular_file(gl_path, sheet=gl_cfg.get("sheet"), header_row=gl_cfg.get("header_row", 0))
    gl_columns = cfg.get("columns", {}).get("gl", {})
    df = df.rename(columns=gl_columns)
    ensure_columns(df, ["date", "account_id"], "general ledger ingestion")
    date_col = "date"
    if date_col in df.columns:
        fmt = cfg.get("ingestion", {}).get("date_format")
        df[date_col] = pd.to_datetime(df[date_col], format=fmt, errors="coerce")
    if "amount" not in df.columns:
        if not {"debit", "credit"}.issubset(df.columns):
            raise ValueError(
                "general ledger ingestion requires 'amount' or both 'debit' and 'credit'"
            )
    if {"debit", "credit"}.issubset(df.columns) and "amount" not in df.columns:
        df["amount"] = df["debit"].fillna(0.0) - df["credit"].fillna(0.0)
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    metadata = {
        "client": cfg["client"],
        "fiscal_year": cfg["fiscal_year"],
        "currency": cfg.get("currency"),
        "source_file": gl_path.name,
        "file_hash": file_digest(gl_path),
        "ingested_at": now_iso(),
        "snapshot": str(snapshot),
    }
    for key, value in metadata.items():
        if key not in df.columns and value is not None:
            df[key] = value
    gl_dest = PARQUET_DIR / "gl" / f"{cfg['client']}_{cfg['fiscal_year']}_gl.parquet"
    gl_dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(gl_dest, index=False)
    append_log(
        "ingest.gl.complete",
        {
            "client": cfg["client"],
            "fiscal_year": cfg["fiscal_year"],
            "rows": len(df),
            "columns": df.columns.tolist(),
            "source": str(gl_path),
            "snapshot": str(snapshot),
            "parquet": str(gl_dest),
        },
    )
    return gl_dest
