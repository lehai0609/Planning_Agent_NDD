# Chart of Accounts → Financial Statements

## 1) Balance Sheet

### Current Assets

| Accounts              | FS Line Item                     | Rule                                               |
| --------------------- | -------------------------------- | -------------------------------------------------- |
| 111, 112              | Cash and Cash Equivalents        | Use closing balance (from Closing Dr/Cr)           |
| 121, 128, 129         | Short-term Financial Investments | Use closing balance                                |
| **131 (Debit only)**  | Trade Receivables                | Take **debit closing** balance                     |
| **331 (Debit only)**  | Advances to Suppliers            | Take **debit closing** balance                     |
| **133 (Debit only)**  | VAT Recoverable                  | Take **debit closing** balance                     |
| 136, 138              | Intercompany/Other Receivables   | Use closing balance                                |
| 141                   | Advances to Employees            | Use closing balance                                |
| 151                   | Goods in Transit                 | Use closing balance                                |
| **152–159**           | Inventories (historical cost)    | Use closing balance                                |
| **2294 (Credit)**     | Allowance for Inventory decline  | Present as **separate negative** line (no netting) |
| 242 (current portion) | Short-term Prepaid Expenses      | Use closing balance                                |
| **333 (Debit only)**  | Taxes Recoverable / Prepaid Tax  | Take **debit closing** balance                     |
| 171                   | Other Current Assets             | Use closing balance                                |

### Non-current Assets

| Accounts                         | FS Line Item                                     | Rule                                                       |
| -------------------------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| 211                              | Tangible Fixed Assets – Historical cost          | Take **debit closing** balance                             |
| 212                              | Finance-leased Fixed Assets – Historical cost    | Take **debit closing** balance                             |
| 213                              | Intangible Fixed Assets – Historical cost        | Take **debit closing** balance                             |
| 217                              | Investment Properties – Historical cost          | Take **debit closing** balance                             |
| **2141/2142/2143/2147 (Credit)** | **Accumulated depreciation/amortization**        | **Separate negative** line, do **not** offset with cost    |
| 241                              | Construction in Progress                         | Use closing balance                                        |
| 228                              | Long-term Financial Investments                  | Use closing balance (often presented **net** with 2292)    |
| 2292 (Credit)                    | Provision for LT Financial Investment impairment | Usually **net** with 228 per TT200; may be a separate line |
| 242 (non-current portion)        | Long-term Prepaid Expenses                       | Use closing balance                                        |
| **347 (Debit only)**             | Deferred Tax Assets                              | Take **debit closing** balance                             |

### Current Liabilities

| Accounts              | FS Line Item                             | Rule                            |
| --------------------- | ---------------------------------------- | ------------------------------- |
| **131 (Credit only)** | Advances from Customers                  | Take **credit closing** balance |
| **331 (Credit only)** | Trade Payables                           | Take **credit closing** balance |
| **333 (Credit only)** | Taxes and Levies Payable                 | Take **credit closing** balance |
| 334                   | Payables to Employees                    | Use closing balance             |
| 335                   | Accrued Expenses                         | Use closing balance             |
| 336, 338              | Intercompany/Other Payables              | Use closing balance             |
| 3387                  | Unearned Revenue (current portion)       | Use closing balance             |
| 341 (current portion) | Short-term Borrowings and Finance Leases | Use closing balance             |
| 352 (current portion) | Short-term Provisions                    | Use closing balance             |

### Non-current Liabilities

| Accounts              | FS Line Item                            | Rule                            |
| --------------------- | --------------------------------------- | ------------------------------- |
| 341 (non-current)     | Long-term Borrowings and Finance Leases | Use closing balance             |
| 343                   | Bonds Payable                           | Use closing balance             |
| **347 (Credit only)** | Deferred Tax Liabilities                | Take **credit closing** balance |
| 3387 (non-current)    | Unearned Revenue (non-current portion)  | Use closing balance             |
| 352 (non-current)     | Long-term Provisions                    | Use closing balance             |

### Equity

| Accounts        | FS Line Item                 | Rule                |
| --------------- | ---------------------------- | ------------------- |
| 411             | Owners’ Capital              | Use closing balance |
| 412             | Share Premium                | Use closing balance |
| 418             | Funds within Owners’ Equity  | Use closing balance |
| 421             | Retained Earnings            | Use closing balance |
| 414, 415        | Other Funds                  | Use closing balance |
| 419             | Foreign Exchange Differences | Use closing balance |
| **423 (Debit)** | Treasury Shares              | **Negative** line   |

---

## 2) Profit & Loss

> Source numbers: **current-year turnovers** that are **already filtered to entries with 911**. Do **not** present 911 as a line item.

| Accounts      | P&L Line Item                             | Rule (current-year turnovers)                            |
| ------------- | ----------------------------------------- | -------------------------------------------------------- |
| 511, 512      | Revenue from Goods and Services           | **Credit** turnover − deductions (521/531/532 **debit**) |
| 521, 531, 532 | Sales Deductions                          | **Debit** turnover                                       |
| 632           | Cost of Goods Sold                        | **Debit** turnover                                       |
| 641           | Selling Expenses                          | **Debit** turnover                                       |
| 642           | General & Administrative Expenses         | **Debit** turnover                                       |
| 515           | Finance Income                            | **Credit** turnover                                      |
| 635           | Finance Costs                             | **Debit** turnover                                       |
| 711           | Other Income                              | **Credit** turnover                                      |
| 811           | Other Expenses                            | **Debit** turnover                                       |
| 821           | Income Tax Expense (current and deferred) | **Debit** turnover                                       |

### Notes and Controls

* **No offsetting** 131/331. Split by **debit** vs **credit** as mapped above.
* **No offsetting** accumulated depreciation (214x) with historical cost (211/212/213/217).
* **No offsetting** inventory with 2294. Show 2294 as a **separate negative** line.
* Accounts class **1–4**: take **closing balances** from **Closing Dr/Cr**.
* Accounts class **5–8**: take **current-year turnovers** that are **counterparted with 911**.
* As a check, 911 must close to 4212 at year-end.
