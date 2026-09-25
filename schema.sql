
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    profile_picture_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    creator_id INTEGER NOT NULL,
    food_type INTEGER,
    dietary_requirement INTEGER,
    servings INTEGER,
    preparation_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL,
    ingredient TEXT NOT NULL,
    amount REAL,
    unit TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_steps (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_images (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_comments (
    id INTEGER PRIMARY KEY,
    value TEXT NOT NULL,
    creator_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_ratings (
    id INTEGER PRIMARY KEY,
    value INTEGER NOT NULL CHECK (value BETWEEN 1 AND 5),
    creator_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE (creator_id, recipe_id)
);

CREATE TABLE IF NOT EXISTS food_types (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dietary_requirements (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

INSERT OR IGNORE INTO food_types (name) VALUES
    ('Breakfast'),
    ('Lunch'),
    ('Dinner'),
    ('Dessert'),
    ('Snack');

INSERT OR IGNORE INTO dietary_requirements (name) VALUES
    ('Vegetarian'),
    ('Vegan'),
    ('Gluten-free'),
    ('Keto'),
    ('Carnivore');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_recipes_creator
ON recipes (creator_id);

CREATE INDEX IF NOT EXISTS idx_recipe_images_recipe
ON recipe_images (recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe
ON recipe_ingredients (recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_steps_recipe
ON recipe_steps (recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_comments_creator
ON recipe_comments (creator_id);

CREATE INDEX IF NOT EXISTS idx_recipe_ratings_recipe
ON recipe_ratings (recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_ratings_creator
ON recipe_ratings (creator_id);