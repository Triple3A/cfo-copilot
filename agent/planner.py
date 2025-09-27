import os
import json
import google.generativeai as genai
from datetime import datetime
from agent import tools

def get_intent(query):
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return {"intent": "error", "params": {}}

    current_month_str = datetime.now().strftime("%B %Y")

    prompt = f"""
    You are a helpful financial assistant. Your job is to understand a user's question
    and classify it into one of the following intents. You must also extract any
    relevant parameters, like the month and year or the number of latest months.

    The current date is {current_month_str}. If the user asks about "this month" or "last month",
    use this for context.

    Intents:
    - revenue: For questions about revenue.
    - gross_margin_trend: For questions about gross margin trends.
    - opex_breakdown: For questions about operating expense breakdowns.
    - cash_runway: For questions about cash runway.
    - unknown: If the question doesn't fit any other category.

    Parameters:
    - month_str: The full month and year (e.g., "June 2025").
    - latest_n_months: The number of latest months to consider (e.g., 3).
    - currency: The currency to use (e.g., "USD", "EUR").

    User Question: "{query}"

    Respond ONLY with a JSON object. Do not add any other text or markdown formatting.
    The JSON object must be in the following format:
    {{
      "intent": "...",
      "params": {{
        "month_str": "...",
        "latest_n_months": ...,
        "currency": "..."
      }}
    }}
    """

    # Set up the model and generate the content
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content(prompt)

    try:
        # The Gemini response text needs to be cleaned of markdown backticks
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, IndexError, AttributeError):
        # Fallback if the model response is not valid JSON
        return {"intent": "unknown", "params": {}}



def run_query(query, data):
    """
    Main function to route the query to the correct tool.
    """
    intent_data = get_intent(query)
    intent = intent_data.get("intent")
    params = intent_data.get("params", {})
    currency = params.get("currency", "USD")

    print(f"DEBUG: Intent={intent}, Params={params}") # For debugging

    if intent == "revenue":
        month_str = params.get("month_str")
        if not month_str:
            return {"response": "You asked about revenue, but didn't specify a month. Please be more specific.", "figure": None}
        return tools.get_revenue(data, month_str, currency)

    elif intent == "gross_margin_trend":
        latest_n_months = params.get("latest_n_months", 3)
        return tools.get_gross_margin_trend(data, latest_n_months)
    
    elif intent == "opex_breakdown":
        month_str = params.get("month_str")
        if not month_str:
            return {"response": "You asked about OPEX breakdown, but didn't specify a month. Please be more specific.", "figure": None}
        return tools.get_opex_breakdown(data, month_str, currency)

    elif intent == "ebitda":
        month_str = params.get("month_str")
        if not month_str:
            return {"response": "You asked about EBITDA, but didn't specify a month. Please be more specific.", "figure": None}
        return tools.get_ebitda(data, month_str, currency)

    elif intent == "cash_runway":
        return tools.get_cash_runway(data, currency)
    
    else: # Handles "unknown" intent
        return {
            "response": "Sorry, I can't answer that question. I can help with:\n"
                        "- Revenue for a specific month\n"
                        "- Gross Margin trends\n"
                        "- Opex breakdowns\n"
                        "- EBITDA\n"
                        "- Cash runway",
            "figure": None
        }