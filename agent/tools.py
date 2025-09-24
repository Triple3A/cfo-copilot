import pandas as pd
import plotly.express as px
from datetime import datetime

def _clean_financial_value(value):
    """Cleans a string financial value into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if pd.isna(value) or value == '-':
        return 0.0
    value = str(value).strip().replace('$', '').replace(',', '')
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    return float(value)

def _parse_date(date_str):
    """Parses 'Mon-YY' into a datetime object."""
    return datetime.strptime(date_str, '%b-%y')

def load_and_prepare_data():
    """Loads, cleans, and prepares all financial data from CSVs."""
    actuals = pd.read_csv('fixtures/actuals.csv')
    budget = pd.read_csv('fixtures/budget.csv')
    fx = pd.read_csv('fixtures/fx.csv')
    cash = pd.read_csv('fixtures/cash.csv')

    # actuals = actuals.melt(id_vars=['entity', 'Account'], var_name='month', value_name='Actual')
    # budget = budget.melt(id_vars=['entity', 'Account'], var_name='month', value_name='Budget')
    # cash = cash.melt(id_vars=['entity'], var_name='month', value_name='Cash')

    actuals['amount'] = actuals['amount'].apply(_clean_financial_value)
    budget['amount'] = budget['amount'].apply(_clean_financial_value)
    cash['cash_usd'] = cash['cash_usd'].apply(_clean_financial_value)

    actuals['month'] = actuals['month'].apply(_parse_date)
    budget['month'] = budget['month'].apply(_parse_date)
    cash['month'] = cash['month'].apply(_parse_date)
    fx['month'] = pd.to_datetime(fx['month'])

    euro_rates = fx[fx['currency'] == 'EUR'][['month', 'rate_to_usd']].rename(columns={'rate_to_usd': 'rate_to_eur'})
    fx = pd.merge(fx, euro_rates, on='month', how='left')
    fx['rate_to_eur'] = fx['rate_to_usd'] / fx['rate_to_eur']
    euro_rates = fx[fx['currency'] == 'USD'][['month', 'rate_to_eur']]

    # Merge with FX rates
    actuals = pd.merge(actuals, fx, on=['month', 'currency'], how='left')
    budget = pd.merge(budget, fx, on=['month', 'currency'], how='left')
    cash = pd.merge(cash, euro_rates, on='month', how='left')

    actuals['amount_usd'] = actuals['amount'] * actuals['rate_to_usd']
    budget['amount_usd'] = budget['amount'] * budget['rate_to_usd']
    actuals['amount_eur'] = actuals['amount'] * actuals['rate_to_eur']
    budget['amount_eur'] = budget['amount'] * budget['rate_to_eur']
    cash['cash_eur'] = cash['cash_usd'] * cash['rate_to_eur']

    return {
        "actuals": actuals,
        "budget": budget,
        "cash": cash
    }
