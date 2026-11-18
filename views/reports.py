"""
Monthly Reports View: Generates monthly summaries, month-over-month comparisons,
and detailed spending pattern analyses.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from services.report_service import (
    get_available_months,
    get_monthly_summary,
    get_monthly_comparison,
)
from services.settings_service import get_active_currency
from services.transaction_service import get_all_transactions
from utils.formatters import format_currency


def render_reports():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("Monthly Financial Reports")
    st.caption("Deep financial breakdown, period comparisons, and spending habits.")

    available_months = get_available_months()
    if not available_months:
        st.info("No transaction records available to generate reports.")
        return

    selected_month = st.selectbox("Select Reporting Month", available_months, index=0)

    summary = get_monthly_summary(selected_month)
    comparison = get_monthly_comparison(selected_month)

    # 1. Monthly Summary Cards
    st.subheader(f"Executive Summary &bull; {selected_month}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Income", format_currency(summary["income"]))
    with c2:
        st.metric("Total Expenses", format_currency(summary["expense"]))
    with c3:
        bal = summary["net_savings"]
        st.metric("Net Savings", format_currency(bal), delta_color="normal" if bal >= 0 else "inverse")
    with c4:
        st.metric("Savings Rate", f"{summary['savings_rate']:.1f}%")

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.info(f"🏆 **Top Expense:** {summary['top_category']} ({format_currency(summary['top_category_amount'])}, {summary['top_category_pct']:.1f}%)")
    with col_stat2:
        st.info(f"📅 **Peak Spending Day:** {summary['peak_spending_day']} ({format_currency(summary['peak_spending_amount'])})")
    with col_stat3:
        st.info(f"📊 **Daily Average Spending:** {format_currency(summary['daily_average'])}")

    st.markdown("---")

    # 2. Month-over-Month Comparison
    st.subheader(f"Comparison vs Previous Month ({comparison['previous_month']})")
    cmp1, cmp2, cmp3 = st.columns(3)
    with cmp1:
        st.metric(
            label="Income Delta",
            value=format_currency(summary["income"]),
            delta=f"{comparison['income_delta']:+,.2f} ({comparison['income_pct_delta']:+.1f}%)",
        )
    with cmp2:
        st.metric(
            label="Expense Delta",
            value=format_currency(summary["expense"]),
            delta=f"{comparison['expense_delta']:+,.2f} ({comparison['expense_pct_delta']:+.1f}%)",
            delta_color="inverse",
        )
    with cmp3:
        st.metric(
            label="Savings Delta",
            value=format_currency(summary["net_savings"]),
            delta=f"{comparison['savings_delta']:+,.2f} ({comparison['savings_pct_delta']:+.1f}%)",
        )

    # Category comparison table
    if comparison["category_changes"]:
        with st.expander("📊 View Category-by-Category Comparison"):
            cat_df = pd.DataFrame(comparison["category_changes"])
            cat_df["current_month"] = cat_df["current_month"].apply(lambda v: format_currency(v))
            cat_df["prev_month"] = cat_df["prev_month"].apply(lambda v: format_currency(v))
            cat_df["difference"] = cat_df["difference"].apply(lambda v: f"{v:+,.2f}")
            cat_df["pct_change"] = cat_df["pct_change"].apply(lambda v: f"{v:+.1f}%")
            disp_cat = cat_df[["category", "current_month", "prev_month", "difference", "pct_change"]].copy()
            disp_cat.columns = ["Category", selected_month, comparison["previous_month"], "Difference", "Change (%)"]
            st.dataframe(
                disp_cat,
                hide_index=True,
                use_container_width=True,
            )

    st.markdown("---")

    # 3. Deep Spending Analysis Charts
    st.subheader("Spending Analysis")
    ch_col1, ch_col2 = st.columns(2)

    with ch_col1:
        st.write("**Expenses by Category**")
        cat_rows = summary.get("category_breakdown", [])
        if cat_rows:
            df_cat = pd.DataFrame(cat_rows)
            fig_cat = px.bar(
                df_cat,
                x="category",
                y="total",
                text="total",
                color="category",
                labels={"total": f"Amount ({sym})", "category": "Category"},
            )
            fig_cat.update_traces(texttemplate=f"{sym}%{{y:,.2f}}", textposition="outside")
            fig_cat.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No expense breakdown data.")

    with ch_col2:
        st.write("**Expenses by Payment Method**")
        pm_rows = summary.get("payment_method_breakdown", [])
        if pm_rows:
            df_pm = pd.DataFrame(pm_rows)
            fig_pm = px.pie(
                df_pm,
                names="payment_method",
                values="total",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_pm.update_traces(textinfo="percent+label")
            fig_pm.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(fig_pm, use_container_width=True)
        else:
            st.info("No payment method data.")

    # Daily spending curve for this month
    df_tx = get_all_transactions(month=selected_month, trans_type="expense")
    if not df_tx.empty:
        st.write("**Daily Spending Activity**")
        daily_trend = pd.DataFrame(df_tx.groupby("date")["amount"].sum()).reset_index()
        fig_daily = px.area(
            daily_trend,
            x="date",
            y="amount",
            labels={"date": "Date", "amount": f"Spending ({sym})"},
            color_discrete_sequence=["#EF4444"],
        )
        fig_daily.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
        st.plotly_chart(fig_daily, use_container_width=True)

