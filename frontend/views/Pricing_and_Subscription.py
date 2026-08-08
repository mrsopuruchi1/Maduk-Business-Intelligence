import streamlit as st
from modules.subscription_module import render_subscription_module


def render_pricing_and_subscription_page():
    # ----------------------------
    # PAGE CONFIG (ONLY HERE)
    # ----------------------------
    

    # ----------------------------
    # GLOBAL REACT-STYLE LAYOUT
    # ----------------------------
    st.markdown("""
    <style>
    /* Page container */
    .main-container {
        max-width: 1200px;
        margin: auto;
        padding-top: 20px;
    }

    /* Header */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    /* Title */
    .page-title {
        font-size: 28px;
        font-weight: 600;
    }

    /* Subtext */
    .page-subtitle {
        color: #A0A0A0;
        font-size: 14px;
    }

    /* Divider spacing */
    .section {
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # AUTH GUARD (LIKE REACT PROTECTED ROUTE)
    # ----------------------------
    if "user_token" not in st.session_state:
        st.warning("🔒 Please login to access subscriptions")
        st.stop()

    user_token = st.session_state.user_token

    # ----------------------------
    # TOP RIGHT LOGOUT (React-style minimal)
    # ----------------------------
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    # ----------------------------
    # PAGE HEADER (REACT STYLE)
    # ----------------------------
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="page-header">
        <div>
            <div class="page-title"></div>
            <div class="page-subtitle">
                MANAGE YOUR PLAN, BILLING, AND UPGRADES
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # RENDER MODULE (LIKE COMPONENT)
    # ----------------------------
    render_subscription_module(user_token)

    # ----------------------------
    # FOOTER
    # ----------------------------
    

    