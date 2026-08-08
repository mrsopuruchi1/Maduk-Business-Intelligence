import streamlit as st
import requests
import os
import re
import time

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def render_signup_module():
    st.markdown("## 🚀 Create an Account")
    st.caption("Signup to start using Maduk Business Intelligence")

    if "signup_loading" not in st.session_state:
        st.session_state.signup_loading = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="
            padding:25px;
            border-radius:12px;
            background-color:#262730;
            box-shadow:0px 4px 12px rgba(0,0,0,0.2);
        ">
        """, unsafe_allow_html=True)

        with st.form("signup_form"):

            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email", placeholder="you@example.com")

            show_password = st.checkbox("Show password")

            password = st.text_input(
                "Password",
                type="text" if show_password else "password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="text" if show_password else "password"
            )

            remember_me = st.checkbox("Remember Me")

            submitted = st.form_submit_button(
                "🚀 Create Account",
                disabled=st.session_state.signup_loading
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ----------------------------
        # NAVIGATION
        # ----------------------------
        st.markdown("Already have an account?")
        if st.button("🔑 Login"):
            st.session_state.auth_view = "login"
            st.rerun()

    # ----------------------------
    # FORM LOGIC
    # ----------------------------
    if submitted:
        st.session_state.signup_loading = True

        if not all([first_name, last_name, email, password]):
            st.warning("⚠️ Fill all fields")
            st.session_state.signup_loading = False
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.warning("⚠️ Enter a valid email")
            st.session_state.signup_loading = False
            return

        if password != confirm_password:
            st.error("❌ Passwords do not match")
            st.session_state.signup_loading = False
            return

        with st.spinner("Creating account..."):
            try:
                res = requests.post(
                    f"{BASE_URL}/auth/signup",
                    params={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "password": password
                    }
                )

                if res.status_code == 200:
                    data = res.json()

                    # ✅ STORE TOKEN FIRST
                    token = data["access_token"]
                    st.session_state["user_token"] = token

                    # ✅ FETCH TENANTS IMMEDIATELY
                    tenants_res = requests.get(
                        f"{BASE_URL}/tenants/list",
                        headers={"Authorization": f"Bearer {token}"}
                    )

                    if tenants_res.status_code == 200:
                        tenants = tenants_res.json()

                        if tenants:
                            st.session_state["active_tenant_id"] = tenants[0]["tenant_id"]
                            st.session_state["active_tenant_name"] = tenants[0]["name"]

                    # ✅ REMEMBER ME
                    if remember_me:
                        st.session_state["remember_me"] = True

                    st.toast("🎉 Account created!")
                    st.success("Welcome aboard 🚀")

                    time.sleep(1)

                    # ✅ REDIRECT TO DASHBOARD
                    st.session_state.auth_view = "dashboard"

                    st.session_state.signup_loading = False
                    st.rerun()

                else:
                    st.error(f"❌ Signup failed: {res.text}")

            except Exception as e:
                st.error(f"🚨 Network error: {str(e)}")

        st.session_state.signup_loading = False