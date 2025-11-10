Here is the **revised Stage 2 plan**, fully adopting your approach: identify **leaf accounts from the trial balance**, then assign each leaf to a **financial-statement line** by **prefix-matching** the account code to the `1st`-level account in the VAS mapping.
This design keeps the mapping compact, eliminates double counting, and uses the TB itself as the structural truth.

---

# **Stage 2 — Account Classification & Mapping (VAS 200 – TB-Leaf Prefix Method)**

---

## **Objective**

Build Balance Sheet (BS) and Income Statement (PL) datasets by:

1. Identifying leaf accounts directly from the ingested TB.
2. Mapping each leaf to an FS line by prefix-matching its account code to the mapping file’s `1st` column.
3. Aggregating movement-based (P&L) and ending balance (BS) amounts without double counting parents.

---

## **Input Specification**

| Source                            | Description             | Key Fields                                                                      |
| --------------------------------- | ----------------------- | ------------------------------------------------------------------------------- |
| `trial_balance_standardized.xlsx` | Clean TB (from Stage 1) | `account_id`, `account_name`, `dr`, `cr`, `closing_dr`, `closing_cr`, `period`  |
| `Mapping VAS.xlsx (Sheet1)`       | VAS mapping registry    | `1st`, `Leadsheet`, `Item on FSs`, `FSs code` (+ context columns for reference) |

---

## **Workflow Plan**

### **1 · Load and Normalize Data**

```python
tb = pd.read_excel("trial_balance_standardized.xlsx")
map_vas = pd.read_excel("Mapping VAS.xlsx", sheet_name="Sheet1")
```

* Normalize account codes: string, strip spaces, keep digits only.
* Clean mapping: `map_vas['1st'] = map_vas['1st'].astype(str).str.strip()`.

---

### **2 · Identify Leaf Accounts in TB**

Goal: include only accounts with no children sharing their prefix.

Algorithm (approx):

```python
codes = tb['account_id'].astype(str)
tb['is_leaf'] = ~tb['account_id'].apply(lambda x: any(y != x and y.startswith(x) for y in codes))
tb_leaf = tb[tb['is_leaf']]
```

Output: `tb_leaf` = list of terminal accounts used for mapping.

---

### **3 · Prefix-Based Mapping**

For each leaf account in `tb_leaf`:

* Find rows in `map_vas` where `account_id.startswith(map_vas['1st'])`.
* If multiple prefixes match, pick the longest (i.e., most specific).
* Assign FS attributes: `Leadsheet`, `Item on FSs`, `FSs code`.

Pseudologic:

```python
def find_mapping(acc):
    matches = map_vas[map_vas['1st'].apply(lambda p: str(acc).startswith(p))]
    if matches.empty:
        return pd.Series({'Leadsheet': None, 'Item on FSs': None, 'FSs code': None})
    return matches.iloc[matches['1st'].str.len().idxmax()][['Leadsheet','Item on FSs','FSs code']]

tb_leaf = tb_leaf.join(tb_leaf['account_id'].apply(find_mapping))
```

---

### **4 · Compute Amounts**

Add signed amount columns:

| Statement            | Formula                               | Source columns       |
| -------------------- | ------------------------------------- | -------------------- |
| **Balance Sheet**    | `bs_amount = closing_dr – closing_cr` | Ending balances      |
| **Income Statement** | `pl_amount = dr – cr`                 | Movement during year |

*(Positive → debit impact; negative → credit impact.)*

---

### **5 · Aggregation by FS Lines**

Group and sum by mapping targets:

```python
fs_bs = (tb_leaf
         .groupby(['Leadsheet','Item on FSs','FSs code'], as_index=False)['bs_amount'].sum())

fs_pl = (tb_leaf
         .groupby(['Leadsheet','Item on FSs','FSs code'], as_index=False)['pl_amount'].sum())
```

---

### **6 · Validation Checks**

| Check                       | Purpose                                       | Rule                            |
| --------------------------- | --------------------------------------------- | ------------------------------- |
| **Completeness**            | every leaf mapped                             | `FSs code notnull`              |
| **Prefix uniqueness**       | no leaf matches >1 prefix                     | longest-prefix rule ensures     |
| **TB tie-out**              | verify no loss of balance                     | sum of all `bs_amount` ≈ 0      |
| **Retained earnings link**  | check P&L flow to equity                      | sum `pl_amount` ≈ change in 421 |
| **Directional consistency** | Assets ≥ 0, Liab ≤ 0, Income ≤ 0, Expense ≥ 0 | assert per category             |
| **Audit trail**             | document mapping path                         | store `mapped_by_prefix` flag   |

---

### **7 · Output Artifacts**

| File                    | Content                   | Columns                                                       |
| ----------------------- | ------------------------- | ------------------------------------------------------------- |
| `fs_bs_aggregated.xlsx` | Balance Sheet summary     | `Leadsheet`, `Item on FSs`, `FSs code`, `bs_amount`           |
| `fs_pl_aggregated.xlsx` | Income Statement summary  | `Leadsheet`, `Item on FSs`, `FSs code`, `pl_amount`           |
| `mapping_log.xlsx`      | Per-account mapping trace | `account_id`, `matched_prefix`, `FSs code`, `method='prefix'` |

---

### **8 · Notebook Execution Flow**

1. Load and normalize TB + mapping.
2. Detect leaf accounts.
3. Apply prefix-based mapping.
4. Compute `bs_amount` and `pl_amount`.
5. Aggregate to FS lines.
6. Run validation and produce diagnostic tables.
7. Export results and log.

---

### **9 · Advantages of This Plan**

* **No double counting:** only leaf accounts are aggregated.
* **Mapping lightweight:** 1st-level prefix suffices.
* **Auto-adaptive:** new sub-accounts auto-classified under existing prefixes.
* **Transparent:** each leaf record retains its matched prefix for audit review.
* **Compatible with VAS hierarchical chart** (1–4 = BS, 5–8 = PL).

---

### **10 · Optional Enhancements**

* Add `map_method = "prefix"` or `"direct"` for future hybrid extension.
* Implement `prefix_conflicts.xlsx` report when two prefixes overlap (e.g., 131 and 1311 both exist in mapping).
* Support multi-period TB by adding `period` to groupby keys.

---

This plan operationalizes your **TB-leaf → prefix match → FS mapping** logic.
It is lean, reproducible in a single notebook, and audit-traceable through the mapping log.
