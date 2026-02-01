import sqlite3

def get_db_connection():
    conn = sqlite3.connect("evenly.db")
    conn.row_factory = sqlite3.Row  # Allows dictionary-like row access
    return conn
