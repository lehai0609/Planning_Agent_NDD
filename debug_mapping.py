from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path.cwd()
DATA_FOLDER = ROOT / "data"
TB_FILES = ["TB_2024.xlsx", "TB_2025.xlsx"]

ACCOUNT_ID_CANDIDATES = ("account_id", "Account No", "AccountNo", "account no", "Account_no")


def normalize_account_id(value: object, *, digits_only: bool = False) -> str:
    text = str(value).strip().replace(" ", "")
    if digits_only:
        text = "".join(ch for ch in text if ch.isdigit())
    return text


def ensure_account_id(df: pd.DataFrame, *, digits_only: bool = False) -> pd.DataFrame:
    for candidate in ACCOUNT_ID_CANDIDATES:
        if candidate in df.columns:
            df = df.copy()
            if candidate != "account_id":
                df["account_id"] = df[candidate]
            df["account_id"] = df["account_id"].apply(lambda x: normalize_account_id(x, digits_only=digits_only))
            return df
    raise KeyError("No account identifier column found.")


def normalize_prefix(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    if "." in text:
        text = text.split(".", 1)[0]
    text = "".join(ch for ch in text if ch.isdigit())
    return text or None


def main() -> None:
    tb_frames: list[pd.DataFrame] = []
    for year, filename in zip(("2024", "2025"), TB_FILES):
        df = pd.read_excel(DATA_FOLDER / filename)
        df = ensure_account_id(df)
        df["period"] = year
        tb_frames.append(df)

    tb_all = pd.concat(tb_frames, ignore_index=True)

    map_df = pd.read_excel(ROOT / "Mapping VAS.xlsx", sheet_name="Sheet1")
    map_df = map_df[["1st", "Leadsheet", "Item on FSs", "FSs code"]].copy()
    map_df["prefix"] = map_df["1st"].apply(normalize_prefix)
    map_df = map_df.dropna(subset=["prefix"])
    map_df = map_df[map_df["prefix"] != ""]
    map_df["prefix_len"] = map_df["prefix"].str.len()
    map_df = map_df.sort_values("prefix_len", ascending=False).reset_index(drop=True)

    prefixes = map_df["prefix"].tolist()

    sample_accounts = tb_all["account_id"].dropna().astype(str).head(10).tolist()
    print("Sample account IDs:", sample_accounts)

    matches = []
    for acc in sample_accounts:
        match = next((pref for pref in prefixes if acc.startswith(pref)), None)
        matches.append((acc, match))

    print("Prefix matches:", matches)
    print("First 10 prefixes from mapping:", prefixes[:10])

    # Mimic leaf detection and mapping logic
    def compute_leaf_flags(series: pd.Series) -> pd.Series:
        codes = series.astype(str).tolist()
        mask = [
            not any(other != code and other.startswith(code) for other in codes) for code in codes
        ]
        return pd.Series(mask, index=series.index)

    tb_all["is_leaf"] = tb_all.groupby("period")["account_id"].transform(compute_leaf_flags)
    tb_leaves = tb_all[tb_all["is_leaf"]].copy()

    mapping_records = []
    for acc_id in tb_leaves["account_id"]:
        acc_str = str(acc_id)
        match = next((pref for pref in prefixes if acc_str.startswith(pref)), None)
        mapping_records.append(match)

    tb_leaves["matched_prefix"] = mapping_records
    unmapped_count = tb_leaves["matched_prefix"].isna().sum()
    print(f"Leaf rows: {len(tb_leaves)}, unmapped: {unmapped_count}")


if __name__ == "__main__":
    main()

