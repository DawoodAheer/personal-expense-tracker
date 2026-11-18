"""
Personal Expense Tracker - Main Streamlit Application Entrypoint.
A comprehensive personal financial management system with SQLite storage,
interactive Plotly visualizations, budget alerts, and PDF/CSV reporting.
"""

from datetime import date
import streamlit as st
from database.db import init_db
from views.dashboard import render_dashboard
from views.add_income import render_add_income
from views.add_expense import render_add_expense
from views.transactions import render_transactions
from views.budgets import render_budgets
from views.reports import render_reports
from views.export import render_export
from views.settings_view import render_settings
from views.goals import render_goals
from views.recurring import render_recurring
from views.khata import render_khata
from services.transaction_service import get_summary_stats
from services.budget_service import get_budget_status
from services.settings_service import get_active_currency, get_theme, set_theme
from services.recurring_service import process_due_recurring
from utils.formatters import format_currency

# Set wide layout and app metadata
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

def apply_theme_css(theme: str) -> None:
    """Inject responsive Light or Dark mode stylesheet."""
    if theme == "dark":
        css = """
        <style>
            .stApp {
                background-color: #0F172A;
                color: #F8FAFC;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
            }
            div[data-testid="stMetric"] {
                background-color: #1E293B;
                border: 1px solid #334155;
                padding: 14px 18px;
                border-radius: 10px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            }
            div[data-testid="stMetric"] label {
                font-weight: 600;
                color: #94A3B8 !important;
            }
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                font-size: 1.6rem;
                font-weight: 700;
                color: #F8FAFC !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #0B0F19;
                color: #F8FAFC;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] label {
                color: #CBD5E1;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 6px;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                background-color: #1E293B;
            }
            div[data-testid="stExpander"] {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            h1, h2, h3, h4 {
                color: #F8FAFC !important;
            }
            hr {
                margin: 1.5rem 0;
                border-color: #334155;
            }
        </style>
        """
    else:
        css = """
        <style>
            .stApp {
                background-color: #FFFFFF;
                color: #0F172A;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
            }
            div[data-testid="stMetric"] {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                padding: 14px 18px;
                border-radius: 10px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            div[data-testid="stMetric"] label {
                font-weight: 600;
                color: #475569 !important;
            }
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                font-size: 1.6rem;
                font-weight: 700;
                color: #0F172A !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #0F172A;
                color: #F8FAFC;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] label {
                color: #E2E8F0;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 6px;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                background-color: #1E293B;
            }
            hr {
                margin: 1.5rem 0;
                border-color: #E2E8F0;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def main():
    # Ensure database tables exist
    init_db()

    # Process due recurring transactions on startup
    if "recurring_checked" not in st.session_state:
        auto_txs = process_due_recurring()
        st.session_state.recurring_checked = True
        if auto_txs:
            st.session_state.recurring_notice_count = len(auto_txs)

    # Initialize theme
    if "app_theme" not in st.session_state:
        st.session_state.app_theme = get_theme()

    active_theme = st.session_state.app_theme
    apply_theme_css(active_theme)

    # Display recurring transactions alert banner if auto-recorded
    if st.session_state.get("recurring_notice_count"):
        count = st.session_state.pop("recurring_notice_count")
        st.info(f"🔄 **Auto-recorded {count} recurring transaction(s)** that were due today! See 'Transactions' or 'Recurring Entries' for details.")

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.markdown("## 💰 Expense Tracker")
        st.caption("Personal Finance & Budget Control")
        st.markdown("---")

        nav_options = [
            "📊 Dashboard",
            "➕ Add Income",
            "➖ Add Expense",
            "📝 Smart Khata & Notes",
            "📋 Transactions",
            "🎯 Budget Management",
            "🏆 Financial Goals",
            "🔁 Recurring Entries",
            "📈 Monthly Reports",
            "💾 Export Data",
            "⚙️ Settings & Currency",
        ]

        selected_page = st.radio("Navigation", nav_options, index=0)

        st.markdown("---")

        # Theme toggle selector in sidebar
        st.markdown("**🌓 Theme Mode**")
        chosen_theme_label = st.radio(
            "Select Theme",
            options=["☀️ Light", "🌙 Dark"],
            index=0 if active_theme == "light" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        selected_theme = "light" if "Light" in chosen_theme_label else "dark"
        if selected_theme != active_theme:
            set_theme(selected_theme)
            st.session_state.app_theme = selected_theme
            st.rerun()

        st.markdown("---")
        
        # Active Currency Badge
        curr = get_active_currency()
        st.markdown(f"**🌐 Currency:** `{curr['code']}` ({curr['symbol']})")

        # Sidebar Quick Financial Pulse
        curr_month = date.today().strftime("%Y-%m")
        stats = get_summary_stats(month=curr_month)
        b_statuses = get_budget_status(curr_month)
        critical_alerts = sum(1 for b in b_statuses if b["alert_level"] in ("WARNING", "EXCEEDED"))

        st.markdown(f"**This Month ({curr_month})**")
        st.write(f"💵 **Balance:** {format_currency(stats['current_balance'])}")
        st.write(f"📉 **Expenses:** {format_currency(stats['total_expenses'])}")

        if critical_alerts > 0:
            st.warning(f"⚠️ {critical_alerts} Budget Alert(s) Active")
        else:
            st.success("✅ Budgets On Track")

        st.markdown("---")
        st.caption("v1.3.0 • Multi-Currency • Goals • Recurring")

    # --- Page Routing ---
    if selected_page == "📊 Dashboard":
        render_dashboard()
    elif selected_page == "➕ Add Income":
        render_add_income()
    elif selected_page == "➖ Add Expense":
        render_add_expense()
    elif selected_page == "📝 Smart Khata & Notes":
        render_khata()
    elif selected_page == "📋 Transactions":
        render_transactions()
    elif selected_page == "🎯 Budget Management":
        render_budgets()
    elif selected_page == "🏆 Financial Goals":
        render_goals()
    elif selected_page == "🔁 Recurring Entries":
        render_recurring()
    elif selected_page == "📈 Monthly Reports":
        render_reports()
    elif selected_page == "💾 Export Data":
        render_export()
    elif selected_page == "⚙️ Settings & Currency":
        render_settings()


if __name__ == "__main__":
    main()

