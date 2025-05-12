# %%
import sqlite3
from datetime import datetime
import os

DB_NAME = os.getenv("DB_PATH", "users.db")

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)
# %%
def init_portfolio_tables():
    conn = get_connection()
    cur = conn.cursor()

    # Portfolios table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            currency TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Holdings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portfolio_id INTEGER,
        ticker TEXT,
        entry_date TEXT,
        entry_price REAL,
        quantity REAL,
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
    )
""")
    # stocks table
    cur.execute("""CREATE TABLE IF NOT EXISTS stocks (
                ticker VARCHAR(50) PRIMARY KEY,
                company VARCHAR(50),
                prices NVARCHAR(4000)
                );
    """)


    # # Cash table
    # cur.execute('''
    #     CREATE TABLE IF NOT EXISTS cash (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         portfolio_id INTEGER NOT NULL,
    #         currency TEXT NOT NULL,
    #         amount REAL NOT NULL
    #     )
    # ''')

    conn.commit()
    conn.close()

# CRUD Functions

def create_portfolio(user_id, name, currency):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO portfolios (user_id, name, currency) VALUES (?, ?, ?)", (user_id, name, currency))
    conn.commit()
    portfolio_id = cur.lastrowid
    conn.close()
    return portfolio_id

def add_holding(portfolio_id, ticker, entry_date, entry_price, quantity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO holdings (portfolio_id, ticker, entry_date, entry_price, quantity) VALUES (?, ?, ?, ?, ?)", 
                (portfolio_id, ticker, entry_date, entry_price, quantity))
    conn.commit()
    conn.close()

def get_holdings(portfolio_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker, entry_date, entry_price, quantity FROM holdings WHERE portfolio_id = ?", (portfolio_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_portfolio(portfolio_id):
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Delete all holdings for that portfolio
    cursor.execute("DELETE FROM holdings WHERE portfolio_id = ?", (portfolio_id,))
    # Delete the portfolio itself
    cursor.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))

    conn.commit()
    conn.close()

def get_portfolios_by_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM portfolios WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_portfolio_by_id(portfolio_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, currency FROM portfolios WHERE id = ?", (portfolio_id,))
    rows = cur.fetchone()
    conn.close()
    return rows
# %%
def get_prices(tickers):
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ','.join(['?'] * len(tickers)) 
    cur.execute(
        f"SELECT prices FROM stocks WHERE ticker in ({placeholders})",
        tickers
    )
    rows = cur.fetchall()
    conn.close()
    return rows
# %%
def get_stocks_data(stocks):
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ','.join(['?'] * len(stocks)) 
    cur.execute(
        f"SELECT ticker, company, prices FROM stocks WHERE company in ({placeholders})",
        stocks
    )
    rows = cur.fetchall()
    conn.close()
    return rows
# %%
def get_all_stocks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT ticker, company FROM stocks; ")
    rows = cur.fetchall()
    conn.close()
    return rows

# %%
