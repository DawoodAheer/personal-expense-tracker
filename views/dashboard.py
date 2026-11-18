"""
Dashboard View: Financial overview metrics, visual charts, and budget alert badges.
"""

from datetime import date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from services.transaction_service import (
    get_summary_stats,
    get_category_breakdown,
    get_monthly_trend,
    get_all_transactions,
)
from services.budget_service import get_budget_status
from services.report_service import get_available_months
from services.settings_service import get_active_currency
from utils.formatters import format_currency


def render_dashboard():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("Financial Dashboard")
    st.caption(f"Live cash flow, spending breakdown, and budgets in {active_curr['name']} ({sym}).")

    # Time frame filter selector
    col_filter1, col_filter2 = st.columns([2, 2])
    with col_filter1:
        months = ["All Time"] + get_available_months()
        selected_month = st.selectbox("Select Time Period", months, index=0)

    month_arg = None if selected_month == "All Time" else selected_month

    # Budget alerts banner if active for the month
    current_m = date.today().strftime("%Y-%m")
    check_month = month_arg if month_arg else current_m
    budget_statuses = get_budget_status(check_month)

    critical_alerts = [b for b in budget_statuses if b["alert_level"] == "EXCEEDED"]
    warning_alerts = [b for b in budget_statuses if b["alert_level"] == "WARNING"]

    if critical_alerts:
        for b in critical_alerts:
            st.error(f"🚨 **Budget Exceeded:** {b['alert_message']}")
    if warning_alerts:
        for b in warning_alerts:
            st.warning(f"⚠️ **Budget Alert (>=80%):** {b['alert_message']}")

    # 1. Key Metrics Cards
    stats = get_summary_stats(month=month_arg)
    income = stats["total_income"]
    expense = stats["total_expenses"]
    balance = stats["current_balance"]
    savings_rate = stats["savings_rate"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Total Income",
            value=format_currency(income),
            help="Total earnings recorded in the selected period",
        )
    with m2:
        st.metric(
            label="Total Expenses",
            value=format_currency(expense),
            delta=f"-{format_currency(expense)}" if expense > 0 else "$0.00",
            delta_color="inverse",
            help="Total spending across all categories",
        )
    with m3:
        balance_color = "normal" if balance >= 0 else "inverse"
        st.metric(
            label="Current Balance",
            value=format_currency(balance),
            delta=f"{format_currency(balance)} net",
            delta_color=balance_color,
            help="Income minus total expenses",
        )
    with m4:
        st.metric(
            label="Savings Rate",
            value=f"{savings_rate:.1f}%",
            delta="Healthy (>=20%)" if savings_rate >= 20 else ("Moderate" if savings_rate >= 10 else "Low"),
            delta_color="normal" if savings_rate >= 20 else "off",
            help="Percentage of income saved",
        )

    st.markdown("---")

    # 2. Charts Section
    tab1, tab2, tab3 = st.tabs(["Income vs Expenses", "Expense Breakdown", "Income Sources"])

    with tab1:
        st.subheader("Income vs Expenses Comparison")
        trend_df = get_monthly_trend()
        if not trend_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=trend_df["month"],
                y=trend_df["total_income"],
                name="Income",
                marker_color="#10B981",
            ))
            fig.add_trace(go.Bar(
                x=trend_df["month"],
                y=trend_df["total_expense"],
                name="Expense",
                marker_color="#EF4444",
            ))
            fig.add_trace(go.Scatter(
                x=trend_df["month"],
                y=trend_df["net_savings"],
                name="Net Savings",
                mode="lines+markers",
                line=dict(color="#3B82F6", width=3),
                marker=dict(size=7),
            ))
            fig.update_layout(
                barmode="group",
                xaxis_title="Month",
                yaxis_title=f"Amount ({sym})",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=30, b=20),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction data available yet. Start by recording your income and expenses.")

    with tab2:
        st.subheader("Expenses by Category")
        exp_df = get_category_breakdown("expense", month=month_arg)
        if not exp_df.empty:
            c1, c2 = st.columns([3, 2])
            with c1:
                fig_donut = px.pie(
                    exp_df,
                    names="category",
                    values="total",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                )
                fig_donut.update_traces(textposition="inside", textinfo="percent+label")
                fig_donut.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
                    margin=dict(l=10, r=10, t=20, b=20),
                    height=360,
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            with c2:
                st.write("**Top Expense Categories**")
                display_exp = exp_df.copy()
                display_exp["total_formatted"] = display_exp["total"].apply(lambda v: format_currency(v))
                display_exp["share"] = (display_exp["total"] / display_exp["total"].sum() * 100).apply(lambda v: f"{v:.1f}%")
                disp_exp = display_exp[["category", "total_formatted", "share", "count"]].copy()
                disp_exp.columns = ["Category", "Total", "% Share", "Transactions"]
                st.dataframe(
                    disp_exp,
                    hide_index=True,
                    use_container_width=True,
                )
        else:
            st.info("No expenses recorded for this period.")

    with tab3:
        st.subheader("Income by Source")
        inc_df = get_category_breakdown("income", month=month_arg)
        if not inc_df.empty:
            fig_inc = px.pie(
                inc_df,
                names="category",
                values="total",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_inc.update_traces(textposition="inside", textinfo="percent+label")
            fig_inc.update_layout(
                showlegend=True,
                margin=dict(l=10, r=10, t=20, b=20),
                height=360,
            )
            st.plotly_chart(fig_inc, use_container_width=True)
        else:
            st.info("No income recorded for this period.")

    # 3. Recent Transactions Table Preview
    st.markdown("---")
    st.subheader("Recent Activity")
    recent_df = get_all_transactions(month=month_arg)
    if not recent_df.empty:
        display_recent = recent_df.head(6).copy()
        display_recent["amount"] = display_recent["amount"].apply(lambda v: format_currency(v))
        display_recent["type"] = display_recent["type"].apply(lambda t: t.capitalize())
        disp_recent = display_recent[["date", "type", "category", "amount", "payment_method", "description"]].copy()
        disp_recent.columns = ["Date", "Type", "Category", "Amount", "Payment Method", "Description"]
        st.dataframe(
            disp_recent,
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.write("No transactions recorded yet.")

