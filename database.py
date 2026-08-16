import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List

DB_PATH = "bots.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    c = conn.cursor()
    
    # Bots table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            bot_token TEXT,
            bot_type TEXT,
            main_file TEXT,
            status TEXT,
            process_id TEXT,
            created_at TIMESTAMP,
            last_started TIMESTAMP,
            last_stopped TIMESTAMP,
            error_message TEXT
        )
    ''')
    
    # Users table for quotas
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            max_bots INTEGER DEFAULT 5,
            created_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_bot(bot_id: str, user_id: int, bot_token: str, bot_type: str, main_file: str):
    """Add new bot to database"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bots (id, user_id, bot_token, bot_type, main_file, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (bot_id, user_id, bot_token, bot_type, main_file, 'stopped', datetime.now()))
    conn.commit()
    conn.close()

def update_bot_status(bot_id: str, status: str, process_id: str = None, error: str = None):
    """Update bot status"""
    conn = get_db()
    c = conn.cursor()
    
    updates = []
    params = []
    
    updates.append("status = ?")
    params.append(status)
    
    if process_id is not None:
        updates.append("process_id = ?")
        params.append(process_id)
    
    if error is not None:
        updates.append("error_message = ?")
        params.append(error)
    
    if status == 'running':
        updates.append("last_started = ?")
        params.append(datetime.now())
    elif status == 'stopped':
        updates.append("last_stopped = ?")
        params.append(datetime.now())
    
    params.append(bot_id)
    
    query = f"UPDATE bots SET {', '.join(updates)} WHERE id = ?"
    c.execute(query, params)
    conn.commit()
    conn.close()

def get_user_bots(user_id: int) -> List[Dict]:
    """Get all bots for a user"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bots WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    bots = [dict(row) for row in c.fetchall()]
    conn.close()
    return bots

def get_bot(bot_id: str) -> Optional[Dict]:
    """Get bot by ID"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
    bot = c.fetchone()
    conn.close()
    return dict(bot) if bot else None

def delete_bot(bot_id: str):
    """Delete bot from database"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
    conn.commit()
    conn.close()

def get_user_bot_count(user_id: int) -> int:
    """Get number of bots a user has"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM bots WHERE user_id = ?", (user_id,))
    count = c.fetchone()['count']
    conn.close()
    return count

def get_user_max_bots(user_id: int) -> int:
    """Get max bots allowed for user"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT max_bots FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result['max_bots'] if result else 5

def create_or_update_user(user_id: int, max_bots: int = 5):
    """Create or update user"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, max_bots, created_at)
        VALUES (?, ?, COALESCE((SELECT created_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, max_bots, user_id, datetime.now()))
    conn.commit()
    conn.close()
