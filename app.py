
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from auth import init_db, create_user, authenticate_user, get_user_id
from portfolio_db import (
    init_portfolio_tables, get_portfolios_by_user,
    create_portfolio, add_holding,
    delete_portfolio, get_portfolio_by_id,
    get_stocks_data, get_all_stocks
)
from nav import (
    get_portfolio_holdings, fetch_historical_prices,
    compute_nav_over_time, get_holdings_summary,
    compute_weighted_performance, compute_benchmark_nav,
    compute_weighted_nav
)

import streamlit as st



def render_holdings_table(summary: pd.DataFrame, portfolio_currency: str):
    # Format columns
    # summary["P&L"] = summary["P&L"].apply(lambda x: f"{x:,.2f} " + portfolio_currency)
    # summary["P&L"] = pd.to_numeric(summary["P&L"]).apply(lambda x: f"{x:,.2f} {portfolio_currency}")
    # summary["Stock performance"] = pd.to_numeric(summary["Stock performance"], errors="coerce").apply(lambda x: f"{x:.2f}%")
    # summary["Weight"] = pd.to_numeric(summary["Weight"], errors="coerce").apply(lambda x: f"{x:.2f}%")

    # summary["Stock performance"] = summary["Stock performance"].apply(lambda x: f"{x:.2f}%")
    # summary["Weight"] = summary["Weight"].apply(lambda x: f"{x:.2f}%")
    
    # Optional: round price columns
    # summary["Entry Price"] = summary["Entry Price"].round(2)
    # summary["Current Price"] = summary["Current Price"].round(2)
    # summary.reset_index(inplace=True)
    summary.set_index("Ticker", inplace=True)
    # print(summary.columns)

    # Style function for P&L and Stock performance
    def highlight_perf(val):
        try:
            val_float = float(val.replace('%', '').replace(f' {portfolio_currency}', '').replace(',', ''))
            if val_float > 0:
                return 'color: green;'
            elif val_float < 0:
                return 'color: red;'
        except:
            pass
        return ''

    # Align numbers and apply styles
    styled_df = summary.style\
        .applymap(highlight_perf, subset=["P&L", "Stock performance"])
        # .set_properties(**{
        #     "text-align": "right",
        #     "font-size": "14px"
        # }, subset=["Entry Price", "Current Price", "Quantity", "P&L", "Stock performance", "Weight"])\
        # .set_properties(**{
        #     "font-weight": "bold"
        # }, subset=["Ticker"])
    
    # Display in Streamlit
    st.markdown("### 📋 Holdings Overview")
    st.dataframe(styled_df, use_container_width=True)


# Init
init_db()
init_portfolio_tables()
st.set_page_config(page_title="Portfolio Tracker", layout="wide")

# Session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
if "active_portfolio_id" not in st.session_state:
    st.session_state.active_portfolio_id = None

# Greeting
user_email = st.session_state.get("user_email", "")
if user_email:
    username = user_email.split("@")[0]
    st.markdown(f"<div style='text-align:right;'>👋 Hello **{username}**</div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📊 Portfolio App")



