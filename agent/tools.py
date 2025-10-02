import pandas as pd

# --- Data Loading ---
DATA_FILE = "fixtures/data.xlsx"

def load_data():
    """
    Loads all necessary dataframes from the Excel file and standardizes month columns.
    """
    try:
        xls = pd.ExcelFile(DATA_FILE)
        actuals_df = pd.read_excel(xls, 'actuals')
        budget_df = pd.read_excel(xls, 'budget')
        cash_df = pd.read_excel(xls, 'cash')
        fx_df = pd.read_excel(xls, 'fx')

        # --- Data Cleaning & Standardization ---
        for df in [actuals_df, budget_df, cash_df, fx_df]:
            if 'month' not in df.columns:
                raise ValueError(f"Column 'month' not found in one of the sheets.")
            df['month_period'] = pd.to_datetime(df['month']).dt.to_period('M')

        for df, amount_col in [(actuals_df, 'amount'), (budget_df, 'amount'), (cash_df, 'cash_usd')]:
             if amount_col in df.columns:
                df[amount_col].fillna(0, inplace=True)

        return actuals_df, budget_df, cash_df, fx_df
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The data file was not found at {DATA_FILE}.")
    except Exception as e:
        raise Exception(f"An error occurred while loading data: {e}")

# --- Helper Functions ---
def _convert_to_usd(df: pd.DataFrame, fx_df: pd.DataFrame) -> pd.DataFrame:
    """Merges a dataframe with FX rates and converts 'amount' to USD."""
    if 'currency' not in df.columns:
        df['amount_usd'] = df['amount']
        return df
        
    merged_df = df.merge(fx_df, on=['month_period', 'currency'], how='left')
    # Assume 1.0 rate for USD or if rate is not found
    merged_df['rate_to_usd'].fillna(1.0, inplace=True)
    merged_df['amount_usd'] = merged_df['amount'] / merged_df['rate_to_usd']
    return merged_df

# --- Tool Functions ---

def get_revenue_vs_budget(actuals_df: pd.DataFrame, budget_df: pd.DataFrame, fx_df: pd.DataFrame, month_name: str, year: int):
    """Fetches and compares actual vs. budget revenue for a given month in USD."""
    try:
        target_period = pd.Period(f'{year}-{month_name}', freq='M')
    except ValueError:
        raise ValueError(f"Invalid month name: '{month_name}'. Please use a full month name (e.g., 'June').")

    # Filter for revenue
    actual_rev = actuals_df[actuals_df['account_category'].str.lower() == 'revenue'].copy()
    budget_rev = budget_df[budget_df['account_category'].str.lower() == 'revenue'].copy()

    # Convert to USD
    actual_rev_usd = _convert_to_usd(actual_rev, fx_df)
    budget_rev_usd = _convert_to_usd(budget_rev, fx_df)

    # Filter for the target month
    actual_monthly = actual_rev_usd[actual_rev_usd['month_period'] == target_period]['amount_usd'].sum()
    budget_monthly = budget_rev_usd[budget_rev_usd['month_period'] == target_period]['amount_usd'].sum()

    if actual_monthly == 0 and budget_monthly == 0:
        return None

    return {"actual": actual_monthly, "budget": budget_monthly}

def get_financial_metric_trend(actuals_df: pd.DataFrame, fx_df: pd.DataFrame, metric: str, last_n_months: int):
    """Calculates a financial metric (Gross Margin or EBITDA) over a trend period."""
    latest_month = actuals_df['month_period'].max()
    start_period = latest_month - last_n_months + 1
    
    recent_actuals = actuals_df[actuals_df['month_period'] >= start_period].copy()
    recent_actuals_usd = _convert_to_usd(recent_actuals, fx_df)

    def sum_by_category(df, category):
        return df[df['account_category'].str.lower() == category]['amount_usd'].sum()

    def sum_by_prefix(df, prefix):
        return df[df['account_category'].str.lower().str.startswith(prefix)]['amount_usd'].sum()

    monthly_summary = recent_actuals_usd.groupby('month_period').apply(lambda x: pd.Series({
        'Revenue': sum_by_category(x, 'revenue'),
        'COGS': sum_by_category(x, 'cogs'),
        'Opex': sum_by_prefix(x, 'opex:')
    })).reset_index()

    if metric == 'Gross Margin':
        # Safely calculate gross margin to avoid division by zero
        monthly_summary['Metric'] = monthly_summary.apply(
            lambda row: ((row['Revenue'] - row['COGS']) / row['Revenue']) * 100 if row['Revenue'] > 0 else 0,
            axis=1
        )
    elif metric == 'EBITDA':
        monthly_summary['Metric'] = monthly_summary['Revenue'] - monthly_summary['COGS'] - monthly_summary['Opex']
    else:
        raise ValueError(f"Unknown metric: {metric}")

    monthly_summary = monthly_summary.sort_values('month_period')
    monthly_summary['month_str'] = monthly_summary['month_period'].dt.strftime('%b %Y')
    
    return monthly_summary[['month_str', 'Metric']]


