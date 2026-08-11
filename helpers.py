from flask import redirect, session
from functools import wraps
import sqlite3
import re


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def get_db():
    conn = sqlite3.connect("database/data.db")
    conn.row_factory = sqlite3.Row
    return conn


def _as_list(response):
    """Normalize a single dict or a list of dicts into a list."""
    if isinstance(response, dict):
        return [response]
    if isinstance(response, (list, tuple)):
        return [item for item in response if isinstance(item, dict)]
    return []


def _columns(items):
    """Column names in first-seen order across all item dicts."""
    cols = []
    for item in items:
        for key in item:
            if key not in cols:
                cols.append(key)
    return cols


def plan_sections(response):
    """Normalize an AI plan response into [(title, columns, items)] sections.

    Handles three shapes:
      * dict of lists   -> schedual: one section per key
      * single dict     -> one section with one item
      * list of dicts   -> one section with many items (e.g. exercises)
    """
    if isinstance(response, dict) and response and all(
        isinstance(v, (list, tuple)) for v in response.values()
    ):
        return [
            (title, _columns(items), items)
            for title, items in response.items()
            if items and _columns(items)
        ]
    if isinstance(response, dict):
        return [("Plan", list(response.keys()), [response])] if response else []
    if isinstance(response, (list, tuple)):
        items = [item for item in response if isinstance(item, dict)]
        return [("Plan", _columns(items), items)] if items and _columns(items) else []
    return []


def _get_id(cursor, table, column, value, user_id, insert_sql):
    """Return the id of an existing row or insert a new one."""
    row = cursor.execute(
        f"SELECT id FROM {table} WHERE {column} = ? AND user_id = ?",
        (value, user_id),
    ).fetchone()
    if row is not None:
        return row["id"]
    cursor.execute(insert_sql, (value, user_id))
    return cursor.lastrowid


