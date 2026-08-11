# AGENTS.md

## Project Overview

AI-Daily-Planner is a Flask web app that generates personalized weekly plans (nutrition, study, workouts, habits, fun) using an LLM agent with multi-provider fallback (Mistral -> Groq -> Gemini). Plans are saved to SQLite and tracked via a weekly schedule with completion checkboxes and an analysis dashboard.

Stack: Python 3.11+, Flask, Flask-Session, LangChain/LangGraph, LangChain-MCP-Adapter, SQLite, Jinja2 templates.

## Setup Commands

```powershell
git clone https://github.com/hashemelhelo2827/AI-Daily-Planner.git
cd AI-Daily-Planner
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add at least one API key (`GEMINI_API_KEY`, `GROQ_API_KEY`, or `MISTRAL_API_KEY`). The more keys you add, the more resilient the agent is to rate limits.

## Development Workflow

- Run the server: `python app.py` -> http://127.0.0.1:5000
- Register an account, then generate a plan from the **New Plan** page.
- The SQLite database is created at `database/data.db` on first run.
- `.env`, `data.db`, `flask_session/`, and `__pycache__/` are gitignored - never commit them.

## Key Architecture

- `app.py` - Flask routes (auth, schedule, analysis, study tracker)
- `helpers.py` - DB access, plan normalization, schedule saving, stats
- `agent/agent.py` - LLM provider chain (Mistral -> Groq -> Gemini) with retry logic
- `agent/tools.py` - MCP tools that search the user's saved data
- `agent/neededclasses.py` - Pydantic models validating agent JSON output
- `database/schema.sql` - SQLite schema
- `templates/` - Jinja2 templates, `static/style.css` - styling

## Testing

No automated test suite currently exists. When adding one, place tests in a `tests/` directory using `pytest` and wire them to the GitHub Actions workflow. Until then, verify manually:
1. Start the server and confirm the homepage loads.
2. Register a user and log in.
3. Generate one plan per category (food, study, exercise, habits, fun, full schedule).
4. Confirm plans appear in the Weekly Schedule and Analysis dashboard.

## Code Style

- Python 3.11+, PEP 8 conventions.
- Keep agent orchestration in `agent/`; keep DB access in `helpers.py` - do not scatter DB queries across route handlers.
- Pydantic models must be added to `agent/neededclasses.py` when the agent output schema changes.
- Use Jinja2 server-side rendering in `templates/`; keep custom styling in `static/style.css`.

## Security Considerations

- The default `SECRET_KEY` in `app.py` is a placeholder (`super-secret-key-change-me`). Change it before any deployment.
- API keys live only in `.env` - never hardcode them.
- Passwords are hashed with Werkzeug; sessions use Flask-Session.

## Build and Deployment

- Local: `python app.py`
- Production: run behind a WSGI server (e.g. gunicorn/waitress) with a reverse proxy; set `SECRET_KEY` and real provider keys via environment variables.
- CI: GitHub Actions runs lint + tests on push/PR (see `.github/workflows/`).

## Pull Request Guidelines

- Title format: `<component>: brief description` (e.g. `agent: add Gemini fallback retry`).
- Before opening a PR, confirm the app boots and plan generation works for at least one provider.
- Do not commit `.env`, `data.db`, or session files.
