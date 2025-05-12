import pandas as pd
import numpy as np
from datetime import datetime as dt
# import yfinance as yf
from portfolio_db import get_stocks_data, get_holdings, get_prices

def get_portfolio_holdings(portfolio_id):
    rows = get_holdings(portfolio_id)
    holdings = []
    for ticker, entry_date, entry_price, quantity in rows:
        holdings.append({
            "ticker": ticker.upper(),
            "entry_date": pd.to_datetime(entry_date),
            "entry_price": float(entry_price),
            "quantity": float(quantity)
        })
    return holdings

def fetch_historical_prices(tickers: tuple, start_date: dt):
    try:
        db_extract = get_prices(tickers)
        prices = pd.concat([pd.read_json(item[0], orient="table") for item in db_extract], axis=1)
        prices = prices.ffill().fillna(0)
        prices.index = pd.to_datetime(prices.index)
        prices = prices.sort_index()
        prices = prices[(prices.index >= start_date)]
        print(prices)
        return prices
    except Exception as e:
        print(str(e))
        return pd.DataFrame()



def compute_nav_over_time(holdings, prices_df):
    portfolio_df = pd.DataFrame(index=prices_df.index)
    for h in holdings:
        ticker = h["ticker"]
        quantity = h["quantity"]
        entry_date = h["entry_date"]
        valid_prices = prices_df[ticker][prices_df.index >= entry_date]
        position_value = valid_prices * quantity
        full_series = pd.Series(0, index=prices_df.index)
        full_series.loc[position_value.index] = position_value
        portfolio_df[ticker] = full_series
    portfolio_df["NAV"] = portfolio_df.sum(axis=1)
    return portfolio_df[["NAV"]]

def get_holdings_summary(holdings, prices_df, portfolio_currency):
    summary = []
    latest_prices = prices_df.iloc[-1]
    total_value = 0
    # print(holdings)
    # First compute total portfolio value
    for h in holdings:
        ticker = h["ticker"]
        qty = h["quantity"]
        current_price = latest_prices[ticker]
        total_value += qty * current_price

    # Compute details per holding
    for h in holdings:
        ticker = h["ticker"]
        entry_price = h["entry_price"]
        qty = h["quantity"]
        entry_date = h["entry_date"].strftime("%Y-%m-%d")
        current_price = latest_prices[ticker]
        value = qty * current_price
        pnl = (current_price - entry_price) * qty
        stock_performance = (current_price - entry_price) / entry_price
        weight = value / total_value if total_value else 0

        summary.append({
            "Ticker": ticker,
            "Entry Price": round(entry_price, 2),
            "Current Price": round(current_price, 2),
            "Quantity": qty,
            "Stock NAV": round(current_price * qty, 2),
            "Entry Date": entry_date,
            "P&L": f"{round(pnl, 2)} {portfolio_currency}",
            "Stock performance": f"{stock_performance * 100:.2f}%",
            "Weight": f"{weight * 100:.2f}%"
        })

    return pd.DataFrame(summary)

def compute_weighted_performance(holdings, prices_df):
    """
    Compute daily portfolio returns using weighted returns of each holding.
    Returns a DataFrame with 'Portfolio' column (% cumulative return).
    """
    if prices_df.shape[0] > 0:
        returns_df = prices_df.pct_change().fillna(0)
        position_values = pd.DataFrame(index=returns_df.index)

        for h in holdings:
            ticker = h["ticker"]
            qty = h["quantity"]
            entry_date = h["entry_date"]
            position_value = prices_df[ticker] * qty
            mask = prices_df.index >= entry_date
            full_series = pd.Series(0, index=prices_df.index)
            full_series[mask] = position_value[mask]
            position_values[ticker] = full_series

        total_value = position_values.sum(axis=1)
        weights_df = position_values.div(total_value, axis=0).fillna(0)

        weighted_returns = (returns_df * weights_df).sum(axis=1)
        performance = (1 + weighted_returns).cumprod() - 1
        return performance.to_frame(name="Portfolio")
    else:
        raise Exception("Prices table is empty")

def compute_benchmark_nav(benchmark_tickers, start_date):
    """
    Fetch benchmark prices and return cumulative % performance for each.
    """
    prices = fetch_historical_prices(tuple(benchmark_tickers), start_date)
    # performance = (1 + prices.pct_change().fillna(0)).cumprod() - 1
    rebased_benchmarks = prices.apply(lambda x: x / x.iloc[0] * 100)
    return rebased_benchmarks

def compute_weighted_nav(stock_prices, holdings):
    """
    Build a TWR-like NAV series starting at 100,
    using user-entered entry prices at purchase date,
    and historical prices afterward.
    
    stock_prices: pd.DataFrame, daily close prices with tickers as columns, Date as index
    holdings: list of dicts, each with keys: 'ticker', 'entry_date' (datetime.date), 'entry_price', 'quantity'
    """

    stock_returns = stock_prices.pct_change().fillna(0)

    # Initialize
    nav_series = pd.Series(index=stock_prices.index, dtype=float)
    portfolio_weights = {}  # ticker -> weight
    active_stocks = {}      # ticker -> quantity
    entry_prices = {}       # ticker -> entry price
    starting_nav = 100
    nav_series.iloc[0] = starting_nav

    # Create lookup for entry dates
    purchase_lookup = {}
    for h in holdings:
        purchase_lookup.setdefault(h["entry_date"], []).append(h)

    prev_nav = starting_nav

    for i, today in enumerate(stock_prices.index):
        # print(i, today)
        
        # Step 1: Check if new stock purchased today
        if today in purchase_lookup.keys():
            for new_purchase in purchase_lookup[today]:
                ticker = new_purchase["ticker"]
                quantity = new_purchase["quantity"]
                price = new_purchase["entry_price"]

                if ticker not in active_stocks:
                    active_stocks[ticker] = 0
                active_stocks[ticker] += quantity
                entry_prices[ticker] = price  # record user-entered price

            # Recompute weights based on NAVs
            navs = {}
            total_value = 0
            for ticker, qty in active_stocks.items():
                if today == holdings[0]["entry_date"]:  # on very first purchase
                    current_price = entry_prices[ticker]
                elif ticker in entry_prices and today == next((h["entry_date"] for h in holdings if h["ticker"] == ticker), None):
                    current_price = entry_prices[ticker]
                else:
                    current_price = stock_prices.at[today, ticker]

                nav_stock = qty * current_price
                navs[ticker] = nav_stock
                total_value += nav_stock

            portfolio_weights = {ticker: navs[ticker] / total_value for ticker in active_stocks}

        # Step 2: Compute today's portfolio return
        weighted_return = 0
        for ticker, weight in portfolio_weights.items():
            weighted_return += weight * stock_returns.at[today, ticker]

        # Step 3: Update NAV
        if i > 0:  # skip first day
            prev_nav = prev_nav * (1 + weighted_return)
            nav_series.iloc[i] = prev_nav
    return nav_series