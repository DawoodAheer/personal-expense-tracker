"""
Financial Goals View: Set savings targets, track progress with visual bars,
add contributions, and celebrate when goals are achieved!
"""

from datetime import date
import streamlit as st
import plotly.graph_objects as go
from services.goals_service import (
    add_goal,
    get_all_goals,
    update_goal_savings,
    add_to_goal_savings,
    delete_goal,
    reset_goal,
)
from services.settings_service import get_active_currency
from utils.formatters import format_currency

GOAL_CATEGORIES = [
    "Emergency Fund",
    "Vacation / Travel",
    "Home Purchase",
    "Car / Vehicle",
    "Education / Studies",
    "Wedding",
    "Medical",
    "Electronics / Gadgets",
    "Business Investment",
    "Retirement",
    "Hajj / Umrah",
    "General Savings",
    "Other",
]

STATUS_CONFIG = {
    "ACHIEVED":    {"icon": "🏆", "color": "#10B981", "bg": "#ECFDF5", "label": "Achieved!"},
    "OVERDUE":     {"icon": "🚨", "color": "#EF4444", "bg": "#FEF2F2", "label": "Overdue"},
    "URGENT":      {"icon": "⚠️",  "color": "#F59E0B", "bg": "#FFFBEB", "label": "Urgent"},
    "IN_PROGRESS": {"icon": "🎯", "color": "#3B82F6", "bg": "#EFF6FF", "label": "In Progress"},
}


def _progress_color(pct: float, status: str) -> str:
    if status == "ACHIEVED":
        return "#10B981"
    if pct >= 80:
        return "#F59E0B"
    return "#3B82F6"


def render_goals():
    active_curr = get_active_currency()
    sym = active_curr["symbol"]
    st.title("🎯 Financial Goals")
    st.caption("Set savings targets, track your progress, and hit every milestone.")

    goals = get_all_goals()

    # ── Summary strip ────────────────────────────────────────────────────────
    if goals:
        total_target = sum(g["target_amount"] for g in goals)
        total_saved  = sum(g["saved_amount"] for g in goals)
        achieved     = sum(1 for g in goals if g["status"] == "ACHIEVED")
        in_prog      = sum(1 for g in goals if g["status"] == "IN_PROGRESS")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Goals", len(goals))
        with m2:
            st.metric("🏆 Achieved", achieved)
        with m3:
            st.metric("🎯 In Progress", in_prog)
        with m4:
            overall_pct = (total_saved / total_target * 100) if total_target > 0 else 0
            st.metric("Overall Progress", f"{overall_pct:.1f}%",
                      delta=f"{format_currency(total_saved)} / {format_currency(total_target)}")

        st.markdown("---")

    # ── Add New Goal Form ────────────────────────────────────────────────────
    with st.expander("➕ Create New Financial Goal", expanded=(len(goals) == 0)):
        with st.form("add_goal_form", clear_on_submit=True):
            g1, g2 = st.columns(2)
            with g1:
                g_name = st.text_input("Goal Name *", placeholder="e.g. Emergency Fund, Europe Trip")
                g_category = st.selectbox("Category", GOAL_CATEGORIES)
                g_target = st.number_input(
                    f"Target Amount ({sym}) *",
                    min_value=1.0, max_value=1_000_000_000.0,
                    step=1000.0, format="%.2f",
                )
            with g2:
                g_deadline = st.date_input("Target Deadline (Optional)", value=None)
                g_initial = st.number_input(
                    f"Initial Savings ({sym}) Already Saved",
                    min_value=0.0, max_value=1_000_000_000.0,
                    step=100.0, format="%.2f",
                    help="If you've already saved some amount towards this goal, enter it here.",
                )
                g_desc = st.text_area("Notes (Optional)", placeholder="Why is this goal important to you?", height=80)

            submitted = st.form_submit_button("🎯 Create Goal", type="primary", use_container_width=True)
            if submitted:
                if not g_name.strip():
                    st.error("Please enter a goal name.")
                elif g_target <= 0:
                    st.error("Please enter a target amount greater than 0.")
                elif g_initial > g_target:
                    st.error("Initial savings cannot exceed the target amount.")
                else:
                    try:
                        new_goal = add_goal(
                            name=g_name,
                            target_amount=g_target,
                            category=g_category,
                            deadline=g_deadline.isoformat() if g_deadline else None,
                            description=g_desc,
                        )
                        # Set initial savings if provided
                        if g_initial > 0:
                            update_goal_savings(new_goal["id"], g_initial)
                        st.success(f"✅ Goal **{g_name}** created! Target: {format_currency(g_target)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating goal: {e}")

    # ── Session state for action dialogs ────────────────────────────────────
    if "goal_contribute_id" not in st.session_state:
        st.session_state.goal_contribute_id = None
    if "goal_delete_id" not in st.session_state:
        st.session_state.goal_delete_id = None

    if not goals:
        st.info("No goals yet! Create your first financial goal above to start tracking your savings journey. 🚀")
        return

    # ── Contribution Dialog ──────────────────────────────────────────────────
    if st.session_state.goal_contribute_id is not None:
        g_id = st.session_state.goal_contribute_id
        # Find goal from list
        g_obj = next((g for g in goals if g["id"] == g_id), None)
        if g_obj:
            st.markdown(f"### 💰 Add Savings to: **{g_obj['name']}**")
            remaining = g_obj["remaining"]
            with st.form("contribute_form"):
                contrib_col1, contrib_col2 = st.columns(2)
                with contrib_col1:
                    contrib_amount = st.number_input(
                        f"Amount to Add ({sym})",
                        min_value=0.01,
                        max_value=float(max(remaining, 0.01)),
                        step=100.0, format="%.2f",
                    )
                with contrib_col2:
                    st.metric("Still Needed", format_currency(remaining))
                c1, c2 = st.columns(2)
                with c1:
                    save_c = st.form_submit_button("💰 Add Savings", type="primary", use_container_width=True)
                with c2:
                    cancel_c = st.form_submit_button("Cancel", use_container_width=True)

                if save_c:
                    add_to_goal_savings(g_id, contrib_amount)
                    st.session_state.goal_contribute_id = None
                    st.success(f"Added {format_currency(contrib_amount)} to '{g_obj['name']}'!")
                    st.rerun()
                if cancel_c:
                    st.session_state.goal_contribute_id = None
                    st.rerun()
            st.markdown("---")

    # ── Delete Confirmation ──────────────────────────────────────────────────
    if st.session_state.goal_delete_id is not None:
        g_id = st.session_state.goal_delete_id
        g_obj = next((g for g in goals if g["id"] == g_id), None)
        if g_obj:
            st.error(f"⚠️ Permanently delete goal **{g_obj['name']}**?")
            d1, d2, _ = st.columns([1, 1, 4])
            with d1:
                if st.button("Yes, Delete", type="primary"):
                    delete_goal(g_id)
                    st.session_state.goal_delete_id = None
                    st.success("Goal deleted.")
                    st.rerun()
            with d2:
                if st.button("Cancel"):
                    st.session_state.goal_delete_id = None
                    st.rerun()
            st.markdown("---")

    # ── Goals Grid ───────────────────────────────────────────────────────────
    # Separate active vs achieved
    active_goals    = [g for g in goals if g["status"] != "ACHIEVED"]
    achieved_goals  = [g for g in goals if g["status"] == "ACHIEVED"]

    if active_goals:
        st.subheader("🎯 Active Goals")
        _render_goal_cards(active_goals, sym)

    if achieved_goals:
        with st.expander(f"🏆 Achieved Goals ({len(achieved_goals)})", expanded=False):
            _render_goal_cards(achieved_goals, sym)


