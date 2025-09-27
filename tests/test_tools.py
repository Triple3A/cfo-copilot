import pandas as pd
from datetime import datetime
from agent.tools import *

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
    assert result["figure"] is not None


def test_get_gross_margin_trend():
    """
    Tests the gross margin trend calculation with mock data.
    """

    actuals_data = {
        'account_category': ['Revenue', 'COGS', 'Revenue', 'COGS'],
        'month': [datetime(2025, 4, 1), datetime(2025, 4, 1), datetime(2025, 5, 1), datetime(2025, 5, 1)],
        'amount_usd': [80000, 30000, 90000, 35000],
        'amount_eur': [84800, 31800, 95400, 37150]
    }
    budget_data = {
        'account_category': ['Revenue', 'COGS', 'Revenue', 'COGS'],
        'month': [datetime(2025, 4, 1), datetime(2025, 4, 1), datetime(2025, 5, 1), datetime(2025, 5, 1)],
        'amount_usd': [85000, 32000, 88000, 36000],
        'amount_eur': [85150, 32120, 88240, 36120]
    }
    mock_data = {
        "actuals": pd.DataFrame(actuals_data),
        "budget": pd.DataFrame(budget_data)
    }


    result = get_gross_margin_trend(mock_data, 2)


    assert "The latest gross margin for May 2025 was 61.1%." in result["response"]
    assert result["figure"] is not None


def test_get_opex_breakdown():
    """
    Tests the OPEX breakdown calculation with mock data.
    """

    actuals_data = {
        'account_category': ['Opex:Marketing', 'Opex:R&D', 'Opex:Sales', 'Opex:Admin'],
        'month': [datetime(2025, 6, 1), datetime(2025, 6, 1), datetime(2025, 6, 1), datetime(2025, 6, 1)],
        'amount_usd': [30000, 20000, 15000, 5000],
        'amount_eur': [31800, 21200, 15900, 5300]
    }
    
    mock_data = {
        "actuals": pd.DataFrame(actuals_data),
    }


    result = get_opex_breakdown(mock_data, "June 2025", 'USD')


    assert "Marketing: $30,000" in result["response"]
    assert "R&D: $20,000" in result["response"]
    assert "Sales: $15,000" in result["response"]
    assert "Admin: $5,000" in result["response"]
    assert "Total Opex: $70,000" in result["response"]
    assert result["figure"] is not None


def test_get_ebitda():
    """
    Tests the EBITDA calculation with mock data.
    """

    actuals_data = {
        'account_category': ['Revenue', 'COGS', 'Opex:Marketing', 'Opex:R&D'],
        'month': [datetime(2025, 6, 1), datetime(2025, 6, 1), datetime(2025, 6, 1), datetime(2025, 6, 1)],
        'amount_usd': [100000, 40000, 30000, 20000],
        'amount_eur': [106400, 40300, 31800, 21200]
    }
    mock_data = {
        "actuals": pd.DataFrame(actuals_data),
    }


    result = get_ebitda(mock_data, "June 2025", 'EUR')


    assert "EBITDA for June 2025: €13,100" in result["response"]
    assert result["figure"] is not None