if not st.session_state.logged_in:
    st.markdown(
    """
    # 📈 Track Your Moroccan Stock Portfolio Instantly

    **Live price updates. Clear performance tracking.  
    No spreadsheets. No guesswork.**

    ---
    """
    )

    if st.button("🚀 Join Early Access"):
        st.success("✅ Thank you! We'll notify you as soon as we open.")


    st.sidebar.subheader("🔐 Login or Sign Up")
    tab1, tab2 = st.sidebar.tabs(["Login", "Sign Up"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if authenticate_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_id = get_user_id(email)
                st.session_state.user_email = email
                st.rerun()
            else:
                st.sidebar.error("Invalid email or password.")
    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            if create_user(new_email, new_password):
                st.success("Account created! Please log in.")
            else:
                st.sidebar.error("Email already exists.")
else:
    st.sidebar.subheader("📁 Manage Portfolios")
    with st.sidebar.expander("➕ Create New Portfolio"):
        new_portfolio_name = st.text_input("Portfolio Name", key="new_portfolio")
        new_portfolio_currency = st.text_input("Portfolio Currency", key="new_portfolio_currency")
        if st.button("Create Portfolio"):
            if new_portfolio_name:
                new_id = create_portfolio(st.session_state.user_id, new_portfolio_name, new_portfolio_currency)
                st.session_state.active_portfolio_id = new_id
                st.query_params.clear()
                st.rerun()
            else:
                st.warning("Please enter a portfolio name.")

    portfolios = get_portfolios_by_user(st.session_state.user_id)
    if portfolios:
        name_to_id = {name: pid for pid, name in portfolios}
        default_index = list(name_to_id.values()).index(st.session_state.active_portfolio_id) if st.session_state.active_portfolio_id in name_to_id.values() else 0
        selected_name = st.sidebar.selectbox("Open Existing Portfolio", list(name_to_id.keys()), index=default_index)
        selected_id = name_to_id[selected_name]
        if st.session_state.active_portfolio_id != selected_id:
            st.session_state.active_portfolio_id = selected_id
            st.rerun()
        st.sidebar.success(f"Opened: {selected_name}")
        # if st.sidebar.button("➖ Delete Portfolio"):
        #     delete_portfolio(st.session_state.active_portfolio_id)
        #     st.rerun()


    else:
        st.sidebar.info("No portfolios yet. Create one to get started.")

    st.sidebar.markdown("### 📝 Add Holdings")
    st.sidebar.markdown(
    """
    **Disclaimer:**  
    _This version assumes all stocks entered are still held in the portfolio (buy-and-hold).  
    Sell dates and partial exits will be added in a future update._
    """
)

    if st.session_state.active_portfolio_id:
        all_stocks_data = get_all_stocks()
        company_names = [item[1] for item in all_stocks_data]
        stocks_mapping = {item[1]: item[0] for item in all_stocks_data}
        with st.sidebar.expander("➕ Manual Entry"):
            stock = st.selectbox("Stock", company_names)
            ticker = stocks_mapping[stock]
            entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01, key="manual_price")
            quantity = st.number_input("Quantity", min_value=0.0, step=0.01, key="manual_qty")
            entry_date = st.date_input("Entry Date", value=datetime.today(), key="manual_date")
            if st.button("Add Ticker"):
                if ticker and entry_price > 0 and quantity > 0:
                    add_holding(st.session_state.active_portfolio_id, ticker.upper(), str(entry_date), entry_price, quantity)
                    st.success(f"{ticker.upper()} added successfully!")
                    st.rerun()
                else:
                    st.warning("Please fill all fields.")

        # with st.sidebar.expander("📄 Upload CSV"):
        #     st.markdown("CSV must have columns: `Ticker`, `Entry Date`, `Entry Price`, `Quantity`")
        #     uploaded_file = st.file_uploader("Upload CSV", type="csv")
        #     if "csv_uploaded" not in st.session_state:
        #         st.session_state.csv_uploaded = False
        #     # print("########", st.session_state.csv_uploaded)
        #     if uploaded_file and not st.session_state.csv_uploaded:
        #         try:
        #             df = pd.read_csv(uploaded_file)
        #             required_cols = {"Ticker", "Entry Date", "Entry Price", "Quantity"}
        #             if not required_cols.issubset(df.columns):
        #                 st.error("CSV missing required columns.")
        #             else:
        #                 for _, row in df.iterrows():
        #                     add_holding(
        #                         st.session_state.active_portfolio_id,
        #                         row["Ticker"],
        #                         row["Entry Date"],
        #                         float(row["Entry Price"]),
        #                         float(row["Quantity"])
        #                     )
        #                 st.success("Tickers added from CSV!")
        #                 st.session_state.csv_uploaded = True
        #                 st.rerun()
        #         except Exception as e:
        #             st.error(f"Error processing CSV: {e}")

    # Benchmarks
    st.sidebar.markdown("### 📊 Compare to Benchmarks")
    benchmark_map = {"MASI": "MASI"}
    # # Add user's other portfolios as benchmarks
    # for name, pid in portfolios:
    #     if pid != st.session_state.active_portfolio_id:
    #         benchmark_map[f"(Portfolio) {name}"] = pid  # store by ID
    user_choices = st.sidebar.multiselect(
        "Select Benchmarks:",
        options=list(benchmark_map.keys()),
        default=["MASI"]
    )
    benchmark_tickers = [benchmark_map[c] for c in user_choices]

    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.active_portfolio_id = None
        st.rerun()

    if st.button("START"):
        # MAIN PAGE
        # st.subheader("📈 Portfolio Dashboard")
        if st.session_state.active_portfolio_id:
            holdings = get_portfolio_holdings(st.session_state.active_portfolio_id)
            if holdings:
                tickers = list({h["ticker"] for h in holdings})
                start_date = min(h["entry_date"] for h in holdings)
                prices_df = fetch_historical_prices(tuple(tickers), start_date)
                # Portfolio performance
                # portfolio_perf = compute_weighted_performance(holdings, prices_df)
                # nav_df = compute_nav_over_time(holdings, prices_df)
                # nav_series = nav_df['NAV']
                # cash_flow_dates = [h["entry_date"].date() for h in holdings]
                nav_df = compute_weighted_nav(prices_df, holdings)
                performance = (nav_df.iat[-1] / nav_df.iat[0]) - 1
                # Benchmark performance
                benchmark_nav = compute_benchmark_nav(benchmark_tickers, start_date)
                # combined_df = twrr_df.join(benchmark_nav, how="outer").fillna(method="ffill")


                portfolio_name, portfolio_currency = get_portfolio_by_id(st.session_state.active_portfolio_id)

                

                st.markdown(f"# 📈 {portfolio_name}")
                summary = get_holdings_summary(holdings, prices_df, portfolio_currency)
                # summary.set_index("Ticker", inplace=True)
                nav = (summary["Current Price"] * summary["Quantity"]).sum()
                ptf_pnl = ((summary["Current Price"] - summary["Entry Price"]) * summary.Quantity).sum()
                ptf_perf = ptf_pnl / ((summary["Entry Price"] * summary["Quantity"]).sum())
                st.markdown(
                f"""
                <div style='font-size: 1.2em; margin-bottom: 0.5em;'>
                    <strong>Balance:</strong> {nav:,.2f} {portfolio_currency} &nbsp;&nbsp;|&nbsp;&nbsp;
                    <strong>P&L:</strong> <span style='color:{"green" if ptf_pnl >= 0 else "red"};'>{ptf_pnl:+,.2f} {portfolio_currency}</span> &nbsp;&nbsp;|&nbsp;&nbsp;
                    <strong>Performance:</strong> <span style='color:{"green" if performance >= 0 else "red"};'>{performance * 100:+.2f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )


                render_holdings_table(summary, portfolio_currency)
                # st.dataframe(summary)
                # Plot performance comparison
                st.markdown("### 📉 Performance Comparison")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=nav_df.index, y=nav_df, mode='lines', name="Portfolio Net Asset Value (Rebased)"))
                fig.add_trace(go.Scatter(x=benchmark_nav.index, y=benchmark_nav['MASI'], mode='lines', name="MASI (Rebased)"))

                # Optionally plot benchmarks rebased to 100 here

                fig.update_layout(title="Time Weighted Net Asset Value", xaxis_title="Date", yaxis_title="Net Asset Value")
                st.plotly_chart(fig, use_container_width=True)
                # fig = go.Figure()
                # for col in combined_df.columns:
                #     fig.add_trace(go.Scatter(
                #         x=combined_df.index,
                #         y=combined_df[col] * 100,
                #         mode='lines',
                #         name=col
                #     ))
                # fig.update_layout(title="Portfolio vs Benchmarks", xaxis_title="Date", yaxis_title="Performance (%)")
                # st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tickers added to this portfolio yet.")
        else:
            st.info("Please create or select a portfolio.")
