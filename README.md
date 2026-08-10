# AI-Daily-Planner

An AI-powered daily life planner that builds a personalized weekly schedule covering **food, study, workouts, habits, and fun** — then lets you track how well you stick to it.

Users describe their goals (e.g. *"a high-protein diet plan"*, *"an A+ study schedule"*), and an AI agent generates a structured plan from their registered data, which is saved straight into the planner.

## Features

- **AI plan generation** — separate agents for nutrition, study schedules, exercises, habits, and fun, plus a full weekly schedule. The agent reads your saved data via MCP tools before planning.
- **Multi-provider fallback** — tries Mistral, Groq, and Gemini (in order) with automatic retries on rate limits and invalid JSON.
- **Weekly schedule tracker** — a day-by-day view of food, subjects, exercises, habits, and fun with completion checkboxes.
- **Analysis dashboard** — exercise volume per weekday, longest completion streak, a day × type heatmap, and per-category completion rates.
- **Study tracker** — log grades per subject and view your average grades.
- **Auth** — registration/login with hashed passwords (Werkzeug) and server-side sessions.

## Tech Stack

- **Backend:** Flask, Flask-Session, Werkzeug
- **AI:** LangChain, LangGraph, LangChain-MCP-Adapter, OpenAI SDK
- **Data:** SQLite
- **Models:** Gemini, Groq (Llama), Mistral

## Getting Started

### Prerequisites

- Python 3.11+
- An API key for at least one supported provider (Gemini, Groq, or Mistral)

### Installation

```bash
git clone https://github.com/hashemelhelo2827/AI-Daily-Planner.git
cd AI-Daily-Planner
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and add your API keys. The agent picks the best available provider:

```ini
GEMINI_API_KEY=your_key
# GEMINI_API_KEY2=second_key
GROQ_API_KEY=your_key
MISTRAL_API_KEY=your_key
```

Optional model overrides: `GEMINI_MODEL`, `GROQ_MODEL`, `MISTRAL_MODEL`, etc.

### Running

```bash
python app.py
```

Open http://127.0.0.1:5000, register an account, and start generating your plan.

## Project Structure

```
├── app.py                  # Flask routes (auth, schedule, analysis, study tracker)
├── helpers.py              # DB access, plan normalization, schedule saving, stats
├── agent/
│   ├── agent.py            # LLM provider chain + agent orchestration
│   ├── tools.py            # MCP tools that search the user's saved data
│   └── neededclasses.py    # Pydantic models for agent JSON output
├── database/
│   └── schema.sql          # SQLite schema (users, food, subjects, exercises, habits, fun, schedual, grades)
├── templates/              # Jinja2 templates
├── static/style.css
└── requirements.txt
```

## Database

The SQLite database is created at `database/data.db` on first run. The `schedual` table links schedule entries to food, subjects, exercises, habits, and fun, with a CHECK constraint ensuring each entry references exactly one category.

> `data.db`, `.env`, and session files are gitignored — never commit them.

## Security Note

The default `SECRET_KEY` in `app.py` is a placeholder (`super-secret-key-change-me`). Change it before deploying.

## License

MIT
