"""
Optional Demo Data Seeder for Personal Expense Tracker.
Run `python seed_sample_data.py` to populate realistic demo transactions and budgets
for testing and demonstration purposes.
"""

from datetime import date
from database.db import init_db
from services.transaction_service import add_transaction
from services.budget_service import set_budget


def seed_demo_data():
    init_db()
    today = date.today()
    curr_month = today.strftime("%Y-%m")

    print(f"Seeding demo transactions and budgets for {curr_month}...")

    # Income
    add_transaction(
        trans_type="income",
        amount=5500.0,
        category="Salary",
        payment_method="Direct Deposit",
        date_str=f"{curr_month}-01",
        description="Monthly tech employment paycheck",
    )
    add_transaction(
        trans_type="income",
        amount=850.0,
        category="Freelance & Consulting",
        payment_method="Bank Transfer",
        date_str=f"{curr_month}-08",
        description="Web application consulting project",
    )
    add_transaction(
        trans_type="income",
        amount=120.0,
        category="Investments & Dividends",
        payment_method="Direct Deposit",
        date_str=f"{curr_month}-10",
        description="Quarterly index fund dividend payout",
    )

    # Expenses
    expenses = [
        ("Rent & Housing", 1600.0, "Bank Transfer", f"{curr_month}-01", "Monthly apartment lease payment"),
        ("Groceries", 280.50, "Debit Card", f"{curr_month}-03", "Weekly organic groceries"),
        ("Utilities & Bills", 145.0, "Credit Card", f"{curr_month}-04", "Electric, water & fiber internet"),
        ("Transportation & Fuel", 65.0, "Credit Card", f"{curr_month}-05", "Fuel refill"),
        ("Food & Dining", 85.0, "Credit Card", f"{curr_month}-06", "Dinner at Italian bistro"),
        ("Entertainment & Leisure", 24.99, "Credit Card", f"{curr_month}-07", "Streaming subscriptions"),
        ("Groceries", 175.20, "Debit Card", f"{curr_month}-09", "Mid-month supermarket haul"),
        ("Healthcare & Medical", 45.0, "Debit Card", f"{curr_month}-10", "Prescription & vitamins"),
    ]

    for cat, amt, pm, dt, desc in expenses:
        add_transaction(
            trans_type="expense",
            amount=amt,
            category=cat,
            payment_method=pm,
            date_str=dt,
            description=desc,
        )

    # Budgets
    set_budget(month=curr_month, category="Overall", amount=3500.0)
    set_budget(month=curr_month, category="Rent & Housing", amount=1600.0)
    set_budget(month=curr_month, category="Groceries", amount=600.0)
    set_budget(month=curr_month, category="Food & Dining", amount=200.0)
    set_budget(month=curr_month, category="Utilities & Bills", amount=180.0)
    set_budget(month=curr_month, category="Transportation & Fuel", amount=150.0)

    print("Demo data seeded successfully! You can now launch `streamlit run app.py`.")


if __name__ == "__main__":
    seed_demo_data()

