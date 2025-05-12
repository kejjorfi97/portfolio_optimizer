# -*- coding: utf-8 -*-
"""
Created on Sat May 10 13:33:46 2025

@author: LENOVO
"""

import pandas as pd
from datetime import datetime as dt
import sqlite3

conn = sqlite3.connect(r"C:\Users\LENOVO\Documents\portfolio_optimizer\users.db")

cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS stocks (
                ticker VARCHAR(50) PRIMARY KEY,
                company VARCHAR(50),
                prices NVARCHAR(4000)
                );''')

cse_prices = pd.read_csv("cse_stocks_prices.csv", index_col="date")
cse_stocks = pd.read_excel("casablanca_stocks.xlsx", index_col="Ticker").to_dict()["Instrument name"]
masi = pd.read_csv("MASI.csv",sep=";")[["Date","Price"]]
masi.columns = ["date","MASI"]
masi.date = pd.to_datetime(masi.date).map(lambda x: x.strftime("%Y-%m-%d"))
masi.MASI = masi.MASI.map(lambda x: x.replace(",","")).astype(float)
masi.set_index("date", inplace=True)
masi.dropna(inplace=True)
masi=masi.to_json(orient="table")
cur.execute("INSERT INTO stocks (ticker, company, prices)\
                VALUES(?, ?, ?)",("MASI", "MASI", masi))


for ticker in cse_prices.columns:
    ticker_prices = cse_prices[[ticker]]
    ticker_prices.dropna(inplace=True)
    prices = ticker_prices.to_json(orient="table")
    company = cse_stocks[ticker]
    cur.execute("INSERT INTO stocks (ticker, company, prices)\
                VALUES(?, ?, ?)",(ticker, company, prices))

            
conn.commit()
conn.close()
cur.execute("select prices from stocks where ticker = 'MASI';")
masi = cur.fetchone()
masi = pd.read_json(masi[0], orient="table")
masi.index = pd.to_datetime(masi.index)
masi = masi[(masi.index>=dt(2024,8,15))]
masi = masi.sort_index()
