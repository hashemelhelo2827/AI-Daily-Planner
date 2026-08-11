# Contributing to AI-Daily-Planner

Thanks for your interest in contributing! This project is a small, personal Flask app - any help is appreciated.

## Getting started

1. Fork the repository and clone your fork.
2. Follow the [Setup](README.md#getting-started) instructions.
3. Create a branch: `git checkout -b feat/my-change`.

## What to work on

- Bug fixes for plan generation, the schedule tracker, or the analysis dashboard.
- Improvements to agent prompt reliability (JSON output, retries, provider fallback).
- Tests - there is currently no test suite; a `tests/` dir with `pytest` would be a huge win.
- Documentation, `.env.example` completeness, or a real `CONTRIBUTING` flow.

## Commit & PR guidelines

- Title format: `<component>: brief description` (e.g. `agent: add Gemini fallback retry`).
- Never commit `.env`, `database/data.db`, `flask_session/`, or `__pycache__/`.
- Before opening a PR, confirm the app boots (`python app.py`) and plan generation works for at least one provider.
- Reference the issue you're fixing in the PR description when applicable.

## Reporting bugs

Open an issue with:

- Steps to reproduce
- Expected vs actual behavior
- Your `.env` providers configured (never paste real keys)
- Any error output from the terminal
