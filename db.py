"""Database utilities"""
import sqlite3
from pathlib import Path
import random
from werkzeug.security import generate_password_hash
from config import DIETARY_REQUIREMENTS, FOOD_TYPES

DB_PATH = Path("database.db")
USER_COUNT = 1000000
RECIPE_COUNT = 1000000

def init_db():
    """
    Database initialization function
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    with open("migrations.sql", "r", encoding="utf-8") as file:
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

def seed():
    """Database seeding utility function""" 
    password_hash = generate_password_hash("password")

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA synchronous = OFF")

    # Clear old data

    db.execute("DELETE FROM recipe_ratings")
    db.execute("DELETE FROM recipe_comments")
    db.execute("DELETE FROM recipe_images")
    db.execute("DELETE FROM recipe_steps")
    db.execute("DELETE FROM recipe_ingredients")
    db.execute("DELETE FROM recipes")
    db.execute("DELETE FROM users")


    # Users

    users = (
        (f"user{i}", password_hash)
        for i in range(1, USER_COUNT + 1)
    )

    db.executemany(
        """INSERT INTO users (username, password_hash)
        VALUES (?, ?)""",
        users
    )

    for i in range(1, RECIPE_COUNT + 1):
        creator_id = random.randint(1, USER_COUNT)

        cursor = db.execute(
            """INSERT INTO recipes
                (title, description, creator_id, food_type,
                dietary_requirements, servings, preparation_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                f"Recipe {i}",
                f"Description for recipe {i}",
                creator_id,
                random.choice(FOOD_TYPES),
                random.choice(DIETARY_REQUIREMENTS),
                random.randint(1, 8),
                random.randint(5, 120)
            ]
        )

        recipe_id = cursor.lastrowid


        # Ingredients

        ingredient_count = random.randint(1, 3)

        for j in range(1, ingredient_count + 1):
            db.execute(
                """INSERT INTO recipe_ingredients
                    (recipe_id, ingredient, amount, unit)
                VALUES (?, ?, ?, ?)""",
                [
                    recipe_id,
                    f"Ingredient {j}",
                    random.randint(1, 500),
                    random.choice(["g", "ml", "tbsp", "tsp", "pcs"])
                ]
            )


        # Steps

        step_count = random.randint(1, 3)

        for j in range(1, step_count + 1):
            db.execute(
                """INSERT INTO recipe_steps
                    (recipe_id, step_number, instruction)
                VALUES (?, ?, ?)""",
                [
                    recipe_id,
                    j,
                    f"Instruction {j} for recipe {i}."
                ]
            )


        # Images

        image_count = random.randint(0, 1)

        for j in range(1, image_count + 1):
            db.execute(
                """INSERT INTO recipe_images
                    (recipe_id, file_name)
                VALUES (?, ?)""",
                [
                    recipe_id,
                    "placeholder.jpg"
                ]
            )


        # Comments

        comment_count = random.randint(0, 2)

        for j in range(comment_count):
            db.execute(
                """INSERT INTO recipe_comments
                    (value, creator_id, recipe_id)
                VALUES (?, ?, ?)""",
                [
                    f"Comment {j + 1} on recipe {i}",
                    random.randint(1, USER_COUNT),
                    recipe_id
                ]
            )


        # Ratings

        rating_count = random.randint(0, 3)

        # sample() prevents the same user rating a recipe twice
        rating_users = random.sample(
            range(1, USER_COUNT + 1),
            rating_count
        )

        for user_id in rating_users:
            db.execute(
                """INSERT INTO recipe_ratings
                    (value, creator_id, recipe_id)
                VALUES (?, ?, ?)""",
                [
                    random.randint(1, 5),
                    user_id,
                    recipe_id
                ]
            )


    db.commit()
    db.execute("PRAGMA synchronous = NORMAL")
    db.close()

    print(f"Created {USER_COUNT} users and {RECIPE_COUNT} recipes.")

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
