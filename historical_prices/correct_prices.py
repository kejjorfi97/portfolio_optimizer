# -*- coding: utf-8 -*-
"""
Created on Mon May 12 23:14:32 2025

@author: LENOVO
"""

import pandas as pd
from datetime import datetime as dt
import sqlite3

conn = sqlite3.connect(r"C:\Users\LENOVO\Documents\portfolio_optimizer\users.db")

cur = conn.cursor()



cur.execute("select prices from stocks;")

prices = cur.fetchall()

bigDf = []

conn.close()

for item in prices:
    p = item[0]
    df = pd.read_json(p, orient="table")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # df = df[df.index >= dt(2012,1,1)]
    # new_price = df.to_json(orient='table')
    # ticker = df.columns[0]
    # cur.execute(
    #     "UPDATE stocks SET prices = ? WHERE ticker = ?",
    #     (new_price, ticker)
    # )
    bigDf.append(df)

bigDf = pd.concat(bigDf, axis=1)

url = "https://www.casablanca-bourse.com/fr/live-market/marche-actions-groupement"

cse = pd.read_html(url, thousands=";")

cse = pd.concat(cse)

cse = cse[["Instrument","Dernier cours"]]

cse.columns = ["stock","price"]

cse.price = cse.price.map(lambda x: x.replace(",",".").replace(" ","")).astype(float)

cse.set_index("stock", inplace=True)

cur.execute("select prices, company from stocks;")
data = cur.fetchall()
for item in data:
    price = item[0]
    name = item[1]
    try:
        df = pd.read_json(price, orient="table")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        today_price = pd.DataFrame([[dt(2025,5,12), cse.loc[name].iat[0]]], columns = ["date", df.columns[0]])
        today_price.set_index("date", inplace=True)
        df = pd.concat([df, today_price])
        new_price = df.to_json(orient='table')
        ticker = df.columns[0]
        cur.execute(
            "UPDATE stocks SET prices = ? WHERE ticker = ?",
            (new_price, ticker)
        )
    except Exception as e:
        print(str(e),"####", name)
# import streamlit as st
# import matplotlib.pyplot as plt

# for ticker in bigDf.columns:
#     st.subheader(f"Price History for {ticker}")
#     fig, ax = plt.subplots()
#     ax.plot(bigDf.index, bigDf[ticker])
#     ax.set_title(f"Price History: {ticker}")
#     ax.set_xlabel("Date")
#     ax.set_ylabel("Price (MAD)")
#     st.pyplot(fig)
today_price = pd.DataFrame([[dt(2025,5,12), 18033.08]], columns = ["date", "MASI"])
today_price.set_index("date", inplace=True)
p = bigDf[["MASI"]].copy()
p = p.head(-1)
df = pd.concat([p, today_price])
new_price = df.to_json(orient='table')
cur.execute(
    "UPDATE stocks SET prices = ? WHERE ticker = ?",
    (new_price, "MASI")
)