def get_opex_breakdown(actuals_df: pd.DataFrame, fx_df: pd.DataFrame, month_name: str, year: int):
    """Calculates the Opex breakdown by category for a given month."""
    try:
        target_period = pd.Period(f'{year}-{month_name}', freq='M')
    except ValueError:
        raise ValueError(f"Invalid month name: '{month_name}'. Please use a full month name (e.g., 'June').")

    opex_actuals = actuals_df[
        (actuals_df['account_category'].str.lower().str.startswith('opex:')) &
        (actuals_df['month_period'] == target_period)
    ].copy()

    if opex_actuals.empty:
        return None

    opex_usd = _convert_to_usd(opex_actuals, fx_df)
    
    # Clean up category names
    opex_usd['Category'] = opex_usd['account_category'].str.replace('Opex: ', '', case=False)
    
    category_summary = opex_usd.groupby('Category')['amount_usd'].sum().reset_index()
    category_summary.rename(columns={'amount_usd': 'Amount (USD)'}, inplace=True)
    
    return category_summary.sort_values(by='Amount (USD)', ascending=False)


def get_cash_runway(actuals_df: pd.DataFrame, cash_df: pd.DataFrame, fx_df: pd.DataFrame):
    """Calculates the current cash runway in months."""
    # 1. Calculate Average Monthly Net Burn over last 3 months
    latest_month = actuals_df['month_period'].max()
    start_period = latest_month - 2  # 3 months including the latest
    
    recent_actuals = actuals_df[actuals_df['month_period'] >= start_period].copy()
    if recent_actuals.empty:
        return {"error": "Not enough recent financial data to calculate net burn."}
        
    recent_actuals_usd = _convert_to_usd(recent_actuals, fx_df)
    
    def sum_by_category(df, category):
        return df[df['account_category'].str.lower() == category]['amount_usd'].sum()
    def sum_by_prefix(df, prefix):
        return df[df['account_category'].str.lower().str.startswith(prefix)]['amount_usd'].sum()

    monthly_summary = recent_actuals_usd.groupby('month_period').apply(lambda x: pd.Series({
        'Income': sum_by_category(x, 'revenue'),
        'Expenses': sum_by_category(x, 'cogs') + sum_by_prefix(x, 'opex:')
    })).reset_index()

    monthly_summary['net_flow'] = monthly_summary['Income'] - monthly_summary['Expenses']
    
    avg_monthly_burn = -monthly_summary['net_flow'].mean()

    if pd.isna(avg_monthly_burn):
        return {"error": "Could not determine average monthly burn."}
    if avg_monthly_burn <= 0:
        return {"runway_months": float('inf'), "latest_cash": 0, "avg_burn": avg_monthly_burn}

    # 2. Get Latest Cash Balance
    if cash_df.empty:
        return {"error": "No cash data available."}
    latest_cash_month = cash_df['month_period'].max()
    latest_cash = cash_df[cash_df['month_period'] == latest_cash_month]['cash_usd'].sum()
        
    # 3. Calculate Runway
    runway_months = latest_cash / avg_monthly_burn

    return {"runway_months": runway_months, "latest_cash": latest_cash, "avg_burn": avg_monthly_burn}

def get_cash_trend(cash_df: pd.DataFrame, last_n_months: int):
    """Calculates the cash balance over a trend period."""
    latest_month = cash_df['month_period'].max()
    start_period = latest_month - last_n_months + 1
    
    recent_cash = cash_df[cash_df['month_period'] >= start_period].copy()
    
    monthly_summary = recent_cash.groupby('month_period')['cash_usd'].sum().reset_index()
    monthly_summary = monthly_summary.sort_values('month_period')
    monthly_summary['month_str'] = monthly_summary['month_period'].dt.strftime('%b %Y')
    
    return monthly_summary[['month_str', 'cash_usd']]
