import streamlit as st
import pandas as pd
import numpy as np

from data_handler import load_prices, calculate_daily_returns, calculate_cumulative_returns, calculate_portfolio_return
from optimizer import optimize_portfolio
from visualizations import plot_pie_chart, plot_cumulative_returns

# -----------------------------
# Define preloaded portfolios
# -----------------------------
PRELOADED_PORTFOLIOS = {
    "Tech Core": {"AAPL": 0.25, "MSFT": 0.25, "GOOGL": 0.25, "AMZN": 0.25},
    "Dividend Mix": {"JNJ": 0.2, "PG": 0.2, "KO": 0.2, "PEP": 0.2, "MCD": 0.2},
    "Global ETF Blend": {"SPY": 0.4, "EFA": 0.3, "EEM": 0.2, "AGG": 0.1},
}

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Portfolio Optimizer", layout="wide")
st.title("📈 Portfolio Optimization Web App")

# Sidebar - Input Mode
st.sidebar.header("Portfolio Input")
input_mode = st.sidebar.radio("Choose input mode:", ("Upload CSV", "Manual Entry", "Preloaded Portfolio"))

# Load portfolio
portfolio = {}

if input_mode == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload your portfolio CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "Ticker" in df.columns and "Weight" in df.columns:
            portfolio = dict(zip(df["Ticker"], df["Weight"]))
        else:
            st.sidebar.error("CSV must have 'Ticker' and 'Weight' columns.")

elif input_mode == "Manual Entry":
    st.sidebar.subheader("Manual Portfolio Entry")
    tickers = st.sidebar.text_area("Enter tickers separated by commas", "AAPL,MSFT,GOOGL")
    weights = st.sidebar.text_area("Enter weights separated by commas", "0.3,0.4,0.3")
    
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        weight_list = [float(w.strip()) for w in weights.split(",")]
        if len(ticker_list) == len(weight_list):
            portfolio = dict(zip(ticker_list, weight_list))
        else:
            st.sidebar.error("Number of tickers and weights must match.")
    except:
        st.sidebar.error("Please enter valid tickers and numeric weights.")

elif input_mode == "Preloaded Portfolio":
    selected = st.sidebar.selectbox("Choose a portfolio:", list(PRELOADED_PORTFOLIOS.keys()))
    portfolio = PRELOADED_PORTFOLIOS[selected]

# Button to trigger optimization
if st.sidebar.button("Optimize Portfolio"):

    if not portfolio:
        st.error("Please provide a valid portfolio.")
    else:
        tickers = list(portfolio.keys())
        weights = list(portfolio.values())

        with st.spinner("Fetching price data..."):
            prices = load_prices(tickers)
            daily_returns = calculate_daily_returns(prices)
            cumulative_value, cumulative_return = calculate_cumulative_returns(daily_returns)

        with st.spinner("Optimizing portfolio..."):
            results = {}
            methods = {"Original": weights, "Max Sharpe": None, "Min Volatility": None}

            for name, m in [("Max Sharpe", "sharpe"), ("Min Volatility", "min_vol")]:
                res = optimize_portfolio(daily_returns, method=m)
                methods[name] = list(res["Optimal Weights"].values())
                results[name] = {
                    "weights": res["Optimal Weights"],
                    "metrics": {
                        "Annual Return": res["Annual Return"],
                        "Volatility": res["Volatility"],
                        "Sharpe Ratio": res["Sharpe Ratio"]
                    }
                }

        st.success("Optimization Complete!")

        # 📈 Performance Chart
        st.subheader("📈 Portfolio Performance")
        cumulative_returns_df = pd.DataFrame()
        for label, w in methods.items():
            port_returns = (daily_returns * w).sum(axis=1)
            cumulative_returns_df[label] = (1 + port_returns).cumprod() - 1

        st.plotly_chart(plot_cumulative_returns(cumulative_returns_df))

        # 📋 Metrics Table
        st.subheader("🧠 Risk & Return Metrics")

        def format_metrics(metrics):
            return {
                "Annual Return": f"{metrics['Annual Return'] * 100:.2f}%",
                "Volatility": f"{metrics['Volatility'] * 100:.2f}%",
                "Sharpe Ratio": f"{metrics['Sharpe Ratio']:.2f}"
            }

        metrics_table = {
            label: format_metrics({
                "Annual Return": results.get(label, {}).get("metrics", {}).get("Annual Return", 0) if label != "Original" else np.mean((daily_returns * weights).sum(axis=1)) * 252,
                "Volatility": results.get(label, {}).get("metrics", {}).get("Volatility", 0) if label != "Original" else np.std((daily_returns * weights).sum(axis=1)) * np.sqrt(252),
                "Sharpe Ratio": results.get(label, {}).get("metrics", {}).get("Sharpe Ratio", 0) if label != "Original" else (
                    np.mean((daily_returns * weights).sum(axis=1)) * 252 /
                    (np.std((daily_returns * weights).sum(axis=1)) * np.sqrt(252))
                )
            }) for label in methods
        }

        metrics_df = pd.DataFrame(metrics_table).T.reset_index().rename(columns={"index": "Portfolio"})
        metrics_df.set_index("Portfolio", inplace=True)
        st.write(metrics_df)

        # 📊 Portfolio Allocation Tabs
        st.subheader("📊 Portfolio Allocations")
        tab1, tab2, tab3 = st.tabs(["Original", "Max Sharpe", "Min Volatility"])

        with tab1:
            st.plotly_chart(plot_pie_chart(portfolio, title="Original Portfolio Allocation"))

        with tab2:
            st.plotly_chart(plot_pie_chart(results["Max Sharpe"]["weights"], title="Max Sharpe Allocation"))

        with tab3:
            st.plotly_chart(plot_pie_chart(results["Min Volatility"]["weights"], title="Min Volatility Allocation"))


else:
    st.info("⬅️ Upload your portfolio or select a sample on the sidebar to start optimizing.")