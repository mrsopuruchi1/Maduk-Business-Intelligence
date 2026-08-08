import requests


def detect_currency():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=2)
        if response.status_code != 200:
            return "USD"

        data = response.json()
        return "NGN" if data.get("country_code") == "NG" else "USD"

    except:
        return "USD"