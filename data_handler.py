import yfinance as yf
import pandas as pd
import numpy as np

def load_prices(tickers, start_date="2019-01-01"):
    """
    Fetches historical adjusted close prices for a list of tickers from Yahoo Finance.
    """
    data = yf.download(tickers, start=start_date)
    if isinstance(data, pd.Series):
        data = data.to_frame()
    data = data[[('Close', ticker) for ticker in tickers]]
    data.columns = data.columns.droplevel()
    return data.dropna()
def calculate_daily_returns(prices):
    """
    Computes daily returns from price data.
    """
    return prices.pct_change().dropna()

def calculate_cumulative_returns(daily_returns):
    """
    Computes both cumulative value and cumulative return.
    Returns:
        - cumulative_value: Value of $1 over time
        - cumulative_return: Cumulative percentage return over time
    """
    cumulative_value = (1 + daily_returns).cumprod()
    cumulative_return = cumulative_value - 1
    return cumulative_value, cumulative_return

def calculate_portfolio_return(daily_returns, weights):
    """
    Calculates portfolio daily return given individual asset returns and weights.
    """
    weights = np.array(weights)
    return (daily_returns * weights).sum(axis=1)

def calculate_risk_metrics(daily_returns, weights, freq=252):
    """
    Computes key risk metrics: annualized return, volatility, and Sharpe ratio.
    """
    port_returns = calculate_portfolio_return(daily_returns, weights)
    mean_return = port_returns.mean() * freq
    volatility = port_returns.std() * np.sqrt(freq)
    sharpe_ratio = mean_return / volatility if volatility != 0 else 0
    return {
        "Annual Return": round(mean_return, 4),
        "Volatility": round(volatility, 4),
        "Sharpe Ratio": round(sharpe_ratio, 4)
    }
