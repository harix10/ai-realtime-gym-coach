import streamlit as st
from services.persistence.exercise_repository import get_or_create_user

def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 0.5rem; margin-top: 1rem;">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.4 14.4 9.6 9.6"/>
                <path d="M18.65 21.35a2 2 0 0 1-2.83 0l-7.17-7.18a2 2 0 0 1 0-2.83l.53-.53"/>
                <path d="M21.5 18.5a2 2 0 0 1-2.83 0l-3.54-3.54a2 2 0 0 1 0-2.83l.54-.53"/>
                <path d="M5.35 2.65a2 2 0 0 1 2.83 0l7.17 7.18a2 2 0 0 1 0 2.83l-.53.53"/>
                <path d="M2.5 5.5a2 2 0 0 1 2.83 0l3.54 3.54a2 2 0 0 1 0 2.83l-.54.53"/>
            </svg>
            <h1 style="margin: 0; padding: 0; font-weight: 800; font-size: 2.4rem; letter-spacing: -1px;">AI Real-time GYM Trainer</h1>
        </div>
        <h3 style='color: #94a3b8; font-weight: 400; margin-bottom: 2rem; margin-top: 0;'>Welcome! Please enter a username to start.</h3>
        """,
        unsafe_allow_html=True
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Name (unique)", placeholder="e.g john doe")
        submit_button = st.form_submit_button("Start Session", width="stretch")

    if submit_button:
        if not username:
            st.error("Name cannot be empty.")
            return False

        user = get_or_create_user(username)

        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]

        st.rerun()
            

    return False
