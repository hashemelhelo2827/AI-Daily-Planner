# AI-Daily-Planner

**Your AI-powered daily life planner** — describe your goals, and get a personalized weekly schedule covering food, study, workouts, habits, and fun. Track how well you stick to it.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)
![SQLite](https://img.shields.io/badge/SQLite-database-green)
![LangChain](https://img.shields.io/badge/LangChain-agent-orange)
[![CI](https://github.com/hashemelhelo2827/AI-Daily-Planner/actions/workflows/ci.yml/badge.svg)](https://github.com/hashemelhelo2827/AI-Daily-Planner/actions/workflows/ci.yml)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database](#database)
- [Security Note](#security-note)
- [Troubleshooting](#troubleshooting)

## Overview

AI-Daily-Planner builds a full weekly plan around **your life**. Tell the agent what you want — a high-protein diet, an A+ study schedule, a stamina workout plan — and it generates a structured plan based on the data you've already registered, then saves it straight into your planner.

## Features

**🤖 AI Plan Generation**
- Separate agents for nutrition, study schedules, exercises, habits, and fun, plus a full weekly schedule
- The agent reads your saved data via MCP tools *before* planning, so plans match your real life

**🔁 Multi-Provider Fallback**
- Tries Mistral → Groq → Gemini in priority order
- Automatic retries on rate limits and invalid JSON output
- Skips providers with missing API keys

**📅 Weekly Schedule Tracker**
- Day-by-day view of food, subjects, exercises, habits, and fun
- One-click completion checkboxes, persisted to the database

**📊 Analysis Dashboard**
- Exercise volume per weekday
- Longest completion streak
- Day × type completion heatmap
- Per-category completion rates

**📚 Study Tracker**
- Log grades per subject, with average grade per subject

**🔐 Authentication**
- Registration/login with hashed passwords (Werkzeug)
- Server-side sessions (Flask-Session)

## How It Works

```
You describe a goal
        │
        ▼
AI agent loads your saved data (food, subjects, exercises, habits, fun)
  └─ via MCP tools (agent/tools.py)
        │
        ▼
Provider chain tries in order: Mistral → Groq → Gemini
  └─ retries on rate limits & invalid JSON
        │
        ▼
Structured JSON plan (validated by Pydantic models)
        │
        ▼
Saved to SQLite (database/data.db)
        │
        ▼
Visible in Weekly Schedule + Analysis dashboard
```

## Tech Stack

| Layer | Tech |
|-------|------|
| **Backend** | Flask, Flask-Session, Werkzeug |
| **AI** | LangChain, LangGraph, LangChain-MCP-Adapter, OpenAI SDK |
| **Models** | Gemini, Groq (Llama), Mistral |
| **Data** | SQLite |

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

Copy `.env.example` to `.env` and add your API keys. The agent automatically uses whichever providers are configured:

```ini
GEMINI_API_KEY=your_key
# GEMINI_API_KEY2=second_key
GROQ_API_KEY=your_key
MISTRAL_API_KEY=your_key
```

### Running

```bash
python app.py
```

Open http://127.0.0.1:5000, register an account, and start generating your plan.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Primary Gemini API key |
| `GEMINI_API_KEY2` | Optional | Secondary Gemini API key (used as fallback) |
| `GROQ_API_KEY` | Optional | Groq API key |
| `MISTRAL_API_KEY` | Optional | Mistral API key |
| `GEMINI_MODEL` | No | Gemini model override (default `gemini-2.0-flash-lite`) |
| `GEMINI_ALT_MODEL` | No | Gemini alt model override (default `gemini-2.0-flash`) |
| `GROQ_MODEL` | No | Groq model override (default `llama-3.1-8b-instant`) |
| `GROQ_STRONG_MODEL` | No | Groq strong model override (default `llama-3.3-70b-versatile`) |
| `MISTRAL_MODEL` | No | Mistral model override (default `mistral-small-2603`) |
| `MISTRAL_MEDIUM_MODEL` | No | Mistral medium model override (default `mistral-medium-2604`) |

You need at least **one** API key. The more you add, the more resilient the agent is to rate limits.

## Usage

On the **New Plan** page, pick a category and describe your goal. Example prompts:

| Category | Example prompt |
|----------|----------------|
| 🍎 Food | "A high-protein, low-carb diet plan for a busy student" |
| 📚 Study | "A stress-free study schedule to get A+ in all my subjects" |
| 🏋️ Exercise | "A full-body workout plan for big stamina and muscle" |
| ✨ Habits | "Habits that will change my life for the better" |
| 🎉 Fun | "Fun activities that won't hurt my productivity" |
| 📅 Full Schedule | "Plan my ideal week with all of my goals" |

The agent reviews your registered data, generates the plan, and previews it for confirmation before saving to your weekly schedule.

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

The SQLite database is created at `database/data.db` on first run. The `schedual` table links schedule entries to food, subjects, exercises, habits, and fun — with a CHECK constraint ensuring each entry references exactly **one** category.

> `data.db`, `.env`, and session files are gitignored — never commit them.

## Security Note

The default `SECRET_KEY` in `app.py` is a placeholder (`super-secret-key-change-me`). **Change it before deploying.**

## Troubleshooting

| Problem | Cause / Fix |
|---------|-------------|
| "The AI service quota is exhausted" | Provider is rate-limited. Wait a few minutes and retry — the agent rotates through other configured providers automatically. |
| "The AI output was incomplete" | The model returned malformed JSON. Re-run the same prompt; the agent retries with another provider. |
| Agent fails immediately | Missing or invalid API keys. Check your `.env` and confirm at least one provider key is set. |
| Schedule is empty | Generate a plan from the **New Plan** page first — items are added to the schedule after confirmation. |
