"""Recipe service functions"""

from db import utils as db_utils

def get_recipe(recipe_id):
    """
    Return a recipe by its ID.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        sqlite3.Row | None: The recipe if found, otherwise None.
    """
    sql = """SELECT r.id, r.title, r.description, r.creator_id,
                    r.food_type, r.dietary_requirements, r.servings,
                    r.preparation_time, r.created_at, r.updated_at,
                    u.username AS creator_username
             FROM recipes r
             JOIN users u ON u.id = r.creator_id
             WHERE r.id = ?"""

    result = db_utils.query(sql, [recipe_id])

    return result[0] if result else None

def get_recipes(page, page_size, user_id=None, query=None):
    """
    Return a page of recipes, optionally filtered by user.

    Args:
        page (int): The page number, starting from 1.
        page_size (int): Number of recipes per page.
        user_id (int): User's id.
        query (string): optional query string from search.

    Returns:
        list[sqlite3.Row]: The recipes on the requested page.
    """
    sql = """SELECT r.id, r.title, r.description, r.creator_id,
                    r.food_type, r.dietary_requirements,
                    r.servings, r.preparation_time,
                    r.created_at, r.updated_at,
                    u.username AS creator_username,
                    (
                        SELECT ri.file_name
                        FROM recipe_images ri
                        WHERE ri.recipe_id = r.id
                        ORDER BY ri.id
                        LIMIT 1
                    ) AS image_filename
             FROM recipes r
             JOIN users u ON u.id = r.creator_id
          """

    params = []

    if user_id is not None:
        sql += " WHERE r.creator_id = ?"
        params.append(user_id)

    if query:
        if user_id is not None:
            sql += " AND (r.title LIKE ? OR r.description LIKE ?)"
        else:
            sql += " WHERE r.title LIKE ? OR r.description LIKE ?"
        params.extend([f"%{query}%", f"%{query}%"])

    sql += """ ORDER BY r.created_at DESC
              LIMIT ? OFFSET ?"""

    limit = page_size
    offset = page_size * (page - 1)

    params.extend([limit, offset])

    return db_utils.query(sql, params)

def create_recipe(
    title,
    description,
    creator_id,
    food_type=None,
    dietary_requirements=None,
    servings=None,
    preparation_time=None,
    con=None):
    """
    Create a new recipe.

    Args:
        title (str): The recipe title.
        description (str): The recipe description.
        creator_id (int): The ID of the recipe creator.
        food_type (str | None): The type of food.
        dietary_requirements (str | None): Dietary requirements.
        servings (int | None): Number of servings.
        preparation_time (int | None): Preparation time in minutes.

    Returns:
        int: The ID of the created recipe.
    """
    sql = """INSERT INTO recipes
                (title, description, creator_id, food_type,
                 dietary_requirements, servings, preparation_time)
             VALUES (?, ?, ?, ?, ?, ?, ?)"""

    return db_utils.execute(sql, [
        title,
        description,
        creator_id,
        food_type,
        dietary_requirements,
        servings,
        preparation_time
    ], con)

def update_recipe(
    recipe_id,
    title,
    description,
    food_type=None,
    dietary_requirements=None,
    servings=None,
    preparation_time=None,
    con=None
    ):
    """
    Update a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        title (str): The new title.
        description (str): The new description.
        food_type (str | None): The new food type.
        dietary_requirements (str | None): New dietary requirements.
        servings (int | None): The new number of servings.
        preparation_time (int | None): The new preparation time.
    """
    sql = """UPDATE recipes
             SET title = ?,
                 description = ?,
                 food_type = ?,
                 dietary_requirements = ?,
                 servings = ?,
                 preparation_time = ?,
                 updated_at = CURRENT_TIMESTAMP
             WHERE id = ?"""

    db_utils.execute(sql, [
        title,
        description,
        food_type,
        dietary_requirements,
        servings,
        preparation_time,
        recipe_id
    ], con)

def delete_recipe(recipe_id):
    """
    Delete a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
    """
    sql = """DELETE FROM recipes
             WHERE id = ?"""

    db_utils.execute(sql, [recipe_id])

# Ingredients

def get_ingredients(recipe_id):
    """
    Return all ingredients belonging to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        list[sqlite3.Row]: The recipe ingredients.
    """
    sql = """SELECT id, ingredient, amount, unit
             FROM recipe_ingredients
             WHERE recipe_id = ?
             ORDER BY id"""

    return db_utils.query(sql, [recipe_id])

