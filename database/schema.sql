PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS food (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    food TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sets INTEGER NOT NULL DEFAULT 3,
    number INTEGER NOT NULL DEFAULT 8,
    exercise_name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fun (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fun TEXT NOT NULL,
    descreption TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    grade INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    habits TEXT NOT NULL,
    descreption TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "schedual" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('subject', 'exercise', 'food', 'habit', 'fun')),

    subject_id INTEGER,
    exercise_id INTEGER,
    food_id INTEGER,
    habit_id INTEGER,
    fun_id INTEGER,

    time TEXT NOT NULL,
    day TEXT NOT NULL CHECK (day IN ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")),
    done BOOLEAN NOT NULL DEFAULT FALSE,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES food(id) ON DELETE CASCADE,
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    FOREIGN KEY (fun_id) REFERENCES fun(id) ON DELETE CASCADE,

    CONSTRAINT check_valid_type_id CHECK (
        (type = 'subject'  AND subject_id  IS NOT NULL AND exercise_id IS NULL AND food_id IS NULL AND habit_id IS NULL AND fun_id IS NULL) OR
        (type = 'exercise' AND exercise_id IS NOT NULL AND subject_id  IS NULL AND food_id IS NULL AND habit_id IS NULL AND fun_id IS NULL) OR
        (type = 'food'     AND food_id     IS NOT NULL AND subject_id  IS NULL AND exercise_id IS NULL AND habit_id IS NULL AND fun_id IS NULL) OR
        (type = 'habit'    AND habit_id    IS NOT NULL AND subject_id  IS NULL AND exercise_id IS NULL AND food_id IS NULL AND fun_id IS NULL) OR
        (type = 'fun'      AND fun_id      IS NOT NULL AND subject_id  IS NULL AND exercise_id IS NULL AND food_id IS NULL AND habit_id IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS ingrediants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL,
    ingrediant TEXT NOT NULL,
    FOREIGN KEY (food_id) REFERENCES food(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_schedual_user_day ON schedual (user_id, day);
CREATE INDEX IF NOT EXISTS idx_schedual_user_type ON schedual (user_id, type);
CREATE INDEX IF NOT EXISTS idx_ingrediants_food ON ingrediants (food_id);
