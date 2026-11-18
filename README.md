# 💰 Personal Expense Tracker

A full-featured, responsive **Personal Expense Tracker** built with **Python**, **Streamlit**, **SQLite**, **Pandas**, and **Plotly**. Designed for managing daily income, tracking expenses, setting category budgets with automated threshold warnings (80% and 100%), generating monthly financial analytics, and exporting reports in CSV and PDF formats.

---

## 🌟 Key Features

### 1. 📊 Interactive Financial Dashboard
- Real-time KPI metric cards: **Total Income**, **Total Expenses**, **Current Balance**, and **Savings Rate (%)** formatted in your selected country's currency.
- **Interactive Plotly Visualizations**:
  - Monthly Income vs. Expenses comparison with net savings trend line.
  - Category-wise expense breakdown with interactive donut charts.
  - Income distribution by source.
- Dynamic budget alerts banner displayed directly at the top of the dashboard.
- Live preview of recent financial transactions.

### 2. 🌍 Universal Multi-Currency Support (ہر ملک کی کرنسی)
- Choose from 35+ major world currencies or enter any custom currency code and symbol:
  - 🇵🇰 Pakistani Rupee (`PKR` - `₨`)
  - 🇮🇳 Indian Rupee (`INR` - `₹`)
  - 🇺🇸 US Dollar (`USD` - `$`)
  - 🇪🇺 Euro (`EUR` - `€`)
  - 🇬🇧 British Pound (`GBP` - `£`)
  - 🇦🇪 UAE Dirham (`AED` - `AED`)
  - 🇸🇦 Saudi Riyal (`SAR` - `SAR`)
  - 🇨🇦 Canadian Dollar (`CAD` - `CA$`)
  - 🇹🇷 Turkish Lira (`TRY` - `₺`), etc.
- Custom symbol positioning: Prefix (e.g. `₨ 5,000.00`) or Suffix (e.g. `5,000.00 kr`).
- All dashboards, charts, input forms, alerts, and PDF/CSV reports dynamically update in the chosen currency.

### 3. 🧹 Clean Zero-Start & Database Reset (0 سے شروع)
- Starts fresh with 0 balance, ready for real daily personal finances.
- Built-in **Reset All Data to Zero** feature in Settings to wipe all records and start fresh anytime with full safety confirmation.
- Optional demo data seeder available for testing or portfolio demonstration.

### 2. ➕ Income Management
- Record earnings with:
  - Amount (strictly validated positive values).
  - Income source (Salary, Freelance, Investments, Gifts, or Custom source).
  - Date and deposit method (Direct Deposit, Bank Transfer, PayPal, Cash, etc.).
  - Detailed descriptions and notes.
- Instant feedback and preview table of recent income logs.

### 3. ➖ Expense Tracking
- Log expenses with:
  - Amount, expense category, payment method (Credit Card, Debit Card, Cash, etc.), date, and merchant/notes.
  - Supports custom expense categories.
- **Pre-Submit Budget Warning**: Real-time notifications alert you if logging the expense will push your category or overall budget past 80% or 100%.

### 4. 📋 Transaction History & Management
- Search records dynamically by keywords (merchant, description, category, payment method).
- Multi-criteria filtering:
  - Transaction Type (All, Income, Expense).
  - Category and Payment Method.
  - Custom Date Range.
- **Edit Records**: In-place edit form with field pre-population and validation.
- **Safe Deletion**: Deletion confirmation prompt with record details to prevent accidental data loss.

### 5. 🎯 Budget Management & Threshold Alerts
- Set monthly limits overall or for specific expense categories (e.g. Groceries, Rent, Dining).
- Visual progress meters comparing budget limits against actual spending.
- Real-time remaining balance calculations.
- **Smart Color-Coded Alert Badges**:
  - 🟢 **Safe / On Track**: Spent < 80% of budget.
  - 🟡 **Warning Alert**: Spent &ge; 80% and < 100% of budget.
  - 🔴 **Critical Exceeded Alert**: Spent &ge; 100% of budget.
- Ability to update or delete existing budgets.

### 6. 📝 Smart Khata & Daily Hisaab Notes (روزانہ کھاتہ اور اسمارٹ نوٹس)
- **Natural Language Math Parser**: Apni rozmarrah hisaab kitab jaise natural text mein likhein:
  - `200 Chicken + 500 Cash = 700`
  - `200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii`
  - Ya multi-line grocery/bill lists (+ aur - ke sath).
