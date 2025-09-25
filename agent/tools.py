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
    """Parses 'Mon-YY' or 'YYYY-MM' into a datetime object."""
    # try:
    #     return datetime.strptime(date_str, '%b-%y')
    # except ValueError:
    return datetime.strptime(date_str, '%Y-%m')


def load_and_prepare_data():
    """Loads, cleans, and prepares all financial data from CSVs."""
    actuals = pd.read_csv('actuals.csv')
    budget = pd.read_csv('budget.csv')
    fx = pd.read_csv('fx.csv')
    cash = pd.read_csv('cash.csv')

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

    actuals.drop(columns=['amount', 'currency', 'rate_to_usd', 'rate_to_eur'], inplace=True)
    budget.drop(columns=['amount', 'currency', 'rate_to_usd', 'rate_to_eur'], inplace=True)
    cash.drop(columns=['rate_to_eur'], inplace=True)


    return {
        "actuals": actuals,
        "budget": budget,
        "cash": cash
    }


def get_revenue(data, month_str, currency='USD'):
    """Calculates Revenue (Actual vs Budget) for a given month."""
    try:
        target_date = datetime.strptime(month_str, '%B %Y')
        target_period = pd.Period(target_date, freq='M')
    except ValueError:
        return {"response": "I couldn't understand the date. Please use 'Month YYYY' format.", "figure": None}

    # Filter for Revenue
    rev_actuals = data['actuals'][data['actuals']['account_category'] == 'Revenue']
    rev_budget = data['budget'][data['budget']['account_category'] == 'Revenue']

    if currency == 'EUR':
        col = 'amount_eur'
    else:
        col = 'amount_usd'

    # Filter for Month
    monthly_actual = rev_actuals[rev_actuals['month'].dt.to_period('M') == target_period][col].sum()
    monthly_budget = rev_budget[rev_budget['month'].dt.to_period('M') == target_period][col].sum()

    if monthly_actual == 0 and monthly_budget == 0:
         return {"response": f"No revenue data found for {month_str}.", "figure": None}


    variance = monthly_actual - monthly_budget
    variance_pct = (variance / monthly_budget) * 100 if monthly_budget != 0 else float('inf')

    sign = '$' if currency == 'USD' else '€'
    # Create response
    response = (
        f"Revenue for {month_str}:\n"
        f"- Actual: {sign}{monthly_actual:,.0f}\n"
        f"- Budget: {sign}{monthly_budget:,.0f}\n"
        f"- Variance: {sign}{variance:,.0f} ({variance_pct:.1f}%)"
    )

    # Create chart
    df = pd.DataFrame({
        'Category': ['Actual', 'Budget'],
        f'Amount ({currency})': [monthly_actual, monthly_budget]
    })
    fig = px.bar(df, x='Category', y=f'Amount ({currency})', title=f'Revenue - {month_str}', text_auto='.2s')
    fig.update_traces(textangle=0, textposition="outside")


    return {"response": response, "figure": fig}