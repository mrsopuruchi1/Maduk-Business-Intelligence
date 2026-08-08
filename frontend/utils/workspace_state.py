import streamlit as st

def set_active_workspace(tenant_id: int, tenant_name: str):
    st.session_state["active_tenant_id"] = tenant_id
    st.session_state["active_tenant_name"] = tenant_name


def get_active_workspace():
    return (
        st.session_state.get("active_tenant_id"),
        st.session_state.get("active_tenant_name")
    )


def ensure_workspace(tenants: list):
    """
    Ensures a valid workspace is always selected
    """
    if "active_tenant_id" not in st.session_state or not st.session_state["active_tenant_id"]:
        if tenants:
            st.session_state["active_tenant_id"] = tenants[0]["tenant_id"]
            st.session_state["active_tenant_name"] = tenants[0]["name"]