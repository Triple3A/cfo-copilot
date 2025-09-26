import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from math import ceil


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
    return datetime.strptime(date_str, '%Y-%m')


def load_and_prepare_data():
    """Loads, cleans, and prepares all financial data from CSVs."""
    actuals = pd.read_csv('actuals.csv')
    budget = pd.read_csv('budget.csv')
    fx = pd.read_csv('fx.csv')
    cash = pd.read_csv('cash.csv')

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


def get_revenue(data, month_str, currency):
    """Calculates Revenue (Actual vs Budget) for a given month."""
    try:
        target_date = datetime.strptime(month_str, '%B %Y')
        target_period = pd.Period(target_date, freq='M')
    except ValueError:
        return {"response": "I couldn't understand the date. Please use 'Month YYYY' format.", "figure": None}


    rev_actuals = data['actuals'][data['actuals']['account_category'] == 'Revenue']
    rev_budget = data['budget'][data['budget']['account_category'] == 'Revenue']

    if currency == 'EUR':
        col = 'amount_eur'
    else:
        col = 'amount_usd'


    monthly_actual = rev_actuals[rev_actuals['month'].dt.to_period('M') == target_period][col].sum()
    monthly_budget = rev_budget[rev_budget['month'].dt.to_period('M') == target_period][col].sum()

    if monthly_actual == 0 and monthly_budget == 0:
         return {"response": f"No revenue data found for {month_str}.", "figure": None}


    variance = monthly_actual - monthly_budget
    variance_pct = (variance / monthly_budget) * 100 if monthly_budget != 0 else float('inf')

    sign = '$' if currency == 'USD' else '€'

    response = (
        f"Revenue for {month_str}:\n"
        f"- Actual: {sign}{monthly_actual:,.0f}\n"
        f"- Budget: {sign}{monthly_budget:,.0f}\n"
        f"- Variance: {sign}{variance:,.0f} ({variance_pct:.1f}%)"
    )


    df = pd.DataFrame({
        'Category': ['Actual', 'Budget'],
        f'Amount ({currency})': [monthly_actual, monthly_budget]
    })
    fig = px.bar(df, x='Category', y=f'Amount ({currency})', title=f'Revenue - {month_str}', text_auto='.2s')
    fig.update_traces(textangle=0, textposition="outside")


    return {"response": response, "figure": fig}


def get_gross_margin_trend(data, last_n_months=6):
    """Calculates Gross Margin % trend for the last N months."""
    df = data['actuals'].copy()
    df = df[df['account_category'].isin(['Revenue', 'COGS'])]

    pivot = df.pivot_table(index='month', columns='account_category', values='amount_usd', aggfunc='sum').fillna(0)
    pivot = pivot.sort_index(ascending=False).head(last_n_months).sort_index()

    pivot['Gross_Margin_USD'] = pivot['Revenue'] - pivot.get('COGS', 0)
    pivot['Gross_Margin_%'] = (pivot['Gross_Margin_USD'] / pivot['Revenue']).fillna(0) * 100

    latest_month = pivot.index.max().strftime('%B %Y')
    latest_gm = pivot.loc[pivot.index.max(), 'Gross_Margin_%']
    response = (
        f"Gross Margin Trend:\n"
        f"The latest gross margin for {latest_month} was {latest_gm:.1f}%."
    )

    fig = px.line(pivot, y='Gross_Margin_%', title=f'Gross Margin % Trend (Last {last_n_months} Months)', markers=True)
    fig.update_layout(yaxis_title='Gross Margin %', xaxis_title='Month')
    fig.update_yaxes(ticksuffix="%")

    return {"response": response, "figure": fig}


def get_opex_breakdown(data, month_str, currency='USD'):
    """Provides OPEX breakdown by account for a given month."""
    try:
        target_date = datetime.strptime(month_str, '%B %Y')
        target_period = pd.Period(target_date, freq='M')
    except ValueError:
        return {"response": "I couldn't understand the date. Please use 'Month YYYY' format.", "figure": None}

    col = 'amount_usd' if currency == 'USD' else 'amount_eur'

    opex_actuals = data['actuals'][data['actuals']['account_category'].str.startswith('Opex')].copy()
    opex_actuals['Opex_Category'] = opex_actuals['account_category'].str.split(':').str[1]

    monthly_opex_breakdown = opex_actuals[opex_actuals['month'].dt.to_period('M') == target_period].groupby('Opex_Category')[col].sum().reset_index()
    opex_total = monthly_opex_breakdown[col].sum()

    if monthly_opex_breakdown.empty:
        return {"response": f"No OPEX data found for {month_str}.", "figure": None}

    sign = '$' if currency == 'USD' else '€'

    response = f"Opex Breakdown for {month_str} ({currency}):\n"
    for index, row in monthly_opex_breakdown.iterrows():
        response += f"- {row['Opex_Category']}: {sign}{row[col]:,.0f}\n"
    response += f"Total Opex: {sign}{opex_total:,.0f}"

    fig = px.pie(monthly_opex_breakdown, names=['Admin', 'Marketing', 'R&D', 'Sales'], values=col, title=f'OPEX Breakdown - {month_str}', hole=0.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True)

    return {"response": response, "figure": fig}


