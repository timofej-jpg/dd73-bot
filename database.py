import sqlite3
from datetime import datetime, timedelta

DB_NAME = "fishstats.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_pro BOOLEAN DEFAULT 0,
            trial_used BOOLEAN DEFAULT 0,
            pro_expires_at DATETIME,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fish_type TEXT,
            weight REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_or_register_user(user_id: int, username: str, first_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, is_pro, trial_used, pro_expires_at FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username or "", first_name or "")
        )
        conn.commit()
        cursor.execute("SELECT user_id, is_pro, trial_used, pro_expires_at FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def activate_trial(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT trial_used FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    
    if res and not res[0]:
        expires_at = datetime.now() + timedelta(days=1)
        cursor.execute(
            "UPDATE users SET is_pro = 1, trial_used = 1, pro_expires_at = ? WHERE user_id = ?",
            (expires_at, user_id)
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def extend_pro(user_id: int, days: int = 30):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=days)
    cursor.execute(
        "UPDATE users SET is_pro = 1, pro_expires_at = ? WHERE user_id = ?",
        (expires_at, user_id)
    )
    conn.commit()
    conn.close()

