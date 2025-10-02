import plotly.express as px
import plotly.graph_objects as go

def plot_revenue_vs_budget(actual, budget, month, year):
    """Generates a bar chart comparing actual vs. budget revenue."""
    fig = go.Figure(data=[
        go.Bar(name='Actual', x=['Revenue'], y=[actual], marker_color='#1f77b4'),
        go.Bar(name='Budget', x=['Revenue'], y=[budget], marker_color='#ff7f0e')
    ])
    fig.update_layout(
        title_text=f'Revenue vs. Budget for {month} {year}',
        yaxis_title='Amount (USD)',
        title_x=0.5,
        barmode='group'
    )
    return fig

def plot_metric_trend(df, metric_name):
    """Generates a line chart for a given metric trend."""
    fig = px.line(
        df, 
        x='month_str', 
        y=df.columns[1],  # Assumes the metric is the second column
        title=f'{metric_name} Trend',
        labels={'month_str': 'Month', df.columns[1]: metric_name},
        markers=True
    )
    fig.update_traces(line_color='#1f77b4', marker=dict(color='#1f77b4', size=8))
    fig.update_layout(title_x=0.5)
    if '%' in metric_name:
        fig.update_layout(yaxis_ticksuffix='%')
    return fig

def plot_opex_breakdown(df, month, year):
    """Generates a pie chart for the Opex breakdown."""
    fig = px.pie(
        df,
        values='Amount (USD)', 
        names='Category',
        title=f'Opex Breakdown for {month} {year}', 
        hole=.3,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_cash_trend(df):
    """Generates a line chart for the cash trend."""
    fig = px.line(
        df, 
        x='month_str', 
        y='cash_usd',
        title='Cash Balance Trend (Last 6 Months)',
        labels={'month_str': 'Month', 'cash_usd': 'Cash (USD)'},
        markers=True
    )
    fig.update_traces(line_color='#1f77b4', marker=dict(color='#1f77b4', size=8))
    fig.update_layout(title_x=0.5)
    return fig