- **Live Real-Time Math**: Total Added (+), Total Deducted (-), aur Net Balance exact mathematical accuracy ke sath live breakdown mein calculate hota hai.
- **Permanent SQLite Storage**: Ek click par notes save karein — yeh SQLite database mein permanently save rehte hain aur kabhi delete ya lose nahi hotay.
- **Monthly Diary & Archive**: Maheena-waar (Monthly) filter, keyword search, aur itemized view.
- **1-Click Transaction Sync**: Ek click par khata notes ke tamam items ko real income/expense transactions mein tabdeel karein.

### 7. 🎯 Financial Goals Tracker (بچت کے اہداف)
- Define personal savings targets (Emergency Fund, Vehicle, Vacation, Wedding, Hajj/Umrah, Gadgets, etc.).
- Real-time gauge progress meter for every goal showing target, saved, remaining, and deadline countdown.
- 1-click **Add Savings** contribution modal with automatic completion celebration (🏆 Achieved!).
- Option to reset or delete goals.

### 7. 🔁 Recurring Transactions (ماہانہ خودکار اندراج)
- Set up automatic recurring templates for salary, house rent, utilities, Netflix, subscriptions, and loan EMIs.
- Flexible frequencies: **Daily**, **Weekly**, or **Monthly**.
- **Auto-execution on app launch**: Whenever you open the tracker, due recurring entries are recorded automatically and tagged `[Auto]`.
- Pause or resume recurring templates anytime.

### 8. 🌓 Dark & Light Theme Modes
- Toggle between crisp **Light Mode** and modern **Dark Slate Mode** from the sidebar or Settings page.
- Persistent theme preference saved in database.

### 9. 📈 Monthly Financial Reports & Analysis
- Monthly summaries:
  - Total Income, Total Expenses, Net Savings, and Savings Rate.
  - Peak spending day and peak spending amount.
  - Top expense category and share percentage.
  - Daily average spending calculation.
- **Month-over-Month Comparison**:
  - Automatic delta calculation against the prior month (Dollar change and % change).
  - Itemized category-by-category shift table.
- **Spending Analysis**:
  - Category breakdown bar chart with exact figures.
  - Payment method distribution chart.
  - Daily spending activity area curve.

### 7. 💾 Export Data (CSV & PDF)
- **CSV Export**: Download full transaction logs or filter by specific period and type for Excel / Google Sheets.
- **PDF Export**: Generate and download beautifully structured, multi-section financial reports with ReportLab (includes executive summaries, category tables, budget compliance, and transaction logs).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Frontend UI** | Streamlit |
| **Database** | SQLite3 (Persistent local storage with foreign keys & indexes) |
| **Data Processing** | Pandas |
| **Data Visualization** | Plotly Express & Plotly Graph Objects |
| **Document Generation** | ReportLab |
| **Testing** | Pytest / Unittest |

---

## 📂 Project Architecture

```text
personal-expense-tracker/
│
├── database/
│   ├── __init__.py
│   ├── db.py                  # SQLite connection manager, schema & indexes
│   └── queries.py             # Default category presets and SQL definitions
│
├── services/
│   ├── __init__.py
│   ├── transaction_service.py # Transaction CRUD, filtering & aggregation logic
│   ├── budget_service.py      # Budget limits, remaining math & 80%/100% threshold checks
│   ├── report_service.py      # Monthly summaries, comparisons & spending trends
│   ├── export_service.py      # CSV converter & ReportLab PDF report builder
│   ├── settings_service.py    # Multi-currency registry, theme & zero-reset
│   ├── goals_service.py       # Financial savings targets & contributions
│   └── recurring_service.py   # Automated recurring income/expense scheduler
│
├── utils/
│   ├── __init__.py
│   ├── validators.py          # Input validation (amounts, dates, strings)
│   └── formatters.py          # Currency & percentage formatters
│
├── views/
│   ├── __init__.py
│   ├── dashboard.py           # Dashboard view with KPI cards & Plotly charts
│   ├── add_income.py          # Income recording form
│   ├── add_expense.py         # Expense recording form with pre-check alerts
│   ├── transactions.py        # Search, filter, edit & delete view
│   ├── budgets.py             # Budget setup, progress bars & alert badges
│   ├── goals.py               # Savings goals tracker & gauge meters
│   ├── recurring.py           # Recurring entries scheduler & auto-execution
│   ├── reports.py             # Monthly analytics & month-over-month comparison
│   ├── export.py              # CSV & PDF download center
│   └── settings_view.py       # Currency, theme & database management
│
├── tests/
│   ├── __init__.py
│   ├── test_database.py       # Schema & constraint tests
│   ├── test_transactions.py   # CRUD & filter tests
│   ├── test_budgets.py        # Budget alert threshold unit tests
│   ├── test_reports.py        # Financial report math & PDF generation tests
│   ├── test_settings.py       # Currency & preference unit tests
│   ├── test_goals.py          # Savings goals math & milestone tests
│   └── test_recurring.py      # Recurring auto-execution tests
│
├── app.py                     # Main application entry point & routing
├── seed_sample_data.py        # Optional demo dataset seeder
├── requirements.txt           # Project dependencies
└── README.md                  # Comprehensive documentation
```

