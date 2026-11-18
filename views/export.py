"""
Export Data View: Download filtered transaction records as CSV and monthly reports as PDF.
"""

from datetime import date
import streamlit as st
from services.transaction_service import get_all_transactions
from services.report_service import get_available_months, get_monthly_summary
from services.budget_service import get_budget_status
from services.export_service import export_transactions_to_csv, generate_monthly_pdf_report
from utils.formatters import format_currency


def render_export():
    st.title("Export Financial Data")
    st.caption("Download your transactions as spreadsheet-ready CSV or download formal Monthly Reports as styled PDFs.")

    tab_csv, tab_pdf = st.tabs(["📄 Export Transactions (CSV)", "📑 Export Monthly Report (PDF)"])

    # 1. CSV Export Tab
    with tab_csv:
        st.subheader("Download Transactions as CSV")
        st.write("Export your complete transaction history or filter by month and type.")

        c1, c2 = st.columns(2)
        with c1:
            months = ["All Time"] + get_available_months()
            csv_month = st.selectbox("Select Time Period for CSV", months, key="csv_m")
        with c2:
            csv_type = st.selectbox("Select Transaction Type", ["All", "Income", "Expense"], key="csv_t")

        filter_month = None if csv_month == "All Time" else csv_month
        df_export = get_all_transactions(month=filter_month, trans_type=csv_type)

        st.write(f"Total records to export: **{len(df_export)}**")

        if not df_export.empty:
            csv_bytes = export_transactions_to_csv(df_export)
            file_name = f"transactions_{csv_month.lower().replace(' ', '_')}_{csv_type.lower()}.csv"

            st.download_button(
                label="⬇️ Download CSV File",
                data=csv_bytes,
                file_name=file_name,
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

            with st.expander("Preview CSV Data", expanded=False):
                st.dataframe(df_export, hide_index=True, use_container_width=True)
        else:
            st.info("No transaction data matches the selected criteria to export.")

    # 2. PDF Export Tab
    with tab_pdf:
        st.subheader("Generate & Download Monthly PDF Report")
        st.write("Produces a structured, publication-quality PDF summary including metrics, budgets, and transactions.")

        avail_months = get_available_months()
        if not avail_months:
            st.info("No transaction records available to generate a PDF report.")
            return

        pdf_month = st.selectbox("Select Reporting Month for PDF", avail_months, key="pdf_m")

        # Gather summary & details
        summary = get_monthly_summary(pdf_month)
        budgets = get_budget_status(pdf_month)
        tx_df = get_all_transactions(month=pdf_month)
        tx_list = tx_df.to_dict(orient="records")

        # Report preview metrics
        p1, p2, p3 = st.columns(3)
        with p1:
            st.metric("Total Income", format_currency(summary["income"]))
        with p2:
            st.metric("Total Expenses", format_currency(summary["expense"]))
        with p3:
            st.metric("Net Savings", format_currency(summary["net_savings"]))

        # Generate PDF bytes
        try:
            pdf_bytes = generate_monthly_pdf_report(
                month=pdf_month,
                summary=summary,
                transactions=tx_list,
                budgets=budgets,
            )

            pdf_filename = f"Expense_Report_{pdf_month}.pdf"

            st.download_button(
                label=f"⬇️ Download {pdf_month} PDF Financial Report",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
            st.success(f"PDF Report for {pdf_month} ready for download ({len(pdf_bytes):,} bytes).")
        except Exception as e:
            st.error(f"Failed to generate PDF report: {e}")

