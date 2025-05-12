# Portfolio optimization logic (e.g., Max Sharpe, Min Vol)
import numpy as np
from scipy.optimize import minimize
import pandas as pd

def get_portfolio_performance(weights, returns, freq=252):
    """
    Calculates expected portfolio return, volatility, and Sharpe ratio.
    """
    weights = np.array(weights)
    port_return = np.mean(np.dot(returns, weights)) * freq
    port_volatility = np.std(np.dot(returns, weights)) * np.sqrt(freq)
    sharpe_ratio = port_return / port_volatility if port_volatility != 0 else 0
    return port_return, port_volatility, sharpe_ratio

def optimize_portfolio(returns: pd.DataFrame, method: str = "sharpe"):
    """
    Optimizes portfolio based on the selected method: 'sharpe' or 'min_vol'.
    Returns optimal weights and performance metrics.
    """
    num_assets = returns.shape[1]
    initial_weights = np.array([1.0 / num_assets] * num_assets)
    bounds = tuple((0, 1) for _ in range(num_assets))
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

    if method == "sharpe":
        def objective(weights):
            ret, vol, sharpe = get_portfolio_performance(weights, returns)
            return -sharpe  # We maximize Sharpe
    elif method == "min_vol":
        def objective(weights):
            _, vol, _ = get_portfolio_performance(weights, returns)
            return vol  # Minimize volatility
    else:
        raise ValueError("Invalid optimization method. Use 'sharpe' or 'min_vol'.")

    result = minimize(objective, initial_weights, method="SLSQP",
                      bounds=bounds, constraints=constraints)

    optimal_weights = result.x
    ret, vol, sharpe = get_portfolio_performance(optimal_weights, returns)

    return {
        "Optimal Weights": dict(zip(returns.columns, np.round(optimal_weights, 4))),
        "Annual Return": round(ret, 4),
        "Volatility": round(vol, 4),
        "Sharpe Ratio": round(sharpe, 4)
    }
