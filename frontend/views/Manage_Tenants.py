import streamlit as st
import requests
import os

# ----------------------------
# IMPORT MODULE
# ----------------------------
from modules.membership_dashboard_module import render_membership_dashboard_module
from utils.workspace_state import (
    set_active_workspace,
    ensure_workspace,
    get_active_workspace
)

from utils.api_config import get_backend_url

BASE_URL = get_backend_url()


def render_manage_tenants_page():

    # ----------------------------
    # AUTH CHECK
    # ----------------------------
    if "user_token" not in st.session_state:
        st.warning("🔒 You must be logged in to access this page")
        st.stop()

    user_token = st.session_state.user_token
    headers = {"Authorization": f"Bearer {user_token}"}

    # ----------------------------
    # GLOBAL STYLES
    # ----------------------------
    st.markdown("""
    <style>
    .main {
        padding: 1.5rem 2rem;
    }

    .stButton>button {
        border-radius: 10px;
        height: 3em;
        font-weight: 500;
    }

    .card {
        padding: 20px;
        border-radius: 12px;
        background-color: #262730;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
        text-align:center;
    }

    .header {
        font-size: 24px;
        font-weight: 600;
    }

    .subtle {
        color: #9CA3AF;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # HEADER
    # ----------------------------
    col1, col2 = st.columns([8, 2])

    with col1: 
        st.markdown('<div class="header">🔓 ALL THE SUBSCRIPTION (PRO) FEATURES OF THIS SAAS PLATFORM ARE CURRENTLY *FREE* OF CHARGE 🎁</div>', unsafe_allow_html=True)

        st.divider() 

        st.markdown('<div class="header">🏢 Tenant Management Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle">Manage tenants, members, and access</div>', unsafe_allow_html=True)

    with col2:
        st.button("🔔 Notifications")

    st.divider()

    # ----------------------------
    # FETCH TENANTS (FIXED)
    # ----------------------------
    def fetch_tenants():
        try:
            res = requests.get(
                f"{BASE_URL}/tenants/list",
                headers=headers
            )

            if res.status_code == 200:
                return res.json()
            else:
                st.error(f"Failed to fetch tenants: {res.text}")
                return []

        except Exception as e:
            st.error(f"Error fetching tenants: {str(e)}")
            return []

    tenants = fetch_tenants()

    # ----------------------------
    # EMPTY STATE
    # ----------------------------
    if not tenants:
        st.warning("No tenants found. Please create a tenant first.")
        return

    # ----------------------------
    # ✅ WORKSPACE SWITCHER
    # ----------------------------
    ensure_workspace(tenants)

    tenant_map = {t["name"]: t["tenant_id"] for t in tenants}

    active_id, active_name = get_active_workspace()

    selected_name = st.selectbox(
        "🏢 Switch Workspace",
        options=list(tenant_map.keys()),
        index=list(tenant_map.keys()).index(active_name)
        if active_name in tenant_map else 0
    )

    selected_id = tenant_map[selected_name]

    # ✅ Update workspace only if changed
    if selected_id != active_id:
        set_active_workspace(selected_id, selected_name)
        st.rerun()

    tenant_id = selected_id

    # ----------------------------
    # FETCH MEMBERS FOR STATS
    # ----------------------------
    total_members = 0
    active_members = 0
    pending_members = 0

    try:
        res = requests.get(
            f"{BASE_URL}/tenants/members/list",
            params={"tenant_id": tenant_id},
            headers=headers
        )

        if res.status_code == 200:
            members = res.json()
            total_members = len(members)
            active_members = len([m for m in members if m.get("status") == "active"])
            pending_members = len([m for m in members if m.get("status") == "pending"])
        else:
            st.error(f"Failed to fetch members: {res.text}")

    except Exception as e:
        st.error(f"Error fetching members: {str(e)}")

    # ----------------------------
    # DASHBOARD CARDS
    # ----------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'<div class="card">👥 <b>Total Members</b><br><br><h2>{total_members}</h2></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="card">✅ <b>Active</b><br><br><h2>{active_members}</h2></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="card">⏳ <b>Pending</b><br><br><h2>{pending_members}</h2></div>', unsafe_allow_html=True)

    st.divider()

    # ----------------------------
    # MEMBERSHIP DASHBOARD
    # ----------------------------
    st.subheader("🧑‍🤝‍🧑 Membership Management Dashboard")

    render_membership_dashboard_module(
        user_token=user_token,
        tenant_id=tenant_id,
        tenant_name=selected_name
    )