import re
import pandas as pd
from . import tools, plotting

def route_query(query: str) -> dict:
    """
    Interprets a user's query and routes it to the appropriate tool and plotting function.
    """
    query_lower = query.lower()

    # --- Load Data ---
    try:
        actuals_df, budget_df, cash_df, fx_df = tools.load_data()
    except Exception as e:
        return {"text": f"Error loading data: {e}", "chart": None}

    # --- Entity Extraction: Date ---
    month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', query_lower)
    year_match = re.search(r'(\d{4})', query_lower)
    
    month_name = month_match.group(1).capitalize() if month_match else None
    # Default to the latest year in the data if not specified
    year = int(year_match.group(1)) if year_match else pd.to_datetime(actuals_df['month']).dt.year.max()

    # --- Intent Routing ---

    # Intent: Revenue vs Budget
    if 'revenue' in query_lower and 'budget' in query_lower:
        if not month_name or not year:
            return {"text": "Please specify a month and year for revenue vs. budget analysis.", "chart": None}
        
        data = tools.get_revenue_vs_budget(actuals_df, budget_df, fx_df, month_name, year)
        if data is None:
            return {"text": f"No revenue data found for {month_name} {year}.", "chart": None}

        actual_rev_m = data['actual'] / 1_000_000
        budget_rev_m = data['budget'] / 1_000_000
        variance = data['actual'] - data['budget']
        variance_m = variance / 1_000_000

        text_response = (
            f"### Revenue vs. Budget for {month_name} {year}:\n"
            f"- **Actual Revenue:** ${actual_rev_m:.2f}M\n"
            f"- **Budgeted Revenue:** ${budget_rev_m:.2f}M\n"
            f"- **Variance:** ${variance_m:.2f}M"
        )
        chart = plotting.plot_revenue_vs_budget(data['actual'], data['budget'], month_name, year)
        return {"text": text_response, "chart": chart}

    # Intent: Gross Margin or EBITDA Trend
    if ('gross margin' in query_lower or 'ebitda' in query_lower) and 'trend' in query_lower:
        metric = 'Gross Margin' if 'gross margin' in query_lower else 'EBITDA'
        num_months_match = re.search(r'(\d+)\s+months', query_lower)
        num_months = int(num_months_match.group(1)) if num_months_match else 6

        df_trend = tools.get_financial_metric_trend(actuals_df, fx_df, metric, num_months)
        chart_metric_name = f"{metric} %" if metric == 'Gross Margin' else f"{metric} (USD)"
        chart = plotting.plot_metric_trend(df_trend, chart_metric_name)
        
        text_response = f"Here is the {metric} trend for the last {num_months} months."
        return {"text": text_response, "chart": chart}

    # Intent: Opex Breakdown
    if 'opex' in query_lower and ('breakdown' in query_lower or 'category' in query_lower):
        if not month_name or not year:
            return {"text": "Please specify a month and year for the Opex breakdown.", "chart": None}

        df_opex = tools.get_opex_breakdown(actuals_df, fx_df, month_name, year)
        if df_opex is None or df_opex.empty:
            return {"text": f"No Opex data found for {month_name} {year}.", "chart": None}

        total_opex_m = df_opex['Amount (USD)'].sum() / 1_000_000
        text_response = f"Total Opex for {month_name} {year} was **${total_opex_m:.2f}M**. Here is the breakdown by category."
        chart = plotting.plot_opex_breakdown(df_opex, month_name, year)
        return {"text": text_response, "chart": chart}

    # Intent: Cash Runway
    if 'cash runway' in query_lower:
        data = tools.get_cash_runway(actuals_df, cash_df, fx_df)
        if "error" in data:
            return {"text": data["error"], "chart": None}

        if data['runway_months'] == float('inf'):
            text_response = (
                f"### 💰 Cash Runway Analysis\n"
                f"Congratulations! The company is profitable or cash-neutral based on the last 3 months of data. "
                f"Your average monthly net cash flow was **${-data['avg_burn']:,.0f}**."
            )
        else:
            text_response = (
                f"### 💰 Cash Runway Analysis\n"
                f"- **Current Cash Balance:** ${data['latest_cash']:,.0f} USD\n"
                f"- **Avg. 3-Month Net Burn:** ${data['avg_burn']:,.0f} USD per month\n"
                f"- **Estimated Cash Runway:** **{data['runway_months']:.1f} months**"
            )
        return {"text": text_response, "chart": None}

    # --- Fallback Response ---
    return {
        "text": "Sorry, I can't answer that question. Please try one of the sample questions or ask about: \n- Revenue vs. Budget (for a specific month) \n- Gross Margin or EBITDA trend (for the last X months) \n- Opex breakdown (for a specific month) \n- Cash Runway",
        "chart": None
    }