import streamlit as st
from PIL import Image

# ----------------------------
# CONFIG (ONLY HERE)
# ----------------------------
st.set_page_config(
    page_title="Maduk Business Intelligence",
    page_icon="frontend/assets/madukai_logo.png",
    layout="wide"
)

# ----------------------------
# IMPORT PAGES
# ----------------------------
from views.Signup_and_Login import render_signup_and_login_page
from views.Manage_Tenants import render_manage_tenants_page
from views.Pricing_and_Subscription import render_pricing_and_subscription_page
from views.Analyze_Your_Data import render_analyze_your_data_page 
from views.Predict_Your_Business import render_predict_your_business_page
from views.Get_Business_Recommendation import render_get_business_recommendation_page 
from views.About import render_about_page
from views.Terms import render_terms_page
from views.Privacy_Policy import render_privacy_policy_page

# ----------------------------
# GLOBAL STYLES
# ----------------------------
st.markdown("""
<style>

/* Fix sidebar background */
section[data-testid="stSidebar"] {
    background-color: #111827 !important;
}

/* Sidebar text color */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Remove blue highlight */
[data-testid="stSidebarNav"] {
    background-color: transparent !important;
}

/* Buttons inside sidebar */
section[data-testid="stSidebar"] .stButton>button {
    background-color: #1f2937;
    color: white;
    border: none;
}

section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #374151;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# SESSION STATE
# ----------------------------
if "route" not in st.session_state:
    st.session_state.route = "auth"

if "user_token" not in st.session_state:
    st.session_state.user_token = None

# ----------------------------
# SIDEBAR
# ----------------------------
logo = Image.open("frontend/assets/madukai_logo.png")

with st.sidebar:
    st.image(logo, use_container_width=True)
    st.markdown("## Maduk BI")
    st.markdown('<div class="subtle">AI Business Consultant</div>', unsafe_allow_html=True)
    st.divider()

    if not st.session_state.user_token:
        if st.button("🔐 Login / Signup", use_container_width=True):
            st.session_state.route = "auth"

    else:
        if st.button("🧑‍🤝‍🧑 Team Management", use_container_width=True):
            st.session_state.route = "manage"

        if st.button("💳 Pricing & Subscription", use_container_width=True):
            st.session_state.route = "pricing"

        if st.button("📊 Data Analytics & Insights", use_container_width=True):
            st.session_state.route = "analyze"

        if st.button("📈 Business Renenue Forecast", use_container_width=True):
            st.session_state.route = "predict"

        if st.button("🩺💡 Business Health Prediction & Advice", use_container_width=True):
                    st.session_state.route = "recommend"

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ----------------------------
# ROUTER
# ----------------------------
route = st.session_state.route
is_logged_in = st.session_state.user_token is not None

if not is_logged_in:
    render_signup_and_login_page()

else:
    if route == "manage":
        render_manage_tenants_page()

    elif route == "pricing":
        render_pricing_and_subscription_page()

    elif route == "analyze":
        render_analyze_your_data_page()

    elif route == "predict":
        render_predict_your_business_page() 

    elif route == "recommend":
        render_get_business_recommendation_page() 
    
    elif route == "about":
        render_about_page()

    elif route == "terms":
        render_terms_page()

    elif route == "privacy":
        render_privacy_policy_page()

    else:
        render_manage_tenants_page()

# ----------------------------
# FOOTER NAVIGATION
# ----------------------------
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("ℹ️ About", use_container_width=True):
        st.session_state.route = "about"
        st.rerun()

with col2:
    if st.button("📜 Terms", use_container_width=True):
        st.session_state.route = "terms"
        st.rerun()

with col3:
    if st.button("🔒 Privacy", use_container_width=True):
        st.session_state.route = "privacy"
        st.rerun()

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("""
<div style="
    text-align: center;
    color: #6B7280;
    font-size: 12px;
    margin-top: 20px;
    padding-bottom: 10px;
">
    © 2026 Maduk Business Intelligence • All Rights Reserved
</div>
""", unsafe_allow_html=True)