"""
Add Income View: Record income earnings with source, date, amount, and description.
"""

from datetime import date
import streamlit as st
from database.queries import DEFAULT_INCOME_CATEGORIES
from services.transaction_service import add_transaction, get_all_transactions
from services.settings_service import get_active_currency
from utils.formatters import format_currency


def render_add_income():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("Record Income")
    st.caption("Log your paychecks, freelance payouts, dividends, or other revenue streams.")

    col1, col2 = st.columns([3, 2])

    with col1:
        with st.form("add_income_form", clear_on_submit=True):
            st.subheader("Income Details")

            amount = st.number_input(
                f"Amount ({sym}) *",
                min_value=0.01,
                max_value=1_000_000_000.00,
                step=10.0,
                format="%.2f",
                help=f"Enter positive income amount in {active_curr['name']}",
            )

            category_options = DEFAULT_INCOME_CATEGORIES + ["+ Custom Source..."]
            selected_cat = st.selectbox("Income Source / Category *", category_options)

            if selected_cat == "+ Custom Source...":
                custom_cat = st.text_input("Enter Custom Source Name *")
                final_category = custom_cat.strip()
            else:
                final_category = selected_cat

            tx_date = st.date_input("Date *", value=date.today())

            payment_method_options = [
                "Direct Deposit",
                "Bank Transfer",
                "Cash",
                "Check",
                "Mobile Wallet / PayPal",
                "Other",
            ]
            payment_method = st.selectbox("Payment / Deposit Method *", payment_method_options)

            description = st.text_input(
                "Description / Notes (Optional)",
                placeholder="e.g. Monthly salary from Acme Corp, Freelance UI design milestone",
            )

            submitted = st.form_submit_button("Record Income", use_container_width=True, type="primary")

            if submitted:
                if not final_category:
                    st.error("Please specify a valid income source.")
                elif amount <= 0:
                    st.error("Please enter a valid amount greater than 0.")
                else:
                    try:
                        tx = add_transaction(
                            trans_type="income",
                            amount=amount,
                            category=final_category,
                            payment_method=payment_method,
                            date_str=tx_date.strftime("%Y-%m-%d"),
                            description=description,
                        )
                        st.success(
                            f"Successfully recorded income of {format_currency(tx['amount'])} from '{tx['category']}' on {tx['date']}!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving transaction: {e}")

    with col2:
        st.subheader("Recent Income Entries")
        inc_df = get_all_transactions(trans_type="income")
        if not inc_df.empty:
            recent_inc = inc_df.head(5).copy()
            recent_inc["Amount"] = recent_inc["amount"].apply(lambda v: format_currency(v))
            disp_inc = recent_inc[["date", "category", "Amount", "description"]].copy()
            disp_inc.columns = ["Date", "Source", "Amount", "Notes"]
            st.dataframe(
                disp_inc,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No income records found yet.")

