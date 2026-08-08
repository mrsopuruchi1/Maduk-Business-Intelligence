PLANS = {

    "starter": {
        "price_usd": 0,
        "price_ngn": 0,
        "features": [
            "data_upload",
            "analysis",
            "visualisation",
            "conclusion"
        ]
    },

    "professional": {
        "price_usd": 30,
        "price_ngn": 24000,
        "features": [
            "data_upload",
            "analysis",
            "visualisation",
            "conclusion",
            "campaign_prediction",
            "churn_prediction",
            "revenue_forecast",
            "pdf_reports"
        ]
    },

    "agency": {
        "price_usd": 50,
        "price_ngn": 40000,
        "features": [
            "data_upload",
            "analysis",
            "visualisation",
            "conclusion",
            "campaign_prediction",
            "churn_prediction",
            "revenue_forecast",
            "pdf_reports",
            "budget_optimizer",
            "anomaly_detection",
            "growth_strategy",
            "ai_chatbot"
        ]
    },

    "enterprise": {
        "price_usd": 100,
        "price_ngn": 80000,
        "features": [
            "all_features",
            "multi_client",
            "api_access",
            "autonomous_ai_consultant"
        ]
    }
}


def get_price(plan, currency="USD"):

    if currency == "NGN":
        return PLANS[plan]["price_ngn"]

    return PLANS[plan]["price_usd"]