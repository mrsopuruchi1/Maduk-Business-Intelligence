import streamlit as st
from modules.signup_module import render_signup_module
from modules.login_module import render_login_module


def render_signup_and_login_page():

    # ----------------------------
    # GLOBAL STYLING
    # ----------------------------
    st.markdown("""
    <style>
    body {
        background-color: #0e1117;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: 600;
    }
    input {
        border-radius: 6px !important;
    }
    .small-text {
        color: gray;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # SESSION STATE INIT
    # ----------------------------
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"

    if "user_token" not in st.session_state:
        st.session_state.user_token = None

    # ✅ FIX 1: SYNC TOKEN (important)
    if "token" in st.session_state and not st.session_state.user_token:
        st.session_state.user_token = st.session_state["user_token"]

    # ----------------------------
    # AUTO LOGIN
    # ----------------------------
    if st.session_state.get("remember_me") and st.session_state.user_token:
        st.success("🔐 Welcome back! You are already logged in.")
        st.session_state.auth_view = "dashboard"
        st.rerun()

    # ----------------------------
    # BLOCK ACCESS IF LOGGED IN
    # ----------------------------
    if st.session_state.user_token:
        st.session_state.auth_view = "dashboard"
        st.rerun()

    # ----------------------------
    # HEADER
    # ----------------------------
    st.markdown("""
    <div style="text-align:center; margin-bottom:25px;">
        <h1 style="margin-bottom:5px;">Maduk Business Intelligence</h1>
        <p class="small-text">Your AI Business Consultant</p>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # TAB SWITCH
    # ----------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.auth_view = "login"
            st.rerun()

    with col2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.auth_view = "signup"
            st.rerun()

    st.markdown("---")

    # ----------------------------
    # PAGE RENDERING
    # ----------------------------
    if st.session_state.auth_view == "login":
        render_login_module()

    elif st.session_state.auth_view == "signup":
        render_signup_module()

    elif st.session_state.auth_view == "dashboard":
        st.success("🎉 Redirecting to Dashboard...")
        st.info("This is where your main app loads.")