from typing import List
import os

from openai import OpenAI


def generate_business_advice(question: str, kpi_data: dict) -> List[str]:
    """Generate actionable business advice from a question and KPI data."""
    if not question:
        return ["Please ask a question to get advice."]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ["AI chatbot is not configured: OPENAI_API_KEY is missing."]

    prompt = f"""
You are a top-tier business consultant for digital agencies.
The client's KPI data is: {kpi_data}.
Provide 5 actionable recommendations in bullet points for their business
based on this question: {question}
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400,
        )
        advice_text = response.choices[0].message.content or ""
        advice_lines = [
            line.strip("• ").strip("- ").strip()
            for line in advice_text.splitlines()
            if line.strip()
        ]
        return advice_lines[:5]
    except Exception as exc:
        return [f"Error generating advice: {exc}"]
