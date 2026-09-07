"""Database utilities"""
import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")

def init_db():
    """
    Database initialization function
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    with open("db/migrations.sql", "r", encoding="utf-8") as file:
        connection.executescript(file.read())

    connection.close()

def get_connection():
    """
    Database connection function
    Returns:
        con(Connection) : connection
    """
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.set_trace_callback(print)
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=(), con=None):
    """
    Utility function to execute sql commands
    
    Args:
        sql (str) : sql string
        params (list) : parameters
        con (Connection): optional connection for transaction support
    Returns:
        last_id(int) : result id
    """
    own_connection = con is None

    if own_connection:
        con = get_connection()
    result = con.execute(sql, params)
    last_id = result.lastrowid
    if own_connection:
        con.commit()
        con.close()
    return last_id

def query(sql, params=()):
    """
    Utility function to query with sql commands
    
    Args:
        sql (str) : sql string
        params (list) : parameters
    Returns:
        result(list:any) : query result
    """
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
