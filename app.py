import json
import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from agent.agent import *
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key-change-me")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def _init_schema():
    """Create missing tables on a fresh database."""
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingrediants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER NOT NULL,
            ingrediant TEXT NOT NULL,
            FOREIGN KEY (food_id) REFERENCES food(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


_init_schema()



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()

        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()


        if user is None:
            flash("Username does not exist")
            return redirect("/login")

        if not check_password_hash(user["password"], password):
            flash("Incorrect password")
            return redirect("/login")

        session["user_id"] = user["id"]
        flash("Logged in successfully!")
        return redirect("/homepage")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")

        if not username:
            flash("Username is required")
            return redirect("/register")

        if not email:
            flash("Email is required")
            return redirect("/register")

        if not password or not confirmpassword:
            flash("Please enter both password fields")
            return redirect("/register")

        if password != confirmpassword:
            flash("Password and confirm password aren't the same")
            return redirect("/register")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            conn.close()
            flash("Username is already taken")
            return redirect("/register")

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            conn.close()
            flash("Email is already taken")
            return redirect("/register")

        hash_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
            (email, username, hash_password)
        )
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.")
        return redirect("/login")

    return render_template("regitration.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/homepage")
@login_required
def homepage():
    return render_template("homepage.html")


@app.route("/analysis")
@login_required
def analysis():
    conn = get_db()
    cursor = conn.cursor()
    data = get_analysis(session["user_id"], cursor)
    conn.close()
    return render_template("analysis.html", data=data)


@app.route("/studytracker", methods=["GET", "POST"])
@login_required
def studytracker():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        subject = request.form.get("subject")
        type_ = request.form.get("type")
        grade = request.form.get("grade")


        query = "SELECT id FROM subjects WHERE user_id = ? AND subject = ?"
        row = cursor.execute(query, (session["user_id"], subject)).fetchone()

        if row is None:
            query = "INSERT INTO subjects (user_id, subject) VALUES (?, ?)"
            cursor.execute(query, (session["user_id"], subject))
            conn.commit()
            subject_id = cursor.lastrowid
        else:
            subject_id = row["id"]

        query = "INSERT INTO grades (user_id, subject_id, type, grade) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (session["user_id"], subject_id, type_, grade))
        conn.commit()

        cursor.close()
        return redirect("/studytracker")

    query = """
        SELECT
            s.subject AS subject,
            COALESCE(ROUND(AVG(g.grade), 2), 0) AS average_grade
        FROM subjects s
        LEFT JOIN grades g ON s.id = g.subject_id AND s.user_id = g.user_id
        WHERE s.user_id = ?
        GROUP BY s.id, s.subject
    """

    rows = cursor.execute(query, (session["user_id"],)).fetchall()
    cursor.close()

    subjects = [row["subject"] for row in rows]
    grades = [row["average_grade"] for row in rows]

    return render_template("studytracker.html", rows=rows, subjects=subjects, grades=grades)

@app.route("/newhabit", methods=["GET", "POST"])
@login_required
def newhabit():
    if request.method == "POST":
        habit_type = request.form.get("habbit")
        user_id = session.get("user_id")

        if request.form.get("save") == "true":
            conn = None
            try:
                data = json.loads(request.form.get("response") or "{}")
                conn = get_db()
                cursor = conn.cursor()
                if habit_type == "food":
                    addfood(data, user_id, cursor)
                elif habit_type == "subjects":
                    addsubject(data, user_id, cursor)
                elif habit_type == "exercises":
                    addexersize(data, user_id, cursor)
                elif habit_type == "habit":
                    addhabit(data, user_id, cursor)
                elif habit_type == "fun":
                    addhfun(data, user_id, cursor)
                else:
                    data = data if isinstance(data, dict) else {}
                    addfood(data.get("food", []), user_id, cursor)
                    addsubject(data.get("studyschedual", []), user_id, cursor)
                    addexersize(data.get("exersizes", []), user_id, cursor)
                    addhabit(data.get("habit", []), user_id, cursor)
                    addhfun(data.get("fun", []), user_id, cursor)
                conn.commit()
                flash("Has been added to Schedule.")
                return redirect("/newhabit")
            except Exception:
                app.logger.exception("Save failed")
                flash("Could not save the plan — the AI output was incomplete. Try asking again.")
                return redirect("/newhabit")
            finally:
                if conn is not None:
                    conn.close()

        query = request.form.get("query")

        try:
            if habit_type == "food":
                response = run_async(getnewnutretionsystem(userid=user_id, userinput=query)).result()
            elif habit_type == "subjects":
                response = run_async(getnewstudyschedual(userid=user_id, userinput=query)).result()
            elif habit_type == "exercises":
                response = run_async(getnewexersizes(userid=user_id, userinput=query)).result()
            elif habit_type == "habit":
                response = run_async(getnewhabit(userid=user_id, userinput=query)).result()
            elif habit_type == "fun":
                response = run_async(getnewfun(userid=user_id, userinput=query)).result()
            else:
                response = run_async(getnewschedual(userid=user_id, userinput=query)).result()
        except Exception:
            app.logger.exception("Agent call failed")
            flash("The AI service quota is exhausted right now — try again in a few minutes.")
            return redirect("/newhabit")

        return render_template(
            "newhabbitadded.html",
            rows=response,
            sections=plan_sections(response),
            habit_type=habit_type,
        )

    return render_template("newhabbit.html")


@app.route("/schedual", methods=["GET", "POST"])
@login_required
def schedual():
    conn = get_db()
    cursor = conn.cursor()


    day = request.form.get("day", "Monday") if request.method == "POST" else "Monday"

    rows = getschedual(day, session["user_id"], cursor)

    food_ids = {r["food_id"] for r in rows if r["food_id"]}
    exercise_ids = {r["exercise_id"] for r in rows if r["exercise_id"]}

    ingrediants = {fid: getingrediants(fid, cursor) for fid in food_ids}
    exerciseinfo = {eid: getexrsizeinfo(eid, cursor) for eid in exercise_ids}

    conn.close()

    return render_template(
        "tracing.html",
        rows=rows,
        ingrediants=ingrediants,
        exerciseinfo=exerciseinfo,
        current_day=day
    )


@app.route("/update_status", methods=["POST"])
@login_required
def update_status():
    data = request.get_json()
    item_id = data.get("id")
    is_done = 1 if data.get("done") else 0

    if not item_id:
        return {"status": "error", "message": "Missing item ID"}, 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE schedual SET done = ? WHERE id = ? AND user_id = ?",
        (is_done, item_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return {"status": "success"}, 200
