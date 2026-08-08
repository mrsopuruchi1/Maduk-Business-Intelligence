import streamlit as st
import requests
import os
import re
import time

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def render_login_module():
    st.markdown("## 🔐 Welcome Back")
    st.caption("Login to continue using the platform")

    if "login_loading" not in st.session_state:
        st.session_state.login_loading = False

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

        # ----------------------------
        # FORM
        # ----------------------------
        with st.form("login_form"):

            email = st.text_input("Email", placeholder="you@example.com")

            show_password = st.checkbox("Show password")
            password = st.text_input(
                "Password",
                type="text" if show_password else "password"
            )

            remember_me = st.checkbox("Remember Me")

            submitted = st.form_submit_button(
                "Login",
                disabled=st.session_state.login_loading
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # NAVIGATION (FIXED)
        st.markdown("Don't have an account?")
        if st.button("📝 Create Account"):
            st.session_state.auth_view = "signup"
            st.rerun()

    # ----------------------------
    # FORM LOGIC
    # ----------------------------
    if submitted:
        st.session_state.login_loading = True

        if not email or not password:
            st.warning("⚠️ Please fill all fields")
            st.session_state.login_loading = False
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.warning("⚠️ Enter a valid email")
            st.session_state.login_loading = False
            return

        with st.spinner("Logging you in..."):
            try:
                res = requests.post(
                    f"{BASE_URL}/auth/login",
                    data={
                        "username": email,
                        "password": password
                    }
                )

                if res.status_code == 200:
                    data = res.json()
                    token = data.get("access_token")

                    # ✅ STORE TOKEN FIRST
                    st.session_state["user_token"] = token

                    # ✅ FETCH TENANTS (FIXED INDENTATION)
                    try:
                        tenant_res = requests.get(
                            f"{BASE_URL}/tenants/list",
                            headers={"Authorization": f"Bearer {token}"}
                        )

                        if tenant_res.status_code == 200:
                            tenants = tenant_res.json()
                            if tenants:
                                st.session_state["active_tenant_id"] = tenants[0]["tenant_id"]
                                st.session_state["active_tenant_name"] = tenants[0]["name"]

                    except Exception:
                        pass  # safe fallback

                    # ✅ REMEMBER ME
                    if remember_me:
                        st.session_state["remember_me"] = True
                    else:
                        st.session_state.pop("remember_me", None)

                    st.toast("🎉 Login successful!")
                    st.success("Welcome back! 🚀")
                    st.info("Redirecting...")

                    time.sleep(1)

                    # ✅ ROUTING FIX
                    st.session_state.auth_view = "dashboard"

                    st.session_state.login_loading = False
                    st.rerun()

                else:
                    st.error("❌ Invalid email or password")

            except Exception:
                st.error("🚨 Network error. Try again.")

        st.session_state.login_loading = False