def _render_goal_cards(goals_list: list, sym: str) -> None:
    """Render goal cards in a 2-column grid layout."""
    # 2 columns grid
    for i in range(0, len(goals_list), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(goals_list):
                break
            g = goals_list[i + j]
            cfg = STATUS_CONFIG.get(g["status"], STATUS_CONFIG["IN_PROGRESS"])
            pct = g["percentage"]
            bar_color = _progress_color(pct, g["status"])

            with col:
                # Card container with colored border
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid {cfg['color']};
                        border-radius: 12px;
                        padding: 16px 18px;
                        background: {cfg['bg']};
                        margin-bottom: 4px;
                    ">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:18px; font-weight:700; color:#0F172A;">{cfg['icon']} {g['name']}</span>
                            <span style="font-size:12px; background:{cfg['color']}22; color:{cfg['color']};
                                padding:3px 10px; border-radius:20px; font-weight:600;">{cfg['label']}</span>
                        </div>
                        <div style="color:#64748B; font-size:12px; margin-top:4px;">
                            📂 {g['category']}
                            {"&nbsp;&nbsp;📅 " + str(g['deadline']) if g.get('deadline') else ""}
                            {"&nbsp;&nbsp;⏳ " + str(g['days_left']) + " days left" if g.get('days_left') is not None and g['status'] != 'ACHIEVED' else ""}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Gauge chart for progress
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 26}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1},
                        "bar": {"color": bar_color, "thickness": 0.3},
                        "bgcolor": "#F1F5F9",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0, 80],  "color": "#F1F5F9"},
                            {"range": [80, 100], "color": "#FEF3C7"},
                        ],
                        "threshold": {
                            "line": {"color": "#10B981", "width": 3},
                            "thickness": 0.75,
                            "value": 100,
                        },
                    },
                ))
                fig.update_layout(
                    height=180,
                    margin=dict(l=15, r=15, t=10, b=5),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#0F172A"},
                )
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{g['id']}")

                # Amounts row
                a1, a2, a3 = st.columns(3)
                with a1:
                    st.caption(f"**Target**\n{format_currency(g['target_amount'])}")
                with a2:
                    st.caption(f"**Saved**\n{format_currency(g['saved_amount'])}")
                with a3:
                    st.caption(f"**Left**\n{format_currency(g['remaining'])}")

                if g.get("description"):
                    st.caption(f"📝 {g['description']}")

                # Action buttons
                btn1, btn2, btn3 = st.columns(3)
                with btn1:
                    if g["status"] != "ACHIEVED":
                        if st.button("💰 Add", key=f"contrib_{g['id']}", use_container_width=True):
                            st.session_state.goal_contribute_id = g["id"]
                            st.rerun()
                    else:
                        if st.button("🔄 Reset", key=f"reset_{g['id']}", use_container_width=True):
                            reset_goal(g["id"])
                            st.rerun()
                with btn2:
                    if st.button("🗑️ Delete", key=f"del_g_{g['id']}", use_container_width=True):
                        st.session_state.goal_delete_id = g["id"]
                        st.rerun()
                with btn3:
                    if g["status"] == "ACHIEVED":
                        st.markdown("🎉 **Done!**")
                    elif pct >= 80:
                        st.markdown("🔥 **Almost!**")
                    else:
                        st.markdown(f"💪 {pct:.0f}%")

                st.markdown("---")

