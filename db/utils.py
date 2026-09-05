import sqlite3
import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    with open("db/migrations.sql", "r") as file:
        connection.executescript(file.read())

    connection.close()

def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.set_trace_callback(print)
    con.row_factory = sqlite3.Row
    return con

def execute(sql, params=()):
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    last_id = result.lastrowid
    con.close()

def query(sql, params=()):
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result