def get_ebitda(data, month_str, currency='USD'):
    """Calculates EBITDA for a given month."""
    try:
        target_date = datetime.strptime(month_str, '%B %Y')
        target_period = pd.Period(target_date, freq='M')
    except ValueError:
        return {"response": "I couldn't understand the date. Please use 'Month YYYY' format.", "figure": None}

    col = 'amount_usd' if currency == 'USD' else 'amount_eur'
    
    # Filter for Revenue
    rev_actuals = data['actuals'][data['actuals']['account_category'] == 'Revenue'].copy()
    month_rev_actuals = rev_actuals[rev_actuals['month'].dt.to_period('M') == target_period][col].sum()

    cogs_actuals = data['actuals'][data['actuals']['account_category'] == 'COGS'].copy()
    month_cogs_actuals = cogs_actuals[cogs_actuals['month'].dt.to_period('M') == target_period][col].sum()

    opex_actuals = data['actuals'][data['actuals']['account_category'].str.startswith('Opex')].copy()
    month_opex_actuals = opex_actuals[opex_actuals['month'].dt.to_period('M') == target_period][col].sum()
    
    ebitda = month_rev_actuals - month_cogs_actuals - month_opex_actuals

    sign = '$' if currency == 'USD' else '€'
    response = (
        f"EBITDA for {month_str}: {sign}{ebitda:,.0f}"
    )

    df = pd.DataFrame({
        'Category': ['Revenue', 'COGS', 'Opex'],
        f'Amount ({currency})': [month_rev_actuals, month_cogs_actuals, month_opex_actuals]
    })

    fig = px.bar(df, x='Category', y=f'Amount ({currency})', title=f'EBITDA - {month_str}', text_auto='.2s')
    fig.update_traces(textangle=0, textposition="outside")

    return {"response": response, "figure": fig}


def get_cash_runway(data, currency='USD'):
    """Calculates Cash Runway for the last 3 months."""
    LAST_N_MONTHS = 3
    sign = '$' if currency == 'USD' else '€'
    december_ebitda = int(get_ebitda(data, 'December 2025', currency)['response'].split(sign)[1].replace(',', ''))
    november_ebitda = int(get_ebitda(data, 'November 2025', currency)['response'].split(sign)[1].replace(',', ''))
    october_ebitda = int(get_ebitda(data, 'October 2025', currency)['response'].split(sign)[1].replace(',', ''))

    avg_net_burn = -(december_ebitda + november_ebitda + october_ebitda) / LAST_N_MONTHS

    col = 'cash_usd' if currency == 'USD' else 'cash_eur'
    cash = int(data['cash'].tail(1)[col].iloc[0])

    cash_runway = cash / avg_net_burn

    response = ""
    fig = go.Figure()
    latest_month_date = data['cash']['month'].max()
    
    if avg_net_burn > 0:
        response = (
            f"Cash Runway Analysis:\n"
            f"- Current Cash: {sign}{cash:,.0f}\n"
            f"- Avg. Monthly Net Burn (Last {LAST_N_MONTHS} Months): {sign}{avg_net_burn:,.0f}\n\n"
            f"At the current burn rate, the estimated cash runway is {cash_runway:.1f} months."
        )

        projected_dates = []
        projected_cash = []
        projection_horizon = int(cash_runway) + 3 
        
        for i in range(projection_horizon):
            future_date = latest_month_date + pd.DateOffset(months=i)
            future_cash = cash - (i * avg_net_burn)
            projected_dates.append(future_date)
            projected_cash.append(max(0, future_cash))
            if future_cash <= 0:
                break


        fig.add_trace(go.Scatter(
            x=data['cash'].tail(10)['month'], y=data['cash'].tail(10)[col].values,
            mode='lines+markers', name='Historical Cash', line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=projected_dates, y=projected_cash,
            mode='lines+markers', name='Projected Runway', line=dict(color='red', dash='dash')
        ))

        fig.add_hline(y=0, line_width=1, line_dash="solid", line_color="black")
        

        end_of_runway_date = latest_month_date + pd.DateOffset(months=ceil(cash_runway))
        fig.add_annotation(
            x=end_of_runway_date, y=0,
            text=f"End of Runway (~{cash_runway:.1f} months)",
            showarrow=True, arrowhead=1, ax=0, ay=-40,
            bgcolor="rgba(255, 0, 0, 0.7)", textangle=0, font=dict(color="white")
        )

    else:

        monthly_profit = -avg_net_burn
        response = (
            f"Cash Flow Analysis:\n"
            f"- Current Cash: {sign}{cash:,.0f}\n"
            f"- Avg. Monthly Net Profit (Last {LAST_N_MONTHS} Months): {sign}{monthly_profit:,.0f}\n\n"
            f"The company is cash flow positive based on the last three months.\n"
            f"The concept of a 'cash runway' does not apply, as the cash balance is growing."
        )

        projected_dates = []
        projected_cash = []

        for i in range(6):
            future_date = latest_month_date + pd.DateOffset(months=i)

            future_cash = cash + (i * monthly_profit)
            projected_dates.append(future_date)
            projected_cash.append(future_cash)


        fig.add_trace(go.Scatter(
            x=data['cash'].tail(10)['month'], y=data['cash'].tail(10)[col].values,
            mode='lines+markers', name='Historical Cash', line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=projected_dates, y=projected_cash,
            mode='lines+markers', name='Projected Growth', line=dict(color='green', dash='dash')
        ))


    x = 0.7 if avg_net_burn > 0 else 0.01
    fig.update_layout(
        title='Cash Balance and Projected Runway',
        xaxis_title='Month',
        yaxis_title=f'Cash ({currency})',
        yaxis_tickprefix=sign,
        yaxis_tickformat=',.0f',
        legend=dict(x=x, y=0.98, bordercolor="Black", borderwidth=1),
        margin=dict(t=50, b=10, l=10, r=10)
    )

    return {"response": response, "figure": fig}