def _parse_sets_reps(number):
    """Parse '3 x 12' into (sets, reps); fall back to (3, 8) when unparseable.

    Accepts loose AI output: '3 x 12', '3 × 12', '3*12', '3 sets x 12 reps',
    '3 sets of 12', '12 reps x 3 sets', or a bare number.
    """
    text = str(number).lower().replace("×", "x").replace("✕", "x").replace("·", "x").replace("*", "x")

    match = re.search(r"(\d+)\s*x\s*(\d+)", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    sets = re.search(r"(\d+)\s*sets?", text)
    reps = re.search(r"(\d+)\s*reps?", text)
    if sets and reps:
        return int(sets.group(1)), int(reps.group(1))

    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return 3, int(nums[0])
    return 3, 8


def _schedule(cursor, user_id, entry_type, item_id, timeinday, days, col):
    for day in days or []:
        cursor.execute(
            f"INSERT INTO schedual (user_id, type, {col}, time, day) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, entry_type, item_id, timeinday, day),
        )


def addfood(response, user_id, cursor):
    for r in _as_list(response):
        food_id = _get_id(
            cursor, "food", "food", r.get("name", ""), user_id,
            "INSERT INTO food (food, user_id) VALUES (?, ?)",
        )
        cursor.execute("DELETE FROM ingrediants WHERE food_id = ?", (food_id,))
        for ingredient in r.get("ingrediants") or []:
            cursor.execute(
                "INSERT INTO ingrediants (food_id, ingrediant) VALUES (?, ?)",
                (food_id, ingredient),
            )
        _schedule(cursor, user_id, "food", food_id, r.get("timeinday", ""), r.get("DayOfWeek") or [], "food_id")


def addsubject(response, user_id, cursor):
    for r in _as_list(response):
        subject_id = _get_id(
            cursor, "subjects", "subject", r.get("subject", ""), user_id,
            "INSERT INTO subjects (subject, user_id) VALUES (?, ?)",
        )
        _schedule(cursor, user_id, "subject", subject_id, r.get("timeinday", ""), r.get("DayOfWeek") or [], "subject_id")


def addexersize(response, user_id, cursor):
    for r in _as_list(response):
        sets, reps = _parse_sets_reps(r.get("number", ""))
        row = cursor.execute(
            "SELECT id FROM exercises WHERE exercise_name = ? AND user_id = ?",
            (r.get("name", ""), user_id),
        ).fetchone()
        if row is not None:
            exercise_id = row["id"]
            if sets or reps:
                cursor.execute(
                    "UPDATE exercises SET sets = ?, number = ? WHERE id = ?",
                    (sets, reps, exercise_id),
                )
        else:
            cursor.execute(
                "INSERT INTO exercises (exercise_name, user_id, sets, number) VALUES (?, ?, ?, ?)",
                (r.get("name", ""), user_id, sets, reps),
            )
            exercise_id = cursor.lastrowid
        _schedule(cursor, user_id, "exercise", exercise_id, r.get("timeinday", ""), r.get("DayOfWeek") or [], "exercise_id")


def addhabit(response, user_id, cursor):
    for r in _as_list(response):
        row = cursor.execute(
            "SELECT id FROM habits WHERE habits = ? AND user_id = ?",
            (r.get("activity", ""), user_id),
        ).fetchone()
        if row is not None:
            habit_id = row["id"]
        else:
            cursor.execute(
                "INSERT INTO habits (habits, user_id, descreption) VALUES (?, ?, ?)",
                (r.get("activity", ""), user_id, r.get("descreption", "")),
            )
            habit_id = cursor.lastrowid
        _schedule(cursor, user_id, "habit", habit_id, r.get("timeinday", ""), r.get("DayOfWeek") or [], "habit_id")


def addhfun(response, user_id, cursor):
    for r in _as_list(response):
        fun_id = _get_id(
            cursor, "fun", "fun", r.get("acivity", r.get("activity", "")), user_id,
            "INSERT INTO fun (fun, user_id, descreption) VALUES (?, ?, '')",
        )
        _schedule(cursor, user_id, "fun", fun_id, r.get("timeinday", ""), r.get("DayOfWeek") or [], "fun_id")

def getschedual(day, user_id, cursor) -> list:
    query = """
    SELECT
        schedual.id AS id,
        schedual.time AS Time,
        schedual.done AS done,
        food.food AS Food,
        subjects.subject AS Subject,
        exercises.exercise_name AS Exercise,
        habits.habits AS Habit,
        fun.fun AS Fun,
        schedual.subject_id,
        schedual.exercise_id,
        schedual.food_id,
        schedual.habit_id,
        schedual.fun_id,
        schedual.type AS Type
    FROM schedual
    LEFT JOIN food ON schedual.food_id = food.id
    LEFT JOIN subjects ON schedual.subject_id = subjects.id
    LEFT JOIN exercises ON schedual.exercise_id = exercises.id
    LEFT JOIN habits ON schedual.habit_id = habits.id
    LEFT JOIN fun ON schedual.fun_id = fun.id
    WHERE schedual.user_id = ? AND schedual.day = ?
    ORDER BY schedual.time ASC
    """
    cursor.execute(query, (user_id, day))
    return cursor.fetchall()


def getingrediants(food_id, cursor) -> list:
    if not food_id:
        return []
    query = "SELECT ingrediant FROM ingrediants WHERE food_id = ?"
    return cursor.execute(query, (food_id,)).fetchall()


def getexrsizeinfo(exercise_id, cursor) -> dict:
    if not exercise_id:
        return []
    query = "SELECT * FROM exercises WHERE id = ?"
    return cursor.execute(query, (exercise_id,)).fetchall()


def get_analysis(user_id, cursor) -> dict:
    """Aggregate schedule stats for the analysis page.

    Returns exercise volume per weekday, longest weekday streak,
    a day x type completion heatmap, and per-category completion.
    """
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    volume = {day: 0 for day in days_order}
    rows = cursor.execute(
        """
        SELECT s.day AS day, SUM(e.sets * e.number) AS volume
        FROM schedual s
        JOIN exercises e ON s.exercise_id = e.id
        WHERE s.user_id = ? AND s.type = 'exercise' AND s.done = 1
        GROUP BY s.day
        """,
        (user_id,),
    ).fetchall()
    for row in rows:
        volume[row["day"]] = row["volume"] or 0

    done_days = {
        row["day"]
        for row in cursor.execute(
            "SELECT day FROM schedual WHERE user_id = ? AND done = 1 GROUP BY day",
            (user_id,),
        ).fetchall()
    }
    streak = 0
    current = 0
    for day in days_order:
        current = current + 1 if day in done_days else 0
        streak = max(streak, current)

    heatmap = {day: {} for day in days_order}
    rows = cursor.execute(
        """
        SELECT day, type, COUNT(*) AS total, SUM(done) AS done
        FROM schedual
        WHERE user_id = ?
        GROUP BY day, type
        """,
        (user_id,),
    ).fetchall()
    for row in rows:
        heatmap[row["day"]][row["type"]] = {
            "done": row["done"] or 0,
            "total": row["total"],
        }

    type_order = ["subject", "exercise", "food", "habit", "fun"]
    heatmap_types = [t for t in type_order if any(t in heatmap[day] for day in days_order)]

    categories = [
        {
            "type": row["type"],
            "done": row["done"] or 0,
            "total": row["total"],
            "pct": round(100 * (row["done"] or 0) / row["total"]) if row["total"] else 0,
        }
        for row in cursor.execute(
            """
            SELECT type, SUM(done) AS done, COUNT(*) AS total
            FROM schedual
            WHERE user_id = ?
            GROUP BY type
            """,
            (user_id,),
        ).fetchall()
    ]

    return {
        "days": days_order,
        "volumes": [volume[day] for day in days_order],
        "streak": streak,
        "heatmap": heatmap,
        "heatmap_types": heatmap_types,
        "categories": categories,
    }
