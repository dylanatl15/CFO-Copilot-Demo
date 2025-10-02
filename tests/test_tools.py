import pytest
import pandas as pd
from agent import tools

# --- Mock Data Fixtures ---

@pytest.fixture
def mock_data_frames():
    """Creates a dictionary of mock DataFrames for use in tests."""
    actuals_data = {
        'month': ['2025-06-30', '2025-06-30', '2025-05-31', '2025-05-31', '2025-04-30', '2025-04-30'],
        'account_category': ['revenue', 'cogs', 'revenue', 'cogs', 'revenue', 'cogs'],
        'amount': [2000, 800, 1800, 700, 1600, 600],
        'currency': ['USD', 'USD', 'CAD', 'CAD', 'USD', 'USD']
    }
    budget_data = {
        'month': ['2025-06-30'],
        'account_category': ['revenue'],
        'amount': [1900],
        'currency': ['USD']
    }
    cash_data = {
        'month': ['2025-06-30'],
        'cash_usd': [5000]
    }
    fx_data = {
        'month': ['2025-05-31'],
        'currency': ['CAD'],
        'rate_to_usd': [1.25]
    }
    
    dfs = {
        "actuals_df": pd.DataFrame(actuals_data),
        "budget_df": pd.DataFrame(budget_data),
        "cash_df": pd.DataFrame(cash_data),
        "fx_df": pd.DataFrame(fx_data)
    }

    # Convert month columns to period objects, similar to load_data()
    for name, df in dfs.items():
        df['month_period'] = pd.to_datetime(df['month']).dt.to_period('M')

    return dfs


# --- Tests ---

def test_get_revenue_vs_budget(mock_data_frames):
    """
    Tests the revenue vs. budget calculation for a specific month.
    """
    result = tools.get_revenue_vs_budget(
        mock_data_frames['actuals_df'],
        mock_data_frames['budget_df'],
        mock_data_frames['fx_df'],
        month_name='June',
        year=2025
    )
    
    assert result is not None
    assert result['actual'] == 2000  # From June data
    assert result['budget'] == 1900 # From June data

def test_get_revenue_vs_budget_with_fx_conversion(mock_data_frames):
    """
    Tests the revenue vs. budget calculation for a month requiring FX conversion.
    """
    result = tools.get_revenue_vs_budget(
        mock_data_frames['actuals_df'],
        mock_data_frames['budget_df'],
        mock_data_frames['fx_df'],
        month_name='May',
        year=2025
    )
    
    assert result is not None
    # Actuals: 1800 CAD / 1.25 = 1440 USD
    # Budget: No budget data for May, so should be 0
    assert result['actual'] == pytest.approx(1440)
    assert result['budget'] == 0

def test_get_cash_runway(mock_data_frames):
    """
    Tests the cash runway calculation.
    - June: Rev=2000, COGS=800 -> Net = 1200
    - May: Rev=1800 CAD (1440 USD), COGS=700 CAD (560 USD) -> Net = 880
    - April: Rev=1600, COGS=600 -> Net = 1000
    - Average Burn: -((1200 + 880 + 1000) / 3) = -1026.67 (i.e., it's a profit)
    - Since the company is profitable, runway should be infinite.
    """
    result = tools.get_cash_runway(
        mock_data_frames['actuals_df'],
        mock_data_frames['cash_df'],
        mock_data_frames['fx_df']
    )
    
    assert result['runway_months'] == float('inf')
    assert result['avg_burn'] < 0