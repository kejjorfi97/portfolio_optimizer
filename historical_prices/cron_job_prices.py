# -*- coding: utf-8 -*-
"""
Created on Sun May 11 17:39:54 2025

@author: LENOVO
"""

import schedule
import pandas as pd
from datetime import datetime as dt
import os


# schedule.clear()

def scrape_cse_prices():
    if dt.today().weekday() not in [5,6]: 
        url = "https://www.casablanca-bourse.com/fr/live-market/marche-actions-groupement"
        df = pd.read_html(url, thousands=";")
        df = pd.concat(df)
        df = df[["Instrument", "Cours de référence"]]
        df.columns = ["stock", "price"]
        df.price = df.price.map(lambda x: x.replace(",",".").replace(" ","")).astype(float)
        today = dt.today()
        outputPath = r"C:\Users\LENOVO\Documents\portfolio_optimizer\historical_prices"
        fileName = f"cse_prices_{dt.today().strftime('%Y_%m_%d')}.csv" 
        filePath = os.path.join(outputPath, fileName)
        df.to_csv(filePath, index=False)
    

# scrape_cse_prices()

schedule.every().day.at('21:30').do(scrape_cse_prices)

while True:
    schedule.run_pending()