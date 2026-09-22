"""Users service functions"""
from db import utils as db_utils

def get_user(user_id):
    """
    Return a user by their ID.
    Args:
        user_id (int): The ID of the user.
    Returns:
        sqlite3.Row | None: The user if found, otherwise None.
    """
    sql = """SELECT id,
        username,
        profile_picture_filename,
        created_at,
        (SELECT MAX(created_at) FROM recipes WHERE creator_id = users.id) AS latest_recipe_at
             FROM users
             WHERE id = ?"""
    result = db_utils.query(sql, [user_id])
    return result[0] if result else None

def get_user_password_hash(user_id):
    """
    Return a user password has by their ID.
    Args:
        user_id (int): The ID of the user.
    Returns:
        sqlite3.Row | None: The user password hash if found, otherwise None.
    """
    sql = """SELECT password_hash
             FROM users
             WHERE id = ?"""
    result = db_utils.query(sql, [user_id])
    return result[0] if result else None

def get_users(page, page_size, query=None):
    """
    Return a page of users.

    Args:
        page (int): The page number, starting from 1.
        page_size (int): Number of users per page.
        query (string): optional query string from search.

    Returns:
        list[sqlite3.Row]: The users on the requested page.
    """
    sql = """
        SELECT
            u.id,
            u.username,
            u.created_at,
            u.profile_picture_filename,
            COUNT(r.id) AS recipe_count
        FROM users u
        LEFT JOIN recipes r ON r.creator_id = u.id
    """
    params = []

    if query:
        sql += " WHERE username LIKE ?"
        params.append(f"%{query}%")

    sql += """
        GROUP BY u.id
        ORDER BY username
        LIMIT ? OFFSET ?
    """

    params.extend([
        page_size,
        page_size * (page - 1)
    ])

    return db_utils.query(sql, params)

def get_user_by_username(username):
    """
    Return a user by their username.

    Args:
        username (str): The username of the user.

    Returns:
        sqlite3.Row | None: The user if found, otherwise None.
    """
    sql = """SELECT id,
        username,
        password_hash,
        profile_picture_filename,
        created_at
        FROM users
        WHERE username = ?"""

    result = db_utils.query(sql, [username])

    return result[0] if result else None

def create_user(username, password_hash, filename=None):
    """
    Create a new user.

    Args:
        username (str): The username of the user.
        password_hash (str): The hashed password.

    Returns:
        int: The ID of the created user.
    """
    sql = """INSERT INTO users (username, password_hash, profile_picture_filename)
             VALUES (?, ?, ?)"""

    return db_utils.execute(sql, [username, password_hash, filename])

def update_user(user_id, username, password_hash, profile_pic_filename):
    """
    Update a user's information

    Args:
        user_id (int): The ID of the user.
        username (str): The new username.
        password_hash (str): The new username.
        profile_pic_filename (str): users profile picture filename
    """
    sql = """UPDATE users
             SET username = ?,
                password_hash = ?,
                profile_picture_filename = ?
             WHERE id = ?"""

    db_utils.execute(sql, [username, password_hash, profile_pic_filename, user_id])

def remove_profile_picture(user_id):
    """
    Remove a user's profile picture.

    Args:
        user_id (int): The ID of the user.
    """
    sql = """UPDATE users
             SET profile_picture_filename = NULL
             WHERE id = ?"""

    db_utils.execute(sql, [user_id])

def get_user_recipes(user_id):
    """
    Return all recipes created by a user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list[sqlite3.Row]: The user's recipes.
    """
    sql = """SELECT id, title, description, food_type,
                    servings, preparation_time, created_at, updated_at
             FROM recipes
             WHERE creator_id = ?
             ORDER BY created_at DESC"""

    return db_utils.query(sql, [user_id])

def delete_user(user_id):
    """
    Delete a user.

    Args:
        user_id (int): The ID of the user.
    """
    sql = """DELETE FROM users
             WHERE id = ?"""

    db_utils.execute(sql, [user_id])

def user_count(query=None):
    """
    Gets the count of users in the database
    
    Args:
        query (string): optional query string from search.
    Returns:
            count of users as int.
    """
    sql = "SELECT COUNT(*) FROM users"
    params = []

    if query:
        sql += " WHERE username LIKE ?"
        params.append(f"%{query}%")

    return db_utils.query(sql, params)[0][0]