def add_ingredient(recipe_id, ingredient, amount=None, unit=None, con=None):
    """
    Add an ingredient to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        ingredient (str): The ingredient name.
        amount (float | None): The ingredient amount.
        unit (str | None): The measurement unit.

    Returns:
        int: The ID of the created ingredient.
    """
    sql = """INSERT INTO recipe_ingredients
                (recipe_id, ingredient, amount, unit)
             VALUES (?, ?, ?, ?)"""

    return db_utils.execute(sql, [
        recipe_id,
        ingredient,
        amount,
        unit
    ], con)

# Steps

def get_recipe_steps(recipe_id):
    """
    Return all steps belonging to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        list[sqlite3.Row]: The recipe steps.
    """
    sql = """SELECT id, step_number, instruction
             FROM recipe_steps
             WHERE recipe_id = ?
             ORDER BY step_number"""

    return db_utils.query(sql, [recipe_id])

def add_step(recipe_id, step_number, instruction, con=None):
    """
    Add an instruction step to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        step_number (int): The position of the step.
        instruction (str): The instruction text.

    Returns:
        int: The ID of the created step.
    """
    sql = """INSERT INTO recipe_steps
                (recipe_id, step_number, instruction)
             VALUES (?, ?, ?)"""

    return db_utils.execute(sql, [
        recipe_id,
        step_number,
        instruction
    ], con)

# Images

def get_images(recipe_id):
    """
    Return all images belonging to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        list[sqlite3.Row]: The recipe images in display order.
    """
    sql = """SELECT id, file_name
             FROM recipe_images
             WHERE recipe_id = ?
            """

    return db_utils.query(sql, [recipe_id])

# Comments

def get_comment_by_id(comment_id):
    """
    Return a comment by its ID.

    Args:
        comment_id (int): The ID of the comment.

    Returns:
        sqlite3.Row: The comment, or None if not found.
    """
    sql = """
        SELECT id, value, creator_id, recipe_id, created_at
        FROM recipe_comments
        WHERE id = ?
    """

    comments = db_utils.query(sql, [comment_id])

    return comments[0] if comments else None

def get_comments(recipe_id):
    """
    Return all comments belonging to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        list[sqlite3.Row]: The recipe comments.
    """
    sql = """SELECT c.id, c.value, c.creator_id,
                    c.created_at,
                    u.username AS creator_username
             FROM recipe_comments c
             JOIN users u ON u.id = c.creator_id
             WHERE c.recipe_id = ?
             ORDER BY c.created_at DESC"""

    return db_utils.query(sql, [recipe_id])

def add_comment(recipe_id, creator_id, value):
    """
    Add a comment to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        creator_id (int): The ID of the commenter.
        value (str): The comment text.

    Returns:
        int: The ID of the created comment.
    """
    sql = """INSERT INTO recipe_comments
                (recipe_id, creator_id, value)
             VALUES (?, ?, ?)"""

    return db_utils.execute(sql, [
        recipe_id,
        creator_id,
        value
    ])

def update_comment(comment_id, value):
    """
    Update a comment.

    Args:
        comment_id (int): The ID of the comment.
        value (str): The new comment text.
    """
    sql = """UPDATE recipe_comments
             SET value = ?, updated_at = CURRENT_TIMESTAMP
             WHERE id = ?"""

    db_utils.execute(sql, [value, comment_id])

def delete_comment(comment_id):
    """
    Delete a comment.

    Args:
        comment_id (int): The ID of the comment.
    """
    sql = """DELETE FROM recipe_comments
             WHERE id = ?"""

    db_utils.execute(sql, [comment_id])

# Ratings

def get_rating(recipe_id, user_id):
    """
    Return a user's rating for a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        user_id (int): The ID of the user.

    Returns:
        sqlite3.Row | None: The rating if one exists, otherwise None.
    """
    sql = """SELECT id, value, recipe_id
             FROM recipe_ratings
             WHERE recipe_id = ? AND creator_id = ?"""

    result = db_utils.query(sql, [recipe_id, user_id])

    return result[0] if result else None

def get_rating_by_id(rating_id):
    """
    Return a rating by it's id

    Args:
        rating_id (int): The ID of the rating.

    Returns:
        sqlite3.Row | None: The rating if one exists, otherwise None.
    """
    sql = """SELECT id, value, recipe_id
             FROM recipe_ratings
             WHERE id = ?"""

    result = db_utils.query(sql, [rating_id])

    return result[0] if result else None

def get_ratings(recipe_id):
    """
    Return all ratings for a recipe.
    Args:
        recipe_id (int): The ID of the recipe.
    """
    sql = """
        SELECT rr.id,
               rr.value,
               rr.creator_id,
               u.username AS creator_username,
               rr.created_at
        FROM recipe_ratings rr
        JOIN users u ON u.id = rr.creator_id
        WHERE rr.recipe_id = ?
        ORDER BY rr.id DESC
    """

    return db_utils.query(sql, [recipe_id])

