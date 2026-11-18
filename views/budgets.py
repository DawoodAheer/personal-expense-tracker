"""
Budget Management View: Set monthly and category budgets, track real-time progress,
and view clear alerts at 80% and 100% thresholds.
"""

from datetime import date
import streamlit as st
from services.budget_service import (
    set_budget,
    delete_budget,
    get_budget_status,
)
from services.settings_service import get_active_currency
from database.queries import DEFAULT_EXPENSE_CATEGORIES
from utils.formatters import format_currency


def render_budgets():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("Budget Management")
    st.caption("Establish monthly spending limits by category and track threshold alerts at 80% and 100%.")

    # Select month
    current_month_str = date.today().strftime("%Y-%m")
    col_m, _ = st.columns([2, 3])
    with col_m:
        month_input = st.text_input("Budget Month (YYYY-MM)", value=current_month_str)

    # 1. Set or Update Budget Form
    with st.expander("➕ Set or Update Budget Limit", expanded=True):
        with st.form("set_budget_form"):
            b_cat_options = ["Overall"] + DEFAULT_EXPENSE_CATEGORIES
            b_category = st.selectbox("Budget Target", b_cat_options)
            b_amount = st.number_input(
                f"Budget Limit ({sym})",
                min_value=1.0,
                max_value=1_000_000_000.0,
                step=50.0,
                format="%.2f",
                help=f"Define monthly spending limit in {active_curr['name']}",
            )

            save_budget_btn = st.form_submit_button("Save Budget", type="primary", use_container_width=True)
            if save_budget_btn:
                try:
                    set_budget(
                        month=month_input.strip(),
                        category=b_category,
                        amount=b_amount,
                    )
                    st.success(f"Budget for '{b_category}' set to {format_currency(b_amount)} for {month_input}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error setting budget: {e}")

    # 2. Budget Performance & Alerts
    st.subheader(f"Budget Performance for {month_input}")
    statuses = get_budget_status(month_input.strip())

    if not statuses:
        st.info(f"No budgets configured yet for {month_input}. Use the form above to define your targets.")
        return

    # Delete budget state
    if "confirm_delete_budget_id" not in st.session_state:
        st.session_state.confirm_delete_budget_id = None

    if st.session_state.confirm_delete_budget_id is not None:
        b_id = st.session_state.confirm_delete_budget_id
        st.error(f"⚠️ Confirm removing budget #{b_id}?")
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("Yes, Remove", type="primary"):
                delete_budget(b_id)
                st.session_state.confirm_delete_budget_id = None
                st.success("Budget removed.")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state.confirm_delete_budget_id = None
                st.rerun()
        st.markdown("---")

    # Display each budget with progress bars and color-coded alert status
    for item in statuses:
        cat = item["category"]
        budget_amt = item["budget"]
        spent_amt = item["spent"]
        remaining_amt = item["remaining"]
        pct = item["percentage"]
        alert = item["alert_level"]

        # Alert banner styles
        if alert == "EXCEEDED":
            badge_html = f"<span style='background-color:#FEE2E2;color:#DC2626;padding:3px 8px;border-radius:6px;font-weight:600;'>🚨 EXCEEDED ({pct:.1f}%)</span>"
        elif alert == "WARNING":
            badge_html = f"<span style='background-color:#FEF3C7;color:#D97706;padding:3px 8px;border-radius:6px;font-weight:600;'>⚠️ ALERT &ge;80% ({pct:.1f}%)</span>"
        else:
            badge_html = f"<span style='background-color:#DCFCE7;color:#16A34A;padding:3px 8px;border-radius:6px;font-weight:600;'>✅ ON TRACK ({pct:.1f}%)</span>"

        with st.container():
            c_header, c_badge, c_del = st.columns([3, 2, 1])
            with c_header:
                st.markdown(f"**{cat}**")
            with c_badge:
                st.markdown(badge_html, unsafe_allow_html=True)
            with c_del:
                if st.button("Delete", key=f"del_b_{item['id']}"):
                    st.session_state.confirm_delete_budget_id = item["id"]
                    st.rerun()

            # Progress bar normalized to 0.0 - 1.0 (clamped)
            progress_ratio = min(max(spent_amt / budget_amt, 0.0), 1.0) if budget_amt > 0 else 0.0
            st.progress(progress_ratio)

            col_sub1, col_sub2, col_sub3 = st.columns(3)
            with col_sub1:
                st.caption(f"Budget: **{format_currency(budget_amt)}**")
            with col_sub2:
                st.caption(f"Spent: **{format_currency(spent_amt)}**")
            with col_sub3:
                if remaining_amt >= 0:
                    st.caption(f"Remaining: <span style='color:green;font-weight:bold;'>{format_currency(remaining_amt)}</span>", unsafe_allow_html=True)
                else:
                    st.caption(f"Over Budget: <span style='color:red;font-weight:bold;'>{format_currency(abs(remaining_amt))}</span>", unsafe_allow_html=True)

            st.markdown("---")

