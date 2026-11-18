"""
Smart Khata & Notes View: Quick natural-language hisaab notes with instant
math parsing (+ and -) and permanent monthly diary archiving.
"""

from datetime import date
import streamlit as st
import pandas as pd
from services.khata_service import (
    parse_hisaab_text,
    save_khata_note,
    get_all_khata_notes,
    delete_khata_note,
    update_khata_note,
)
from services.settings_service import get_active_currency
from services.transaction_service import add_transaction
from utils.formatters import format_currency


SAMPLE_NOTE_EXAMPLES = [
    "200 Chicken + 500 Cash = 700",
    "200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii",
    """50000 Salary
+ 1500 Freelance
- 12000 House Rent
- 3500 Electricity Bill
- 1200 Internet
- 8000 Groceries / Rashan""",
]


def render_khata():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]

    st.title("📝 Smart Khata & Notes (روزانہ حساب کتاب)")
    st.caption(
        "Natural text mein hisaab likhein (jaise: `200 Chicken + 500 Cash - 100`) — "
        "yeh khud exact math calculate karega aur hamesha ke liye monthly diary mein save rakhega."
    )

    tab_pad, tab_archive = st.tabs(["✍️ New Hisaab Note", "📚 Saved Monthly Notes (ڈائری)"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: Smart Note Pad & Calculator
    # ─────────────────────────────────────────────────────────────────────────
    with tab_pad:
        col_input, col_preview = st.columns([3, 2])

        with col_input:
            st.subheader("Hisaab Note Pad")

            # Quick helper templates
            sample_pick = st.selectbox(
                "💡 Quick Example / Sample Format:",
                options=["-- Write My Own --"] + SAMPLE_NOTE_EXAMPLES,
            )

            default_text = "" if sample_pick == "-- Write My Own --" else sample_pick

            note_title = st.text_input(
                "Note Title *",
                value="Daily Hisaab" if not default_text else "Kitchen & Market Expenses",
                placeholder="e.g. Rashan Khata, Grocery List, Daily Office Lunch",
            )

            note_date = st.date_input("Date", value=date.today())

            note_body = st.text_area(
                "Enter Your Hisaab / Notes (+ aur - use karein) *",
                value=default_text,
                height=160,
                placeholder="Example:\n200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii\n\nOr line-by-line:\n+ 500 doodh\n- 50 discount",
            )

            # Live calculation
            calc = parse_hisaab_text(note_body)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                save_btn = st.button("💾 Save to Monthly Notes", type="primary", use_container_width=True)
            with col_btn2:
                push_to_trans = st.button("📥 Add Items as Transactions", use_container_width=True)

            if save_btn:
                if not note_body.strip():
                    st.error("Please enter some hisaab or notes before saving.")
                elif calc["item_count"] == 0:
                    st.warning("No numbers/amounts detected to calculate. Please include amounts like `200 Chicken`.")
                else:
                    saved = save_khata_note(
                        title=note_title,
                        raw_text=note_body,
                        date_str=note_date.isoformat(),
                    )
                    st.success(
                        f"✅ Note **'{saved['title']}'** saved permanently! Total: **{format_currency(saved['calculated_total'])}**"
                    )
                    st.rerun()

            if push_to_trans:
                if calc["item_count"] == 0:
                    st.error("No items found to convert.")
                else:
                    count_added = 0
                    for itm in calc["items"]:
                        t_type = "income" if itm["sign"] > 0 else "expense"
                        t_category = "Khata Income" if itm["sign"] > 0 else "Khata Expense"
                        add_transaction(
                            trans_type=t_type,
                            amount=float(itm["amount"]),
                            category=t_category,
                            payment_method="Cash",
                            date_str=note_date.isoformat(),
                            description=f"[Khata] {itm['label']}",
                        )
                        count_added += 1
                    st.success(f"🎉 Successfully converted {count_added} item(s) into real transactions!")
                    st.rerun()

        with col_preview:
            st.subheader("📊 Live Math Breakdown")

            p1, p2 = st.columns(2)
            with p1:
                st.metric("Total Added (+)", format_currency(calc["total_additions"]))
            with p2:
                st.metric("Total Deducted (-)", format_currency(calc["total_deductions"]))

            st.metric(
                "Net Total",
                format_currency(calc["net_total"]),
                delta=f"{calc['item_count']} item(s) parsed",
            )

            if calc["items"]:
                st.write("**Extracted Item Details:**")
                disp_rows = [
                    {
                        "Item / Label": itm["label"],
                        "Action": "➕ Add" if itm["type"] == "add" else "➖ Deduct",
                        f"Amount ({sym})": format_currency(itm["amount"]),
                    }
                    for itm in calc["items"]
                ]
                st.dataframe(pd.DataFrame(disp_rows), hide_index=True, use_container_width=True)
            else:
                st.info("Start typing above to see real-time calculation and itemized breakdown.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: Saved Monthly Notes Archive
    # ─────────────────────────────────────────────────────────────────────────
    with tab_archive:
        st.subheader("📚 Saved Monthly Hisaab Notes")
        st.caption("Aapke tamam hisaab notes yahan permanently mehfooz rehte hain.")

        # Filters
        c_filter1, c_filter2 = st.columns(2)
        with c_filter1:
            all_saved = get_all_khata_notes()
            unique_months = sorted(list(set(n["month"] for n in all_saved)), reverse=True)
            month_choice = st.selectbox("Select Month", ["All Months"] + unique_months)
        with c_filter2:
            search_kw = st.text_input("🔍 Search Notes", placeholder="Search title or text...")

        filtered_notes = get_all_khata_notes(month=month_choice, search_query=search_kw)

        st.write(f"Showing **{len(filtered_notes)}** saved hisaab note(s)")

        if not filtered_notes:
            st.info("No saved notes found for this filter. Create and save your first hisaab note in the first tab!")
            return

        # Overall sum of displayed notes
        notes_grand_total = sum(float(n["calculated_total"]) for n in filtered_notes)
        st.metric("Total Sum of Filtered Notes", format_currency(notes_grand_total))
        st.markdown("---")

        # Delete confirmation state
        if "confirm_delete_note_id" not in st.session_state:
            st.session_state.confirm_delete_note_id = None

        if st.session_state.confirm_delete_note_id is not None:
            del_nid = st.session_state.confirm_delete_note_id
            st.error(f"⚠️ Confirm permanently deleting Note #{del_nid}?")
            cd1, cd2, _ = st.columns([1, 1, 4])
            with cd1:
                if st.button("Yes, Delete Note", type="primary"):
                    delete_khata_note(del_nid)
                    st.session_state.confirm_delete_note_id = None
                    st.success("Note deleted.")
                    st.rerun()
            with cd2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_note_id = None
                    st.rerun()
            st.markdown("---")

        for note in filtered_notes:
            with st.container():
                c_title, c_date, c_total, c_del = st.columns([4, 2, 3, 1])
                with c_title:
                    st.markdown(f"### 📋 {note['title']}")
                with c_date:
                    st.caption(f"📅 **{note['date']}**")
                with c_total:
                    st.markdown(f"**Total:** `{format_currency(note['calculated_total'])}`")
                with c_del:
                    if st.button("🗑️", key=f"del_note_{note['id']}", use_container_width=True):
                        st.session_state.confirm_delete_note_id = note["id"]
                        st.rerun()

                # Raw Text & Item Breakdown inside expander
                with st.expander("🔍 View Full Note & Breakdown"):
                    st.text_area("Original Hisaab Text:", value=note["raw_text"], disabled=True, height=100)
                    if note.get("items"):
                        disp_items = [
                            {
                                "Item / Label": itm["label"],
                                "Action": "➕ Add" if itm["type"] == "add" else "➖ Deduct",
                                f"Amount ({sym})": format_currency(itm["amount"]),
                            }
                            for itm in note["items"]
                        ]
                        st.dataframe(pd.DataFrame(disp_items), hide_index=True, use_container_width=True)

                st.markdown("---")
