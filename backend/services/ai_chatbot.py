# backend/ai_chatbot.py
from typing import List
import openai
import os

# Load API key from .env
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_business_advice(question: str, kpi_data: dict) -> List[str]:
    """
    Generate actionable business advice for digital agencies based on a question and KPI data.
    Behaves like a self-learning AI consultant.
    """
    if not question:
        return ["Please ask a question to get advice."]

    prompt = f"""
You are a top-tier business consultant for digital agencies. 
The client's KPI data is: {kpi_data}.
Provide 5 actionable recommendations in bullet points for their business based on this question: {question}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        advice_text = response.choices[0].message.content
        advice_lines = [line.strip("• ").strip("- ").strip() for line in advice_text.split("\n") if line.strip()]
        return advice_lines[:5]
    except Exception as e:
        return [f"Error generating advice: {str(e)}"]