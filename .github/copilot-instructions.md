# AI Agent Instructions for Planning_Agent_NDD

## Project Overview

This is a **notebook-driven development (NDD)** intelligent RPA system for audit planning that automates the transformation of trial balances (TB) and general ledgers (GL) into analyzed financial statements with risk detection.

**Core workflow**: Config load → Data ingestion → Validation (pandera) → FS mapping → Analytics → Visualization

## Architecture & Key Patterns

### Notebook-First Development Philosophy
- **Primary workspace**: `notebooks/draft.ipynb` is the main development file, synced to `draft.py` via jupytext
- **Dual format**: All notebooks maintain `.ipynb` and `.py:percent` pairs for version control
- **Execution model**: Cells are meant to be run sequentially; each stage builds on the previous
- **Workflow stages**: Ingestion → Validation → Mapping → Analytics (see cell markdown headers)

### Data Flow Architecture
```
data/TB_*.xlsx, GL_*.xlsx → Stage 1 (Ingestion) → DataFrames
    ↓ (governed by configs/client_year.yaml)
Stage 2 (Validation) → pandera schemas → validated DataFrames
    ↓ (using FS line mapping.md rules)
Stage 3 (Mapping) → Financial Statement structure
    ↓
Stage 4 (Analytics) → artifacts/*.parquet + run_log.json
```

### Configuration-Driven Operations
- **Client configs**: `configs/tomoe_2025.yaml` defines paths, column mappings, and business rules
- **Column mapping**: Config specifies which Excel columns map to canonical fields (e.g., `AccountCode`, `Balance`)
- **Sign conventions**: `credit_negative` means credits are stored as negative numbers
- **Date formats**: Specified in config as `'%d/%m/%Y'` for consistent parsing

### Critical Domain Rules (Vietnamese Accounting)
- **Bidirectional accounts**: Accounts like 131, 331, 333 can have debit OR credit balances
  - 131 Debit = Trade Receivables (asset), 131 Credit = Advances from Customers (liability)
  - 331 Debit = Advances to Suppliers (asset), 331 Credit = Trade Payables (liability)
  - 333 Debit = Taxes Recoverable (asset), 333 Credit = Taxes Payable (liability)
- **Accumulated depreciation**: Accounts 2141/2142/2143/2147 are presented as **separate negative lines**, NOT netted against fixed asset cost
- **Allowances**: Account 2294 (inventory allowance) shown as separate negative line in current assets
- See `FS line mapping.md` for complete chart-of-accounts → financial statement mapping rules

### Data Validation Strategy
- **Schema enforcement**: Use pandera for DataFrame validation (not yet implemented in current code but planned)
- **Path validation**: All file paths validated with `pathlib.Path.exists()` before reading
- **Logging**: Append structured JSON to `artifacts/run_log.json` with schema:
  ```json
  {"timestamp": "ISO8601", "dataset": "name", "source": "path", 
   "rows": int, "columns": int, "status": "pass|fail", "hash": "sha256"}
  ```

## Developer Workflows

### Environment Setup
```bash
# Install dependencies (uses uv for fast resolution)
uv sync                              # Core only
uv sync --extra dev --extra nlp --extra ml  # All features
```

### Running Code
```bash
# Open notebook in VS Code or Jupyter
code notebooks/draft.ipynb

# Format code
ruff format .                        # Fast formatter
black .                              # Alternative

# Lint
ruff check .

# Run tests (when tests/ exists)
pytest
pytest tests/test_<module>.py::test_<function_name>  # Single test
```

### Working with Notebooks
- **jupytext sync**: Automatically maintains `.ipynb` ↔ `.py:percent` sync
- **Cell execution**: Run cells top-to-bottom; later cells depend on earlier state
- **Path resolution**: Notebooks use try/except for `__file__` to work in both .py and .ipynb contexts:
  ```python
  try:
      NOTEBOOK_DIR = Path(__file__).resolve().parent
  except NameError:  # pragma: no cover - jupyter magic
      NOTEBOOK_DIR = Path.cwd()
  ```

