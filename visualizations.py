# Charts: pie chart, return plot, etc.
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_pie_chart(weights: dict, title: str = "Portfolio Weights"):
    """
    Creates an interactive pie chart of portfolio weights using Plotly.
    Returns the Plotly figure for Streamlit rendering.
    """
    labels = list(weights.keys())
    sizes = list(weights.values())
    fig = px.pie(names=labels, values=sizes, title=title, hole=0.3)
    return fig


def plot_cumulative_returns(cumulative_returns: pd.DataFrame, title: str = "Cumulative Returns"):
    """
    Creates an interactive line chart of cumulative returns using Plotly.
    Returns the Plotly figure for Streamlit rendering.
    """
    fig = go.Figure()
    for column in cumulative_returns.columns:
        fig.add_trace(go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns[column],
            mode='lines',
            name=column
        ))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Cumulative Return", hovermode="x unified")
    return fig
