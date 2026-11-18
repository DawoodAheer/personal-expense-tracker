"""
Settings View: Configure country currency, formatting preferences,
and reset database to start clean from zero (0).
"""

import streamlit as st
from services.settings_service import (
    WORLD_CURRENCIES,
    get_active_currency,
    set_active_currency,
    reset_app_data_to_zero,
    get_theme,
    set_theme,
)
from utils.formatters import format_currency


def render_settings():
    st.title("⚙️ Settings & Currency")
    st.caption("Customize your country's currency, display formats, and manage your data.")

    active = get_active_currency()

    # --- 1. Currency Configuration ---
    st.subheader("🌍 Country Currency & Symbol")
    st.write("Select the currency for your country or define a custom currency symbol.")

    curr_options = [f"{c['country']} - {c['name']} ({c['code']} {c['symbol']})" for c in WORLD_CURRENCIES]
    
    # Find current index
    default_idx = 0
    for i, c in enumerate(WORLD_CURRENCIES):
        if c["code"] == active["code"]:
            default_idx = i
            break

    selected_option = st.selectbox(
        "Choose Your Currency",
        options=curr_options,
        index=default_idx,
        help="Select any country's currency. All dashboard cards, budgets, transactions, and reports will update automatically.",
    )

    selected_currency_data = WORLD_CURRENCIES[curr_options.index(selected_option)]

    with st.form("currency_settings_form"):
        col1, col2, col3 = st.columns(3)
        c_code: str = str(selected_currency_data["code"])
        c_symbol: str = str(selected_currency_data["symbol"])
        c_name: str = str(selected_currency_data["name"])

        if selected_currency_data["code"] == "CUSTOM":
            with col1:
                c_code = (st.text_input("Currency Code", value=active.get("code", "CST")) or "CST").strip().upper()
            with col2:
                c_symbol = (st.text_input("Currency Symbol", value=active.get("symbol", "¤")) or "¤").strip()
            with col3:
                c_name = (st.text_input("Currency Name", value=active.get("name", "Custom Currency")) or "Custom Currency").strip()
        else:
            with col1:
                st.text_input("Currency Code", value=selected_currency_data["code"], disabled=True)
            with col2:
                c_symbol = (st.text_input("Currency Symbol", value=selected_currency_data["symbol"]) or selected_currency_data["symbol"]).strip()
            with col3:
                st.text_input("Currency Name", value=selected_currency_data["name"], disabled=True)

        col_pos, col_prev = st.columns(2)
        with col_pos:
            c_pos = st.radio(
                "Symbol Position",
                options=["prefix", "suffix"],
                index=0 if active.get("position", "prefix") == "prefix" else 1,
                format_func=lambda x: f"Prefix ({c_symbol} 1,000.00)" if x == "prefix" else f"Suffix (1,000.00 {c_symbol})",
                horizontal=True,
            )

        with col_prev:
            preview_val = format_currency(12500.50, currency_symbol=c_symbol, position=c_pos)
            st.metric("Live Format Preview", preview_val)

        save_curr_btn = st.form_submit_button("💾 Save Currency Settings", type="primary", use_container_width=True)

        if save_curr_btn:
            set_active_currency(
                code=c_code,
                symbol=c_symbol,
                name=c_name,
                position=c_pos,
            )
            st.success(f"Currency updated to {c_name} ({c_symbol}) successfully!")
            st.rerun()

    st.markdown("---")

    # --- 2. Appearance & Theme ---
    st.subheader("🎨 Appearance & Theme")
    current_theme = get_theme()
    theme_choice = st.radio(
        "Interface Mode",
        options=["☀️ Light Mode", "🌙 Dark Mode"],
        index=0 if current_theme == "light" else 1,
        horizontal=True,
    )
    new_theme = "light" if "Light" in theme_choice else "dark"
    if new_theme != current_theme:
        set_theme(new_theme)
        st.session_state["app_theme"] = new_theme
        st.rerun()

    st.markdown("---")

    # --- 3. Clean Database Start From Zero (0 سے شروع) ---
    st.subheader("🧹 Database Reset (Start Fresh from 0)")
    st.write("Reset all transactions and budgets to 0 so you can track your real daily personal income and expenses.")

    if "confirm_reset_zero" not in st.session_state:
        st.session_state.confirm_reset_zero = False

    if not st.session_state.confirm_reset_zero:
        if st.button("🗑️ Reset All Data to Zero (0)", type="secondary"):
            st.session_state.confirm_reset_zero = True
            st.rerun()
    else:
        st.error(
            "⚠️ **Are you sure?** This will permanently delete all recorded transactions and budgets so your account starts at 0 balance. (Your currency settings will be preserved)."
        )
        col_y, col_n, _ = st.columns([1, 1, 3])
        with col_y:
            if st.button("Yes, Reset to 0", type="primary"):
                reset_app_data_to_zero()
                st.session_state.confirm_reset_zero = False
                st.success("All data has been reset to 0! You now have a clean slate.")
                st.rerun()
        with col_n:
            if st.button("Cancel"):
                st.session_state.confirm_reset_zero = False
                st.rerun()

    st.markdown("---")

    # --- 3. Optional Demo Seeder ---
    st.subheader("🎲 Demo Data Option")
    st.caption("If you ever want to preview how the dashboard and charts look with sample numbers:")
    if st.button("Load Sample Demo Data"):
        from seed_sample_data import seed_demo_data
        seed_demo_data()
        st.success("Sample transactions and budgets populated!")
        st.rerun()