## Code Conventions & Patterns

### Style Rules (100-char line limit)
- **Imports**: Standard library → Third-party → Local (grouped, sorted)
- **Types**: Always use type hints: `Dict[str, pd.DataFrame]`, `Optional[Path]`
- **Naming**: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_CASE` (constants)
- **Paths**: Use `pathlib.Path` exclusively; no string concatenation for paths

### DataFrame Operations
```python
# Good: Use Dict type hints for DataFrame collections
def load_dataframes(dataset_map: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    # ... load data
    return frames

# Good: Calculate repo paths relative to notebook location
REPO_ROOT = NOTEBOOK_DIR.parent
DATA_DIR = REPO_ROOT / "data"
```

### Display Patterns in Notebooks
```python
# Standard pattern for data preview
display(Markdown(f"### {dataset_name}"))
display(Markdown(f"- Shape: {df.shape}\n- Columns: {len(df.columns)}"))
display(df.head())  # Sample data
display(df.describe(include="number").T)  # Numeric summary
```

### Error Handling
- **File operations**: Raise `FileNotFoundError` with helpful message including full path
- **Validation failures**: Log to `run_log.json` with `status: "fail"` and error details
- **Data quality**: Use pandera schemas (future); currently manual checks

## Integration Points & Dependencies

### External Data Sources
- **Input formats**: Excel (.xlsx) for TB/GL, PDF for prior-year financial statements
- **Excel reading**: Use `pd.read_excel(path)` without openpyxl import (pandas handles it)
- **PDF parsing**: `pdfplumber` for text extraction (see `IPA in Audit.md` for ML/NLP use cases)

### Output Artifacts
- **Intermediate data**: Save as `.parquet` in `artifacts/` (efficient, typed columnar format)
- **Reports**: Generate Excel via `xlsxwriter`, visualizations via `plotly`
- **Audit trail**: Every ingestion/validation appends to `artifacts/run_log.json`

### Optional ML/NLP Features
- **Anomaly detection**: `pyod.IsolationForest` for GL transaction outliers
- **Text extraction**: `spacy`, `sentence-transformers` for footnote analysis
- **Change detection**: `ruptures` for time-series breakpoint analysis
- Install via: `uv sync --extra nlp --extra ml`

## Project-Specific Gotchas

1. **Sign convention awareness**: Credits may be negative in raw data; check `configs/*.yaml` for `sign_convention`
2. **Account code ambiguity**: Always check debit/credit balance side for accounts 131, 331, 333, 347 before mapping to FS lines
3. **Fiscal year shifts**: Trial balance and GL file naming includes year suffix (e.g., `TB_2025.xlsx`, `GL_30Sept2025.xlsx`)
4. **Config-first changes**: When adding new data sources, update `configs/*.yaml` first, then notebook code
5. **No tests yet**: Test infrastructure is defined (`pytest` in dev deps) but `tests/` directory doesn't exist; manual validation via notebook outputs

## Key Files to Reference

- **`AGENTS.md`**: Command reference, architecture summary, code style rules (THIS FILE)
- **`FS line mapping.md`**: Complete chart-of-accounts → Balance Sheet/P&L mapping rules with sign logic
- **`IPA in Audit.md`**: Conceptual blueprint for ML/NLP features (anomaly detection, NLP of footnotes)
- **`configs/tomoe_2025.yaml`**: Example client configuration structure
- **`notebooks/draft.ipynb`**: Main implementation and working example of all patterns

## When Editing Code

1. **Check config schema**: Does your change require new config keys? Update `configs/tomoe_2025.yaml` as template
2. **Maintain notebook sync**: If editing `.py` file, regenerate `.ipynb` or vice versa (jupytext handles this)
3. **Log changes**: Append to `run_log.json` for any data ingestion or validation operations
4. **Type everything**: Add type hints to all function signatures
5. **Test in notebook**: Run cells sequentially to verify changes work in interactive context
