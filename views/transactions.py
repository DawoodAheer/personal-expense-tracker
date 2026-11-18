"""
Transactions View: Search, filter, view, edit, and safely delete financial records.
"""

from datetime import datetime, date, timedelta
import streamlit as st
from services.transaction_service import (
    get_all_transactions,
    get_transaction,
    update_transaction,
    delete_transaction,
)
from database.queries import DEFAULT_INCOME_CATEGORIES, DEFAULT_EXPENSE_CATEGORIES, DEFAULT_PAYMENT_METHODS
from services.settings_service import get_active_currency
from utils.formatters import format_currency


def render_transactions():
    sym = get_active_currency()["symbol"]
    st.title("Transaction History")
    st.caption("Search, filter, update, or remove your income and expense transactions.")

    # --- Deletion Confirmation Dialog / State Handling ---
    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None
    if "editing_tx_id" not in st.session_state:
        st.session_state.editing_tx_id = None

    # Handle delete confirmation banner
    if st.session_state.confirm_delete_id is not None:
        del_id = st.session_state.confirm_delete_id
        tx_to_del = get_transaction(del_id)
        if tx_to_del:
            st.error(
                f"⚠️ **Confirm Deletion:** Are you sure you want to permanently delete Transaction **#{del_id}** "
                f"({tx_to_del['type'].upper()} of {format_currency(tx_to_del['amount'])} on {tx_to_del['date']})?"
            )
            c_yes, c_no, _ = st.columns([1, 1, 4])
            with c_yes:
                if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
                    delete_transaction(del_id)
                    st.session_state.confirm_delete_id = None
                    st.success(f"Transaction #{del_id} deleted successfully.")
                    st.rerun()
            with c_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            st.markdown("---")

    # Handle Edit Transaction Form
    if st.session_state.editing_tx_id is not None:
        edit_id = st.session_state.editing_tx_id
        tx = get_transaction(edit_id)
        if tx:
            st.markdown(f"### ✏️ Edit Transaction #{edit_id}")
            with st.form("edit_tx_form"):
                e_type = st.radio("Type", ["income", "expense"], index=0 if tx["type"] == "income" else 1, horizontal=True)
                e_amount = st.number_input(f"Amount ({sym})", value=float(tx["amount"]), min_value=0.01, step=5.0, format="%.2f")

                all_cat_options = sorted(set(DEFAULT_INCOME_CATEGORIES + DEFAULT_EXPENSE_CATEGORIES + [tx["category"]]))
                cat_idx = all_cat_options.index(tx["category"]) if tx["category"] in all_cat_options else 0
                e_category = st.selectbox("Category", all_cat_options, index=cat_idx)

                all_pm_options = sorted(set(DEFAULT_PAYMENT_METHODS + [tx["payment_method"]]))
                pm_idx = all_pm_options.index(tx["payment_method"]) if tx["payment_method"] in all_pm_options else 0
                e_payment_method = st.selectbox("Payment Method", all_pm_options, index=pm_idx)

                tx_d = datetime.strptime(tx["date"], "%Y-%m-%d").date()
                e_date = st.date_input("Date", value=tx_d)
                e_desc = st.text_input("Description", value=tx["description"] or "")

                col_save, col_cancel = st.columns(2)
                with col_save:
                    save_btn = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                with col_cancel:
                    cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                if save_btn:
                    try:
                        update_transaction(
                            transaction_id=edit_id,
                            trans_type=e_type,
                            amount=e_amount,
                            category=e_category,
                            payment_method=e_payment_method,
                            date_str=e_date.strftime("%Y-%m-%d"),
                            description=e_desc,
                        )
                        st.session_state.editing_tx_id = None
                        st.success("Transaction updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating transaction: {e}")

                if cancel_btn:
                    st.session_state.editing_tx_id = None
                    st.rerun()
            st.markdown("---")

    # --- Filters Section ---
    with st.expander("🔍 Search and Filter Options", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            search_query = st.text_input("Search Keyword", placeholder="Search notes, category, merchant...")
        with f2:
            type_filter = st.selectbox("Transaction Type", ["All", "Income", "Expense"])
        with f3:
            payment_filter = st.selectbox("Payment Method", ["All"] + DEFAULT_PAYMENT_METHODS)

        f4, f5, f6 = st.columns(3)
        with f4:
            all_known_cats = sorted(set(DEFAULT_INCOME_CATEGORIES + DEFAULT_EXPENSE_CATEGORIES))
            cat_filter = st.selectbox("Category", ["All"] + all_known_cats)
        with f5:
            use_date_range = st.checkbox("Filter by Date Range", value=False)
        with f6:
            if use_date_range:
                today = date.today()
                start_date_val = st.date_input("Start Date", value=today - timedelta(days=30))
                end_date_val = st.date_input("End Date", value=today)
                start_str = start_date_val.strftime("%Y-%m-%d")
                end_str = end_date_val.strftime("%Y-%m-%d")
            else:
                start_str = None
                end_str = None

    # Retrieve filtered data
    df = get_all_transactions(
        trans_type=type_filter,
        category=cat_filter,
        payment_method=payment_filter,
        search_query=search_query,
        start_date=start_str,
        end_date=end_str,
    )

    st.write(f"**Found {len(df)} transactions**")

    if df.empty:
        st.info("No transactions match the selected filters.")
        return

    # Display Data Table with action buttons
    display_df = df.copy()
    display_df["amount_formatted"] = display_df["amount"].apply(lambda v: format_currency(v))
    display_df["type_formatted"] = display_df["type"].apply(lambda t: t.capitalize())

    disp_tx = display_df[["id", "date", "type_formatted", "category", "amount_formatted", "payment_method", "description"]].copy()
    disp_tx.columns = ["ID", "Date", "Type", "Category", "Amount", "Payment Method", "Description"]

    st.dataframe(
        disp_tx,
        hide_index=True,
        use_container_width=True,
    )

    # Edit & Delete Action Bar
    st.markdown("#### Manage Record")
    col_sel, col_action1, col_action2 = st.columns([2, 1, 1])

    available_ids = df["id"].tolist()
    with col_sel:
        target_id = st.selectbox("Select Transaction by ID to Edit or Delete", available_ids)

    with col_action1:
        if st.button("✏️ Edit Selected", use_container_width=True):
            st.session_state.editing_tx_id = target_id
            st.rerun()

    with col_action2:
        if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
            st.session_state.confirm_delete_id = target_id
            st.rerun()

