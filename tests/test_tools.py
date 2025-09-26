import pandas as pd
from datetime import datetime
from agent.tools import get_revenue

def test_get_revenue():
    """
    Tests the revenue calculation with mock data.
    """

    actuals_data = {
        'account_category': ['Revenue', 'COGS'],
        'month': [datetime(2025, 6, 1), datetime(2025, 6, 1)],
        'amount_usd': [100000, 40000],
        'amount_eur': [106400, 40300]
    }
    budget_data = {
        'account_category': ['Revenue', 'COGS'],
        'month': [datetime(2025, 6, 1), datetime(2025, 6, 1)],
        'amount_usd': [90000, 45000],
        'amount_eur': [90500, 45350]
    }
    mock_data = {
        "actuals": pd.DataFrame(actuals_data),
        "budget": pd.DataFrame(budget_data)
    }


    result = get_revenue(mock_data, "June 2025", 'USD')


    assert "Actual: $100,000" in result["response"]
    assert "Budget: $90,000" in result["response"]
    assert "Variance: $10,000 (11.1%)" in result["response"]
    assert result["figure"] is not None # Check that a figure was generated