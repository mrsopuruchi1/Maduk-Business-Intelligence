import streamlit as st
import requests
import os
import time

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def render_subscription_module(user_token: str):

    headers = {"Authorization": f"Bearer {st.session_state.get('user_token')}"}

    # ----------------------------
    # GLOBAL STYLING (STRIPE-LIKE)
    # ----------------------------
    st.markdown("""
    <style>
    .pricing-card {
        padding: 25px;
        border-radius: 16px;
        background: #262730;
        text-align: center;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.25);
        transition: 0.3s;
    }
    .pricing-card:hover {
        transform: scale(1.02);
    }
    .highlight {
        border: 2px solid #00C8FF;
    }
    .price {
        font-size: 32px;
        font-weight: bold;
    }
    .feature {
        text-align: left;
        margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # STATE
    # ----------------------------
    if "sub_loading" not in st.session_state:
        st.session_state.sub_loading = None

    # ----------------------------
    # HEADER
    # ----------------------------
    st.markdown("## 💳 Pricing & Subscription Dashboard")
    st.caption("Choose a plan that fits your business")

    # ----------------------------
    # FETCH CURRENT SUBSCRIPTION
    # ----------------------------
    current_plan = "Starter"
    subscription_status = "inactive"

    try:
        res = requests.get(f"{BASE_URL}/subscription-status", headers=headers)
        if res.status_code == 200:
            data = res.json()
            current_plan = data.get("plan", "Starter")
            subscription_status = data.get("status", "inactive")
    except:
        pass

    st.info(f"📦 Current Plan: **{current_plan}** | Status: **{subscription_status}**")

    # ----------------------------
    # CURRENCY TOGGLE
    # ----------------------------
    currency = st.radio("💱 Currency", ["USD", "NGN"], horizontal=True)

    # ----------------------------
    # PLAN DEFINITIONS
    # ----------------------------
    plans = {
        "Starter": {
            "price_usd": 0,
            "price_ngn": 0,
            "features": ["Data Upload", "Analysis", "Visualization", "Conclusion"]
        },
        "Professional": {
            "price_usd": 30,
            "price_ngn": 24000,
            "features": [
                "All Starter Features",
                "Campaign Prediction",
                "Churn Prediction",
                "Revenue Forecast",
                "PDF Reports"
            ]
        },
        "Agency": {
            "price_usd": 50,
            "price_ngn": 40000,
            "features": [
                "All Professional Features",
                "Budget Optimizer",
                "Anomaly Detection",
                "Growth Strategy",
                "AI Chatbot"
            ]
        },
        "Enterprise": {
            "price_usd": 100,
            "price_ngn": 80000,
            "features": [
                "All Agency Features",
                "Multi-Client",
                "API Access",
                "Autonomous AI Consultant"
            ]
        }
    }

    cta_map = {
        "Starter": "Start Free",
        "Professional": "Upgrade to Pro 🚀",
        "Agency": "Scale Your Business 📈",
        "Enterprise": "Go Enterprise 🏢"
    }

    # ----------------------------
    # PRICING CARDS
    # ----------------------------
    cols = st.columns(4)

    for idx, (plan_name, plan) in enumerate(plans.items()):
        with cols[idx]:

            is_popular = plan_name == "Professional"
            is_current = plan_name == current_plan

            card_class = "pricing-card highlight" if is_popular else "pricing-card"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

            if is_popular:
                st.markdown("🔥 **Most Popular**")

            if is_current:
                st.markdown("✅ **Current Plan**")

            st.subheader(plan_name)

            price = plan["price_usd"] if currency == "USD" else plan["price_ngn"]
            symbol = "$" if currency == "USD" else "₦"

            st.markdown(f'<div class="price">{symbol}{price}/mo</div>', unsafe_allow_html=True)

            st.markdown("---")

            for feature in plan["features"]:
                st.markdown(f'<div class="feature">✅ {feature}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            disabled = is_current or (st.session_state.sub_loading == plan_name)

            if st.button(
                cta_map[plan_name],
                key=f"sub_{plan_name}",
                disabled=disabled,
                use_container_width=True
            ):
                st.session_state.sub_loading = plan_name

                with st.spinner("Processing subscription..."):
                    try:
                        res = requests.post(
                            f"{BASE_URL}/subscribe",
                            json={
                                "plan": plan_name,
                                "currency": currency
                            },
                            headers=headers
                        )

                        if res.status_code == 200:
                            data = res.json()
                            payment_link = data.get("payment_link")

                            # ----------------------------
                            # STARTER PLAN
                            # ----------------------------
                            if plan_name == "Starter":
                                st.success("✅ Starter plan activated")
                                st.balloons()
                                st.rerun()

                            # ----------------------------
                            # PAID PLANS
                            # ----------------------------
                            elif payment_link:
                                st.success("💳 Redirecting to payment...")

                                # Auto redirect (Streamlit safe)
                                st.markdown(
                                    f'<meta http-equiv="refresh" content="0; url={payment_link}">',
                                    unsafe_allow_html=True
                                )

                                st.markdown(f"[👉 Click here if not redirected]({payment_link})")

                            else:
                                st.error("❌ Payment link not returned by backend")
                                st.json(data)

                        elif res.status_code == 401:
                            st.error("Session expired. Please login again.")

                        else:
                            st.error(f"Subscription failed: {res.text}")

                    except Exception as e:
                        st.error(f"Network error: {str(e)}")

                st.session_state.sub_loading = None

            st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------
    # CANCEL SUBSCRIPTION
    # ----------------------------
    st.divider()
    st.subheader("❌ Cancel Subscription")

    if current_plan == "Starter":
        st.info("You are already on the free plan.")
    else:
        if st.button("Cancel Subscription", use_container_width=True):
            with st.spinner("Cancelling subscription..."):
                try:
                    res = requests.post(
                        f"{BASE_URL}/cancel-subscription",
                        headers=headers
                    )

                    if res.status_code == 200:
                        st.success("✅ Subscription cancelled. Downgraded to Starter.")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Cancellation failed")

                except Exception:
                    st.error("Network error")