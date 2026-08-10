from datetime import datetime, time
import sqlite3
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("agent search tools")

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "data.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


@mcp.tool()
def search_in_habits(userid: int) -> list[dict]:
    """Search all habits registered for a specific user ID."""
    rows = cursor.execute(
        "SELECT id, habits FROM habits WHERE user_id = ?", (userid,)
    ).fetchall()
    return [{"id": row["id"], "habit": row["habits"]} for row in rows]


@mcp.tool()
def search_in_food(userid: int) -> list[dict]:
    """Search all food entries registered for a specific user ID."""
    rows = cursor.execute(
        "SELECT id, food FROM food WHERE user_id = ?", (userid,)
    ).fetchall()
    return [{"id": row["id"], "food": row["food"]} for row in rows]


@mcp.tool()
def search_in_subjects(userid: int) -> list[dict]:
    """Search all study subjects registered for a specific user ID."""
    rows = cursor.execute(
        "SELECT id, subject FROM subjects WHERE user_id = ?", (userid,)
    ).fetchall()
    return [{"id": row["id"], "subject": row["subject"]} for row in rows]


@mcp.tool()
def search_in_exercises(userid: int) -> list[dict]:
    """Search all exercise routines registered for a specific user ID."""
    rows = cursor.execute(
        "SELECT id, exercise_name, sets, number FROM exercises WHERE user_id = ?",
        (userid,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "exercise_name": row["exercise_name"],
            "sets": row["sets"],
            "number": row["number"],
        }
        for row in rows
    ]


@mcp.tool()
def search_in_fun(userid: int) -> list[dict]:
    """Search all fun activities registered for a specific user ID."""
    rows = cursor.execute(
        "SELECT id, fun FROM fun WHERE user_id = ?", (userid,)
    ).fetchall()
    return [{"id": row["id"], "fun": row["fun"]} for row in rows]

@mcp.tool()
def search_ingredients(foodid: int) -> list[dict]:
    """Search all ingredients belonging to a specific food ID."""
    rows = cursor.execute(
        "SELECT * FROM ingrediants WHERE food_id = ?", (foodid,)
    ).fetchall()
    return [{"id": row["id"], "food_id": row["food_id"], "ingrediant": row["ingrediant"]} for row in rows]


@mcp.tool()
def search_in_data(userid: int) -> list[dict]:
    """Search across ALL categories (Habits, Food, Subjects, Exercises, Fun) for a user ID."""
    rows = cursor.execute(
        """
        SELECT 'Habit' AS category, habits AS detail FROM habits WHERE user_id = :uid
        UNION ALL
        SELECT 'Food' AS category, food FROM food WHERE user_id = :uid
        UNION ALL
        SELECT 'Subject' AS category, subject FROM subjects WHERE user_id = :uid
        UNION ALL
        SELECT 'Exercise' AS category, exercise_name || ' (' || sets || ' sets x ' || number || ' reps)' FROM exercises WHERE user_id = :uid
        UNION ALL
        SELECT 'Fun' AS category, fun FROM fun WHERE user_id = :uid
        """,
        {"uid": userid},
    ).fetchall()

    return [{"category": row["category"], "detail": row["detail"]} for row in rows]


if __name__ == "__main__":
    mcp.run()
