import streamlit as st
import requests
import os
import pandas as pd

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def render_membership_dashboard_module(user_token: str, tenant_id: int, tenant_name: str):

    # ✅ FIX: Sync with active workspace
    tenant_id = st.session_state.get("active_tenant_id", tenant_id)
    tenant_name = st.session_state.get("active_tenant_name", tenant_name)

    st.caption("Manage tenants, members, roles, and access")
    headers = {"Authorization": f"Bearer {user_token}"}

    # ----------------------------
    # SESSION STATE
    # ----------------------------
    if "members_data" not in st.session_state:
        st.session_state.members_data = []

    if "confirm_remove_tenant" not in st.session_state:
        st.session_state.confirm_remove_tenant = False

    # ----------------------------
    # HELPER: API RESPONSE
    # ----------------------------
    def handle_response(res):
        if res.status_code == 200:
            return res.json(), None
        elif res.status_code == 403:
            return None, "Permission denied"
        elif res.status_code == 401:
            return None, "Session expired"
        else:
            return None, f"Error: {res.text}"

    # ----------------------------
    # FETCH MEMBERS
    # ----------------------------
    def fetch_members():
        try:
            res = requests.get(
                f"{BASE_URL}/tenants/members/list",
                params={"tenant_id": tenant_id},
                headers=headers
            )
            data, error = handle_response(res)

            if error:
                st.error(error)
                st.session_state.members_data = []
            else:
                st.session_state.members_data = data or []

        except Exception as e:
            st.error(f"Failed to fetch members: {str(e)}")
            st.session_state.members_data = []

    fetch_members()
    members = st.session_state.members_data

    # ✅ SHOW ACTIVE WORKSPACE
    st.info(f"🏢 Active Workspace: {tenant_name}")

    st.divider()

    # ----------------------------
    # TABS
    # ----------------------------
    tab_members, tab_add = st.tabs([
        "📋 Members",
        "➕ Add Member"
    ])

    # ============================
    # ADD MEMBER
    # ============================
    with tab_add:
        with st.form("add_member_form", clear_on_submit=True):
            user_id = st.text_input("User ID", key="add_user_id")
            role = st.selectbox("Role", ["Admin", "Floor"])
            submitted = st.form_submit_button("➕ Add Member")

            if submitted:
                if not user_id:
                    st.warning("User ID required")
                else:
                    with st.spinner("Adding member..."):
                        res = requests.post(
                            f"{BASE_URL}/tenants/members/add",
                            params={
                                "tenant_id": tenant_id,
                                "target_user_id": user_id,
                                "role": role,
                            },
                            headers=headers,
                        )

                        _, error = handle_response(res)

                        if error:
                            st.error(error)
                        else:
                            st.success("Member added successfully 🎉")
                            st.rerun()

    # ============================
    # MEMBERS TAB
    # ============================
    with tab_members:
        search = st.text_input("🔍 Search members")

        display_members = members

        if search:
            display_members = [
                m for m in members
                if search.lower() in m.get("name", "").lower()
            ]

        if display_members:

            st.markdown(
                f"<h3 style='color:white;'>👥 Members of {tenant_name}</h3>",
                unsafe_allow_html=True
            )

            for m in display_members:

                role = m.get("role", "Floor").capitalize()
                is_owner = role == "Owner"

                badge = "👑 Owner" if is_owner else f"🎭 {role}"
                user_id_val = m.get("user_id")

                st.markdown(f"""
                <div style="
                    padding:15px;
                    border-radius:12px;
                    background:#262730;
                    margin-bottom:10px;
                    box-shadow:0px 3px 10px rgba(0,0,0,0.2);
                    color:white;
                ">
                    <div style="font-size:16px; font-weight:600;">
                        👤 {m.get("name", "N/A")}
                    </div>
                    <div style="color:#d1d5db;">
                        📧 {m.get("email", "N/A")}
                    </div>
                    <hr style="border:0.5px solid #444;">
                    <div>🆔 User ID: {user_id_val}</div>
                    <div>🏢 Tenant ID: {m.get("tenant_id")}</div>
                    <div style="margin-top:8px; font-weight:500;">
                        {badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ----------------------------
                # CONTROLS (NON-OWNER ONLY)
                # ----------------------------
                if not is_owner:

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        new_role = st.selectbox(
                            "Change Role",
                            ["Admin", "Floor"],
                            key=f"role_{user_id_val}"
                        )

                    with col2:
                        if st.button("Update Role", key=f"update_{user_id_val}"):
                            res = requests.post(
                                f"{BASE_URL}/tenants/members/change-role",
                                params={
                                    "tenant_id": tenant_id,
                                    "target_user_id": user_id_val,
                                    "new_role": new_role
                                },
                                headers=headers
                            )

                            if res.status_code == 200:
                                st.success("Role updated ✅")
                                st.rerun()
                            else:
                                st.error(res.text)

                    with col3:
                        if st.button("Remove", key=f"remove_{user_id_val}"):
                            st.session_state[f"confirm_remove_{user_id_val}"] = True

                        if st.session_state.get(f"confirm_remove_{user_id_val}", False):
                            st.warning(f"Remove {m.get('name','member')}?")
                            c1, c2 = st.columns(2)

                            with c1:
                                if st.button("Yes", key=f"yes_{user_id_val}"):
                                    res = requests.delete(
                                        f"{BASE_URL}/tenants/members/remove",
                                        params={
                                            "tenant_id": tenant_id,
                                            "target_user_id": user_id_val
                                        },
                                        headers=headers
                                    )

                                    if res.status_code == 200:
                                        st.success("Member removed 🗑️")
                                        st.session_state[f"confirm_remove_{user_id_val}"] = False
                                        st.rerun()
                                    else:
                                        st.error(res.text)

                            with c2:
                                if st.button("Cancel", key=f"cancel_{user_id_val}"):
                                    st.session_state[f"confirm_remove_{user_id_val}"] = False

        else:
            st.info("No members found for this tenant.")