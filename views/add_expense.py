"""
Add Expense View: Record expenses with amount, category, date, payment method, and description.
Includes intelligent pre-check warnings when spending approaches or exceeds budget limits.
"""

from datetime import date
import streamlit as st
from database.queries import DEFAULT_EXPENSE_CATEGORIES, DEFAULT_PAYMENT_METHODS
from services.transaction_service import add_transaction, get_all_transactions
from services.budget_service import get_budget_alert_for_expense
from services.settings_service import get_active_currency
from utils.formatters import format_currency


def render_add_expense():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("Record Expense")
    st.caption("Track daily purchases, bills, and spending to stay within your budget.")

    col1, col2 = st.columns([3, 2])

    with col1:
        with st.form("add_expense_form", clear_on_submit=True):
            st.subheader("Expense Details")

            amount = st.number_input(
                f"Amount ({sym}) *",
                min_value=0.01,
                max_value=1_000_000_000.00,
                step=5.0,
                format="%.2f",
                help=f"Enter positive expense amount in {active_curr['name']}",
            )

            category_options = DEFAULT_EXPENSE_CATEGORIES + ["+ Custom Category..."]
            selected_cat = st.selectbox("Category *", category_options)

            if selected_cat == "+ Custom Category...":
                custom_cat = st.text_input("Enter Custom Category Name *")
                final_category = custom_cat.strip()
            else:
                final_category = selected_cat

            tx_date = st.date_input("Date *", value=date.today())

            payment_method = st.selectbox("Payment Method *", DEFAULT_PAYMENT_METHODS)

            description = st.text_input(
                "Description / Merchant (Optional)",
                placeholder="e.g. Trader Joe's, Electricity Bill, Shell Gas Station",
            )

            submitted = st.form_submit_button("Record Expense", use_container_width=True, type="primary")

            if submitted:
                if not final_category:
                    st.error("Please specify a valid expense category.")
                elif amount <= 0:
                    st.error("Please enter a valid amount greater than 0.")
                else:
                    date_str = tx_date.strftime("%Y-%m-%d")

                    # Check budget impact warnings
                    budget_alerts = get_budget_alert_for_expense(
                        category=final_category,
                        amount=amount,
                        date_str=date_str,
                    )

                    try:
                        tx = add_transaction(
                            trans_type="expense",
                            amount=amount,
                            category=final_category,
                            payment_method=payment_method,
                            date_str=date_str,
                            description=description,
                        )
                        st.success(
                            f"Recorded expense of {format_currency(tx['amount'])} under '{tx['category']}' on {tx['date']}!"
                        )

                        if budget_alerts:
                            for alert in budget_alerts:
                                st.warning(f"⚠️ {alert}")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving expense: {e}")

    with col2:
        st.subheader("Recent Expenses")
        exp_df = get_all_transactions(trans_type="expense")
        if not exp_df.empty:
            recent_exp = exp_df.head(5).copy()
            recent_exp["Amount"] = recent_exp["amount"].apply(lambda v: format_currency(v))
            disp_exp = recent_exp[["date", "category", "Amount", "payment_method", "description"]].copy()
            disp_exp.columns = ["Date", "Category", "Amount", "Payment", "Notes"]
            st.dataframe(
                disp_exp,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No expense records found yet.")

