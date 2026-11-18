"""
Export Service: Handles CSV data generation and ReportLab PDF monthly financial report generation.
"""

import io
from typing import Dict, Any, List, Optional
import pandas as pd
from reportlab.lib import colors  # pyrefly: ignore[untyped-import]
from reportlab.lib.pagesizes import letter  # pyrefly: ignore[untyped-import]
from reportlab.lib.units import inch  # pyrefly: ignore[untyped-import]
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # pyrefly: ignore[untyped-import]
from reportlab.platypus import (  # pyrefly: ignore[untyped-import]
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def export_transactions_to_csv(df: pd.DataFrame) -> bytes:
    """Convert transaction DataFrame to CSV bytes."""
    output = io.BytesIO()
    # Ensure standard column naming
    export_df = df.copy()
    export_df.to_csv(output, index=False, encoding="utf-8")
    return output.getvalue()


def generate_monthly_pdf_report(
    month: str,
    summary: Dict[str, Any],
    transactions: List[Any],
    budgets: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """
    Generate a beautifully styled PDF report for a selected month using ReportLab.
    Includes:
      - Header and Report Metadata
      - Key Financial Metrics (Income, Expense, Net Savings, Savings Rate)
      - Category-wise Spending Breakdown
      - Budget Adherence & Alerts Summary
      - Recent Transactions for the Month
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Get currency code for PDF formatting
    try:
        from services.settings_service import get_active_currency
        curr_code = get_active_currency().get("code", "USD")
    except Exception:
        curr_code = "USD"

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E293B"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    elements: List[Any] = []

    # Title & Subtitle
    elements.append(Paragraph("Personal Expense Tracker", title_style))
    elements.append(Paragraph(f"Monthly Financial Summary Report &bull; Period: {month}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=0, spaceAfter=14))

    # 1. Executive Summary Table
    income = summary.get("income", 0.0)
    expense = summary.get("expense", 0.0)
    savings = summary.get("net_savings", 0.0)
    savings_rate = summary.get("savings_rate", 0.0)

    summary_data = [
        [
            Paragraph("<b>Total Income</b>", body_style),
            Paragraph(f"{curr_code} {income:,.2f}", body_bold),
            Paragraph("<b>Total Expenses</b>", body_style),
            Paragraph(f"{curr_code} {expense:,.2f}", body_bold),
        ],
        [
            Paragraph("<b>Net Savings</b>", body_style),
            Paragraph(f"{curr_code} {savings:,.2f}", body_bold),
            Paragraph("<b>Savings Rate</b>", body_style),
            Paragraph(f"{savings_rate:.1f}%", body_bold),
        ],
        [
            Paragraph("<b>Top Expense Category</b>", body_style),
            Paragraph(f"{summary.get('top_category', 'N/A')} ({curr_code} {summary.get('top_category_amount', 0):,.2f})", body_style),
            Paragraph("<b>Peak Spending Day</b>", body_style),
            Paragraph(f"{summary.get('peak_spending_day', 'N/A')} ({curr_code} {summary.get('peak_spending_amount', 0):,.2f})", body_style),
        ],
    ]

    t_summary = Table(summary_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 14))

    # 2. Category Spending Breakdown Table
    cat_breakdown = summary.get("category_breakdown", [])
    if cat_breakdown:
        elements.append(Paragraph("Expense Breakdown by Category", section_style))
        cat_table_data = [
            [
                Paragraph("<b>Category</b>", body_bold),
                Paragraph("<b>Transactions</b>", body_bold),
                Paragraph("<b>Total Spent</b>", body_bold),
                Paragraph("<b>% of Expenses</b>", body_bold),
            ]
        ]
        for row in cat_breakdown:
            cat_tot = float(row.get("total", 0.0))
            pct = (cat_tot / expense * 100.0) if expense > 0 else 0.0
            cat_table_data.append([
                Paragraph(str(row.get("category", "")), body_style),
                Paragraph(str(row.get("count", "")), body_style),
                Paragraph(f"{curr_code} {cat_tot:,.2f}", body_style),
                Paragraph(f"{pct:.1f}%", body_style),
            ])

        t_cats = Table(cat_table_data, colWidths=[2.6 * inch, 1.4 * inch, 1.6 * inch, 1.6 * inch])
        t_cats.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_cats)
        elements.append(Spacer(1, 14))

    # 3. Budget Status Table (if budgets exist for month)
    if budgets:
        elements.append(Paragraph("Budget Performance & Limits", section_style))
        b_table_data = [
            [
                Paragraph("<b>Category</b>", body_bold),
                Paragraph("<b>Budget Limit</b>", body_bold),
                Paragraph("<b>Actual Spent</b>", body_bold),
                Paragraph("<b>Remaining</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]
        ]
        for b in budgets:
            status_text = b.get("alert_level", "SAFE")
            b_color = "#16A34A" if status_text == "SAFE" else ("#DC2626" if status_text == "EXCEEDED" else "#D97706")
            status_para = Paragraph(f"<font color='{b_color}'><b>{status_text} ({b.get('percentage', 0):.1f}%)</b></font>", body_style)

            b_table_data.append([
                Paragraph(str(b.get("category", "")), body_style),
                Paragraph(f"{curr_code} {float(b.get('budget', 0)):,.2f}", body_style),
                Paragraph(f"{curr_code} {float(b.get('spent', 0)):,.2f}", body_style),
                Paragraph(f"{curr_code} {float(b.get('remaining', 0)):,.2f}", body_style),
                status_para,
            ])

        t_budgets = Table(b_table_data, colWidths=[2.0 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch])
        t_budgets.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_budgets)
        elements.append(Spacer(1, 14))

    # 4. Itemized Transaction Log (Up to 30 items for neat presentation)
    if transactions:
        elements.append(Paragraph(f"Transactions for {month} (Recent {min(len(transactions), 30)} of {len(transactions)})", section_style))
        tx_table_data = [
            [
                Paragraph("<b>Date</b>", body_bold),
                Paragraph("<b>Type</b>", body_bold),
                Paragraph("<b>Category</b>", body_bold),
                Paragraph("<b>Payment Method</b>", body_bold),
                Paragraph("<b>Amount</b>", body_bold),
            ]
        ]
        for tx in transactions[:30]:
            t_type = str(tx.get("type", "")).capitalize()
            type_color = "#16A34A" if t_type.lower() == "income" else "#DC2626"
            type_para = Paragraph(f"<font color='{type_color}'><b>{t_type}</b></font>", body_style)

            tx_table_data.append([
                Paragraph(str(tx.get("date", "")), body_style),
                type_para,
                Paragraph(str(tx.get("category", "")), body_style),
                Paragraph(str(tx.get("payment_method", "")), body_style),
                Paragraph(f"{curr_code} {float(tx.get('amount', 0)):,.2f}", body_style),
            ])

        t_tx = Table(tx_table_data, colWidths=[1.1 * inch, 1.0 * inch, 2.3 * inch, 1.5 * inch, 1.3 * inch])
        t_tx.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_tx)

    # Footer note
    elements.append(Spacer(1, 15))
    footer_text = "Generated automatically by Personal Expense Tracker &bull; Confidential Personal Financial Record"
    elements.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=subtitle_style, alignment=1)))

    doc.build(elements)
    return buffer.getvalue()

