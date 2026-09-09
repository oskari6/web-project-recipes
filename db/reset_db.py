"""Database reseting utility module"""
from db.utils import get_connection


def reset_database():
    """
    database reset function
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


if __name__ == "__main__":
    reset_database()
    print("Database reset.")