---

## 🚀 Installation & Running

### 1. Clone or Download the Repository
```bash
git clone https://github.com/your-username/personal-expense-tracker.git
cd personal-expense-tracker
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Populate Sample Demo Data
To explore the application with sample transactions and budgets:
```bash
python seed_sample_data.py
```

### 5. Run the Application
```bash
streamlit run app.py
```

Once started, open your browser to **`http://localhost:8501`**.

---

## 🧪 Running Unit Tests

The test suite thoroughly validates database integrity, transactions, budgets, savings goals, recurring auto-execution, and PDF generation:

```bash
pytest -v
```

All 27 unit tests pass cleanly:
```text
tests/test_budgets.py::TestBudgetService::test_budget_alert_thresholds PASSED
tests/test_budgets.py::TestBudgetService::test_budget_pre_check_alert PASSED
tests/test_budgets.py::TestBudgetService::test_set_and_update_budget PASSED
tests/test_database.py::TestDatabase::test_tables_created PASSED
tests/test_database.py::TestDatabase::test_transaction_check_constraints PASSED
tests/test_goals.py::TestGoalsService::test_add_and_get_goal PASSED
tests/test_goals.py::TestGoalsService::test_add_to_goal_savings PASSED
tests/test_goals.py::TestGoalsService::test_delete_goal PASSED
tests/test_goals.py::TestGoalsService::test_invalid_goal_inputs PASSED
tests/test_goals.py::TestGoalsService::test_update_goal_savings_and_reset PASSED
tests/test_recurring.py::TestRecurringService::test_add_and_get_recurring PASSED
tests/test_recurring.py::TestRecurringService::test_process_due_recurring PASSED
tests/test_recurring.py::TestRecurringService::test_toggle_active_and_delete PASSED
tests/test_reports.py::TestReportService::test_csv_export PASSED
tests/test_reports.py::TestReportService::test_monthly_comparison PASSED
tests/test_reports.py::TestReportService::test_monthly_summary PASSED
tests/test_reports.py::TestReportService::test_pdf_report_generation PASSED
tests/test_reports.py::TestReportService::test_previous_month_calculation PASSED
tests/test_settings.py::TestSettingsService::test_currencies_list PASSED
tests/test_settings.py::TestSettingsService::test_format_currency_with_symbols PASSED
tests/test_settings.py::TestSettingsService::test_reset_data_to_zero PASSED
tests/test_settings.py::TestSettingsService::test_set_and_get_currency PASSED
tests/test_transactions.py::TestTransactionService::test_add_and_get_transaction PASSED
tests/test_transactions.py::TestTransactionService::test_filter_and_search PASSED
tests/test_transactions.py::TestTransactionsService::test_invalid_transaction_inputs PASSED
tests/test_transactions.py::TestTransactionService::test_summary_and_category_breakdown PASSED
tests/test_transactions.py::TestTransactionService::test_update_and_delete_transaction PASSED
```

---

## 🔒 Financial Integrity & Security
- **No Hardcoded Data**: Transactions and budgets are stored permanently in local SQLite tables (`expense_tracker.db`).
- **Parameterized SQL**: All database queries use parameterized SQL bindings to completely prevent SQL injection.
- **Defensive Input Validation**: Inputs are validated for positive amounts, standard dates, and non-empty strings before touching the database.
- **Accurate Calculations**: Decimal rounding and strict balance verification ensure zero calculation drift.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

