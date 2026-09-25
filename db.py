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

    with open("schema.sql", "r", encoding="utf-8") as file:
        connection.executescript(file.read())

    try:
        with connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(recipes)")}
            for old_name in ("food_type", "dietary_requirement"):
                if old_name in columns:
                    connection.execute(
                        f'ALTER TABLE recipes RENAME COLUMN "{old_name}" TO "{old_name}_id"'
                    )
    finally:
        connection.close()

def get_connection():
    """
    Database connection function
    Returns:
        con(Connection) : connection
    """
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
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
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()

def reset_database():
    """
    Database reset utility function
    """
    con = get_connection()

    try:
        con.execute("PRAGMA foreign_keys = OFF")

        tables = con.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
        """).fetchall()

        for table in tables:
            table_name = table["name"]
            con.execute(f'DROP TABLE IF EXISTS "{table_name}"')

        con.commit()
    finally:
        con.close()
    print("Database reset.")
