import os
from dotenv import load_dotenv
import sqlite3
import bcrypt
import secrets
import requests

# Load environment variables
load_dotenv()

DB_NAME = os.getenv("DB_PATH", "users.db")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_URL = os.getenv("APP_URL")


def generate_token():
    return secrets.token_urlsafe(32)

def send_activation_email(email, token):
    activation_link = f"{APP_URL}/?activate=true&email={email}&token={token}"
    html_content = f"""
    <h2>Activate Your Portfolio App Account</h2>
    <p>Click the link below to activate your account:</p>
    <a href="{activation_link}">{activation_link}</a>
    """

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": f"Portfolio App <{SENDER_EMAIL}>",
        "to": [email],
        "subject": "Activate your Portfolio App account",
        "html": html_content
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers=headers,
        json=data
    )

    return response.status_code == 202

def create_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            activation_token TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    token = generate_token()
    try:
        cursor.execute("INSERT INTO users (email, password_hash, is_active) VALUES (?, ?, ?)",
                       (email, password_hash, 1))
        conn.commit()
        # send_activation_email(email, token)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def activate_user(email, token):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT activation_token FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and row[0] == token:
        cursor.execute("UPDATE users SET is_active = 1, activation_token = NULL WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def authenticate_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, is_active FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and row[1] == 1:
        return bcrypt.checkpw(password.encode(), row[0].encode())
    return False


def get_user_id(email):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
