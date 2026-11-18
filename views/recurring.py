"""
Recurring Transactions View: Set up automatic monthly/weekly repeating entries
like rent, salary, utility bills, subscriptions, etc.
"""

from datetime import date
import streamlit as st
from services.recurring_service import (
    add_recurring,
    get_all_recurring,
    toggle_recurring_active,
    delete_recurring,
)
from services.settings_service import get_active_currency
from database.queries import DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES, DEFAULT_PAYMENT_METHODS
from utils.formatters import format_currency

RECURRENCE_OPTIONS = {
    "monthly": "📅 Monthly",
    "weekly":  "📆 Weekly",
    "daily":   "🗓️ Daily",
}

COMMON_RECURRING_EXAMPLES = [
    "Rent / House Rent",
    "Monthly Salary",
    "Electricity Bill",
    "Gas Bill",
    "Internet Bill",
    "Mobile Bill",
    "Water Bill",
    "Gym Membership",
    "Netflix / Streaming",
    "School / Tuition Fee",
    "Car Installment",
    "Insurance Premium",
    "Loan EMI",
    "Savings Transfer",
]


def render_recurring():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]

    st.title("🔁 Recurring Transactions")
    st.caption(
        "Set up repeating income or expenses that auto-record on their due dates. "
        "No more forgetting monthly entries!"
    )

    all_recurring = get_all_recurring()
    active_count = sum(1 for r in all_recurring if r["is_active"])
    paused_count = len(all_recurring) - active_count

    # Summary strip
    if all_recurring:
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Total Templates", len(all_recurring))
        with s2:
            st.metric("✅ Active", active_count)
        with s3:
            st.metric("⏸️ Paused", paused_count)
        st.markdown("---")

    # ── Add New Recurring Form ───────────────────────────────────────────────
    with st.expander("➕ Add New Recurring Transaction", expanded=(len(all_recurring) == 0)):
        with st.form("add_recurring_form", clear_on_submit=True):
            r1, r2 = st.columns(2)
            with r1:
                # Quick template picker
                template_pick = st.selectbox(
                    "Quick Template (or type custom below)",
                    options=["-- None --"] + COMMON_RECURRING_EXAMPLES,
                )
                r_name = st.text_input(
                    "Transaction Name *",
                    value="" if template_pick == "-- None --" else template_pick,
                    placeholder="e.g. Monthly Rent, Salary, Netflix",
                )
                r_type = st.radio("Type *", ["expense", "income"], horizontal=True,
                                  format_func=lambda x: "💸 Expense" if x == "expense" else "💵 Income")
                r_amount = st.number_input(
                    f"Amount ({sym}) *",
                    min_value=0.01, max_value=1_000_000_000.0,
                    step=100.0, format="%.2f",
                )

            with r2:
                all_cats = DEFAULT_EXPENSE_CATEGORIES if r_type == "expense" else DEFAULT_INCOME_CATEGORIES
                r_category = st.selectbox("Category *", all_cats)
                r_payment = st.selectbox("Payment Method *", DEFAULT_PAYMENT_METHODS)
                r_recurrence = st.selectbox(
                    "Repeats Every *",
                    options=list(RECURRENCE_OPTIONS.keys()),
                    format_func=lambda x: RECURRENCE_OPTIONS[x],
                )
                r_start = st.date_input("First Due Date *", value=date.today())
                r_desc = st.text_input(
                    "Notes (Optional)",
                    placeholder="e.g. House rent to landlord",
                )

            submitted = st.form_submit_button(
                "🔁 Create Recurring Entry", type="primary", use_container_width=True
            )
            if submitted:
                name_clean = r_name.strip()
                if not name_clean:
                    st.error("Please enter a transaction name.")
                elif r_amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    try:
                        add_recurring(
                            name=name_clean,
                            trans_type=r_type,
                            amount=r_amount,
                            category=r_category,
                            payment_method=r_payment,
                            recurrence=r_recurrence,
                            start_date=r_start.isoformat(),
                            description=r_desc,
                        )
                        st.success(
                            f"✅ **{name_clean}** set up! "
                            f"It will auto-record {format_currency(r_amount)} every "
                            f"{r_recurrence} starting {r_start}."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating recurring entry: {e}")

    if not all_recurring:
        st.info(
            "No recurring transactions yet! "
            "Add your monthly rent, salary, bills, and subscriptions above. "
            "They'll auto-record on their due dates every time you open the app. 🔄"
        )
        return

    # ── Active Recurring Table ───────────────────────────────────────────────
    st.subheader("📋 Your Recurring Transactions")

    # Delete confirmation state
    if "confirm_del_rec" not in st.session_state:
        st.session_state.confirm_del_rec = None

    if st.session_state.confirm_del_rec is not None:
        r_id = st.session_state.confirm_del_rec
        r_obj = next((r for r in all_recurring if r["id"] == r_id), None)
        if r_obj:
            st.error(f"⚠️ Delete recurring template **{r_obj['name']}**? Future auto-entries will stop.")
            cd1, cd2, _ = st.columns([1, 1, 4])
            with cd1:
                if st.button("Yes, Delete", type="primary"):
                    delete_recurring(r_id)
                    st.session_state.confirm_del_rec = None
                    st.success("Recurring entry deleted.")
                    st.rerun()
            with cd2:
                if st.button("Cancel"):
                    st.session_state.confirm_del_rec = None
                    st.rerun()
            st.markdown("---")

    # Group: active / paused
    for section_label, section_active in [("✅ Active", 1), ("⏸️ Paused", 0)]:
        section_items = [r for r in all_recurring if r["is_active"] == section_active]
        if not section_items:
            continue

        st.markdown(f"**{section_label}**")

        for item in section_items:
            type_icon = "💵" if item["type"] == "income" else "💸"
            recur_label = RECURRENCE_OPTIONS.get(item["recurrence"], item["recurrence"])

            with st.container():
                c_info, c_amount, c_next, c_btn1, c_btn2 = st.columns([3, 2, 2, 1, 1])
                with c_info:
                    st.markdown(f"{type_icon} **{item['name']}**")
                    st.caption(f"{item['category']} · {item['payment_method']}")
                with c_amount:
                    st.markdown(f"**{format_currency(float(item['amount']))}**")
                    st.caption(recur_label)
                with c_next:
                    next_due = item["next_due_date"]
                    try:
                        days = (date.fromisoformat(next_due) - date.today()).days
                        if days < 0:
                            due_label = f"⚠️ Overdue ({abs(days)}d ago)"
                        elif days == 0:
                            due_label = "📌 Due Today!"
                        elif days <= 7:
                            due_label = f"⏰ Due in {days}d"
                        else:
                            due_label = f"📅 {next_due}"
                    except ValueError:
                        due_label = next_due
                    st.markdown(due_label)
                with c_btn1:
                    pause_label = "▶️ Resume" if not item["is_active"] else "⏸️ Pause"
                    if st.button(pause_label, key=f"tog_{item['id']}", use_container_width=True):
                        toggle_recurring_active(item["id"])
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️", key=f"del_rec_{item['id']}", use_container_width=True):
                        st.session_state.confirm_del_rec = item["id"]
                        st.rerun()

                if item.get("description"):
                    st.caption(f"📝 {item['description']}")
                st.markdown("---")

    # ── Info box ────────────────────────────────────────────────────────────
    with st.expander("ℹ️ How Recurring Transactions Work"):
        st.markdown("""
        **How it works:**
        - Every time you open the app, it checks all active recurring templates.
        - If a template's **Next Due Date** is today or past, it **automatically creates** the transaction.
        - The Next Due Date then advances by the recurrence period (daily/weekly/monthly).
        - You can **Pause** any template to stop it temporarily without deleting it.
        - Transactions created this way appear in your normal transaction history with the **[Auto]** prefix.
        
        **Tips:**
        - Set salary as *monthly income* on your pay date.
        - Set rent as *monthly expense* on the 1st of each month.
        - Set Netflix/subscriptions as *monthly expense*.
        """)