def get_user_ratings(user_id):
    """
    Return all recipes rated by a user.
    Args:
        user_id (int): The ID of the user.
    """
    sql = """
        SELECT rr.id,
               rr.value,
               rr.recipe_id,
               r.title AS recipe_title
        FROM recipe_ratings rr
        JOIN recipes r ON r.id = rr.recipe_id
        WHERE rr.creator_id = ?
        ORDER BY rr.id DESC
    """

    return db_utils.query(sql, [user_id])

def get_average_rating(recipe_id):
    """
    Return the average rating and rating count for a recipe.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        sqlite3.Row: The average rating and number of ratings.
    """
    sql = """SELECT AVG(value) AS average_rating,
                    COUNT(*) AS rating_count
             FROM recipe_ratings
             WHERE recipe_id = ?"""

    result = db_utils.query(sql, [recipe_id])

    return result[0]

def add_rating(recipe_id, creator_id, value):
    """
    Add a rating to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        creator_id (int): The ID of the user.
        value (int): The rating from 1 to 5.

    Returns:
        int: The ID of the created rating.
    """
    sql = """INSERT INTO recipe_ratings
                (recipe_id, creator_id, value)
             VALUES (?, ?, ?)"""

    return db_utils.execute(sql, [
        recipe_id,
        creator_id,
        value
    ])

def update_rating(rating_id, value):
    """
    Update a user's rating for a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        creator_id (int): The ID of the user.
        value (int): The new rating from 1 to 5.
    """
    sql = """UPDATE recipe_ratings
             SET value = ?
             WHERE id = ?"""

    db_utils.execute(sql, [
        value,
        rating_id
    ])

def recipe_count(user_id=None, query=None):
    """
    Gets the count of recipes in the database

    Args:
        user_id (int): optional userid filter.
        query (string): optional query string from search.
    Returns:
        count of recipes as int.
    """
    sql = "SELECT COUNT(*) FROM recipes"
    params = []

    if user_id is not None:
        sql += " WHERE creator_id = ?"
        params.append(user_id)

    if query:
        sql += " WHERE title LIKE ? OR description LIKE ?"
        params.extend([f"%{query}%", f"%{query}%"])

    return db_utils.query(sql, params)[0][0]

def remove_all_steps(recipe_id, con=None):
    """
    Removed all steps from a recipe

    Args:
        recipe_id (int): id of recipe
    """
    sql = """
        DELETE FROM recipe_steps
        WHERE recipe_id = ?
    """

    db_utils.execute(sql, [recipe_id], con)

def remove_all_ingredients(recipe_id, con=None):
    """
    Removed all ingredients from a recipe

    Args:
        recipe_id (int): id of recipe
    """
    sql = """
        DELETE FROM recipe_ingredients
        WHERE recipe_id = ?
    """

    db_utils.execute(sql, [recipe_id], con)

def remove_image(recipe_id, image_id, con):
    """
    Removed images from a recipe

    Args:
        recipe_id (int): id of recipe
        image_id (int): id of recipe
        con : connection transaction
    """
    sql = """
        DELETE FROM recipe_images
        WHERE id = ? AND recipe_id = ?
        RETURNING file_name
    """

    db_utils.execute(sql, [image_id, recipe_id], con)

def add_image(recipe_id, file_name, con=None):
    """
    Add an image to a recipe.

    Args:
        recipe_id (int): The ID of the recipe.
        file_name (str): The image file name.

    Returns:
        int: The ID of the created image.
    """
    sql = """INSERT INTO recipe_images
                (recipe_id, file_name)
             VALUES (?, ?)"""

    return db_utils.execute(sql, [
        recipe_id,
        file_name,
    ], con)


def create_ingredients(
    recipe_id,
    ingredients,
    amounts,
    units,
    con
):
    """
    Create ingredients utility function
    Args:
        recipe_id(int) : id of recipe
        ingredients(list) : ingredients
        amounts(list) : amounts
        units(list) : units
        con(Connection) : connection object
    """
    remove_all_ingredients(recipe_id, con)
    for ingredient, amount, unit in zip(
            ingredients,
            amounts,
            units
        ):
        if not ingredient.strip():
            continue

        add_ingredient(
            recipe_id,
            ingredient,
            amount,
            unit,
            con
        )

def create_recipe_steps(
    recipe_id,
    steps,
    con
):
    """
    Create steps utility function
    Args:
        recipe_id(int) : id of recipe
        steps(list): list
        con(Connection) : connection object
    """
    remove_all_steps(recipe_id, con)
    step_number = 1

    for instruction in steps:
        if not instruction.strip():
            continue

        add_step(
            recipe_id,
            step_number,
            instruction,
            con
        )

        step_number += 1
