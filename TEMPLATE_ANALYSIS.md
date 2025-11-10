# Template Analysis Summary

## Overview
This document summarizes the analysis of the Balance Sheet and Income Statement templates, focusing on their structure and how they align with the mapping configuration.

## Template Structure

### Balance Sheet Template (`BS_Template.xlsx`)
- **Total rows**: 153
- **Column B (Index 1)**: Contains line item labels/descriptions
- **Column C (Index 2)**: Contains FS codes (Financial Statement line codes)
- **Total unique FS codes**: 117

**Key FS Code Ranges:**
- **100-199**: Short-term assets (100 = parent, 110-155 = children)
- **200-269**: Long-term assets (200 = parent, 210-269 = children)
- **270**: Total Assets (calculated: 100 + 200)
- **300-343**: Liabilities (300 = parent, 310-343 = children)
- **400-432**: Owners' Equity (400 = parent, 410-432 = children)
- **440**: Total Resources (calculated: 300 + 400)

**Special codes with suffixes:**
- `411a`, `411b`: Sub-categories of contributed capital
- `421a`, `421b`: Previous year's and current year's retained profits

### Income Statement Template (`Income_Statement_Template.xlsx`)
- **Total rows**: 51
- **Column B (Index 1)**: Contains line item labels/descriptions
- **Column C (Index 2)**: Contains FS codes
- **Total unique FS codes**: 22

**Key FS Codes:**
- **01**: Revenue
- **02**: Deductions
- **10**: Net revenue (calculated: 01 - 02)
- **11**: Cost of sales
- **20**: Gross profit (calculated: 10 - 11)
- **21**: Financial incomes
- **22**: Financial expenses
- **23**: Interest expenses (sub-item of 22)
- **25**: Selling expenses
- **26**: General & administrative expenses
- **30**: Net operating (loss)/profit (calculated: 20 + 21 - 22 - 25 - 26)
- **31**: Other incomes
- **32**: Other expenses
- **40**: Other loss
- **50**: Net (loss)/profit before tax (calculated: 30 + 31 - 32 - 40)
- **51**: Current CIT expenses
- **52**: Deferred CIT (incomes)/expenses
- **60**: Net (loss)/profit after tax (calculated: 50 - 51 - 52)
- **61**: Net profit/(loss) of shareholders of parent company
- **62**: Net profit/(loss) of non-controlling interests
- **70**: Basic earnings per share
- **71**: Diluted earnings per share

## Mapping Configuration Alignment

### Statistics
- **FS codes in mapping config**: 99 unique codes
- **FS codes in templates**: 139 unique codes (117 BS + 22 IS)
- **Common codes (in both)**: 99 codes (100% of mapping codes exist in templates)
- **Codes only in templates**: 40 codes

### Analysis
1. **Perfect Alignment**: All 99 FS codes from the mapping configuration exist in the templates. This means every mapped account can be placed into a template line.

2. **Missing in Mapping**: The 40 template codes not in the mapping are:
   - **Parent/aggregate codes**: 100, 110, 120, 130, 140, 150, 200, 210, 220, 230, 240, 250, 260, 300, 310, 330, 400, 410, 430
   - **Calculated lines**: 10, 20, 30, 40, 50, 60 (Income Statement calculated lines)
   - **Total lines**: 270, 440 (Balance Sheet totals)

3. **Implication**: 
   - The mapping config maps to **leaf-level** account lines only
   - Parent codes and calculated lines need to be **computed/aggregated** from child lines
   - The templates provide the **hierarchical structure** for organizing the mapped data

## Template Usage Strategy

### For Populating Financial Statements

1. **Load Template Structure**: Read the template Excel files to get the row structure and FS codes
2. **Match Mapped Data**: Use `fs_code` from `mapped_df` (generated in `draft.py`) to match against template FS codes
3. **Populate Leaf Lines**: Fill in amounts for lines that have direct mappings (the 99 codes)
4. **Calculate Parent Lines**: Sum child lines to populate parent codes (e.g., 100 = sum of 110, 120, 130, 140, 150)
5. **Calculate Derived Lines**: Compute calculated lines using formulas (e.g., 10 = 01 - 02, 20 = 10 - 11)
6. **Preserve Template Format**: Maintain the template's row structure, formatting, and layout

### Column Structure (Row 2 contains headers)
- **Column A (Index 0)**: Empty/for formatting
- **Column B (Index 1)**: "Items" - Line item labels - **preserve as-is**
- **Column C (Index 2)**: "Code" - FS codes - **preserve as-is**
- **Column D (Index 3)**: "Current year\nUnaudited" - **PRIMARY TARGET** for populating mapped amounts
- **Column E (Index 4)**: "Total ADJ" - Adjustments column
- **Column F (Index 5)**: "Current year\nAudited" - Audited amounts
- **Column G (Index 6)**: "Previous year\nper Audited FSs" - Prior year amounts
- **Column H (Index 7)**: "Restated\nof errors" - Restatements
- **Columns I+ (Index 8+)**: Additional columns (17 total columns in templates)

## Next Steps

To implement FS population:

1. **Load Template Structure**: Read template Excel files, preserving row structure
2. **Match Mapped Data**: Use `fs_code` from `mapped_df` (generated in `draft.py`) to match against template FS codes in Column C
3. **Populate Leaf Lines**: Fill Column D ("Current year\nUnaudited") with amounts from `mapped_df` where `fs_code` matches
4. **Calculate Parent Lines**: Sum child lines to populate parent codes (e.g., 100 = sum of 110, 120, 130, 140, 150)
5. **Calculate Derived Lines**: Compute calculated lines using formulas:
   - Income Statement: 10 = 01 - 02, 20 = 10 - 11, 30 = 20 + 21 - 22 - 25 - 26, etc.
   - Balance Sheet: 270 = 100 + 200, 440 = 300 + 400
6. **Preserve Template Format**: Maintain the template's row structure, formatting, and layout
7. **Write Output**: Save populated template to Excel file

## Example Template Row Structure

**Balance Sheet:**
```
Row | Column B (Label)                          | Column C (FS Code)
----|-------------------------------------------|------------------
7   | A - SHORT-TERM ASSETS                     | 100
9   | I. Cash and cash equivalents              | 110
10  | ▪ Cash                                    | 111
11  | ▪ Cash equivalents                        | 112
```

**Income Statement:**
```
Row | Column B (Label)                          | Column C (FS Code)
----|-------------------------------------------|------------------
5   | ▪ Revenue                                 | 01
7   | ▪ Deductions                              | 02
9   | ▪ Net revenue                             | 10
```

