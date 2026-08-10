import asyncio
import os
import re
import sys
from concurrent.futures import Future
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from openai import OpenAIError, RateLimitError

from agent.neededclasses import *

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


def _to_plain_text(content):
    """Flatten langchain content blocks (lists) into a plain string for strict APIs like GROQ."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    parts.append(str(c.get("text", "")))
                else:
                    parts.append(str(c))
            else:
                parts.append(str(c))
        return "\n".join(p for p in parts if p)
    return str(content)


def _retry_delay(e) -> float | None:
    """Read the suggested retry seconds from a rate-limit error message, if present."""
    text = str(e)
    m = re.search(r"(?:retry|again) in\s+([\d.]+)\s*s", text, re.I)
    return float(m.group(1)) if m else None


class ToolTextNormalizer(AgentMiddleware):
    """Convert ToolMessage content to plain strings before the model is called."""

    async def abefore_model(self, state, runtime):
        messages = state["messages"]
        changed = False
        for m in messages:
            if isinstance(m, ToolMessage) and not isinstance(m.content, str):
                m.content = _to_plain_text(m.content)
                changed = True
        return {"messages": messages} if changed else None


def _providers():
    """Provider chain in priority order. Skips any with a missing API key."""
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
    gemini_alt_model = os.getenv("GEMINI_ALT_MODEL", "gemini-2.0-flash")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    groq_strong_model = os.getenv("GROQ_STRONG_MODEL", "llama-3.3-70b-versatile")
    mistral_model = os.getenv("MISTRAL_MODEL", "mistral-small-2603")
    mistral_medium_model = os.getenv("MISTRAL_MEDIUM_MODEL", "mistral-medium-2604")
    providers = []
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        providers.append(("mistral-small", MISTRAL_BASE_URL, mistral_key, mistral_model))
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        providers.append(("groq-strong", GROQ_BASE_URL, groq_key, groq_strong_model))
        providers.append(("groq", GROQ_BASE_URL, groq_key, groq_model))
    if mistral_key:
        providers.append(("mistral-medium", MISTRAL_BASE_URL, mistral_key, mistral_medium_model))
    for name, key in (
        ("gemini-primary", os.getenv("GEMINI_API_KEY")),
        ("gemini-secondary", os.getenv("GEMINI_API_KEY2")),
    ):
        if key:
            providers.append((f"{name}-lite", GEMINI_BASE_URL, key, gemini_model))
            providers.append((f"{name}-alt", GEMINI_BASE_URL, key, gemini_alt_model))
    return providers

client = MultiServerMCPClient(
    {
        "search tools": {
            "command": sys.executable,
            "args": [str(BASE_DIR / "agent" / "tools.py")],
            "transport": "stdio",
        }
    }
)

_tools = None

_loop = asyncio.new_event_loop()
_thread = Thread(target=_loop.run_forever, daemon=True)
_thread.start()


def run_async(coro) -> Future:

    return asyncio.run_coroutine_threadsafe(coro, _loop)


async def get_tools():
    global _tools
    if _tools is None:
        _tools = await client.get_tools()
    return _tools


async def _run_agent(
    system_prompt: str,
    pydantic_model,
    userid: int,
    userinput: str,
    tool_names: list[str] | None = None,
) -> dict:
    parser = JsonOutputParser(pydantic_object=pydantic_model)
    tools = await get_tools()
    if tool_names:
        tools = [t for t in tools if t.name in tool_names]
    system_prompt_full = (
        f"{system_prompt} The userid is {userid}. "
        "First call search_in_data with this userid to load the user's registered data, "
        "then base your plan on it. "
        "Respond with ONLY the JSON object itself (no prose, no explanations, no markdown code fences). "
        "Do not wrap the object in a JSON schema (do not add a 'properties' key). "
        "Output exactly one JSON object matching: "
        f"{parser.get_format_instructions()}"
    )

    last_error = None
    for name, base_url, api_key, model in _providers():
        for attempt in range(3):
            content = ""
            try:
                llm = ChatOpenAI(model=model, base_url=base_url, api_key=api_key, temperature=0)
                agent = create_agent(
                    llm,
                    tools,
                    system_prompt=system_prompt_full,
                    middleware=(ToolTextNormalizer(),),
                )
                result = await agent.ainvoke({"messages": [("user", userinput)]})
                content = result["messages"][-1].content
                if isinstance(content, list):
                    content = "".join(
                        part.get("text", "") for part in content if isinstance(part, dict)
                    )
                parsed = parser.parse(content)
                if isinstance(parsed, dict) and isinstance(parsed.get("properties"), dict):
                    schema_keys = {"title", "type", "required", "$schema", "$defs", "description", "properties"}
                    if (set(parsed.keys()) - {"properties"}).issubset(schema_keys):
                        parsed = parsed["properties"]
                return parsed
            except RateLimitError as e:
                last_error = e
                delay = _retry_delay(e)
                transient = delay is None or delay <= 20
                if transient and attempt < 2:
                    wait = min(delay + 1 if delay else 2 ** attempt * 6, 30)
                    print(
                        f"[agent] provider '{name}' rate-limited, retrying in {wait}s "
                        f"(attempt {attempt + 1}/3)."
                    )
                    await asyncio.sleep(wait)
                    continue
                print(f"[agent] provider '{name}' rate-limited, trying next.")
                break
            except OutputParserException as e:
                last_error = e
                if attempt < 2:
                    print(
                        f"[agent] provider '{name}' returned invalid JSON, retrying "
                        f"(attempt {attempt + 1}/3)."
                    )
                    continue
                print(f"[agent] provider '{name}' kept returning invalid JSON, trying next.")
                break
            except Exception as e:
                last_error = e
                print(
                    f"[agent] provider '{name}' failed ({type(e).__name__}): "
                    f"{str(e)[:160]} — trying next."
                )
                break

    raise last_error


async def getnewnutretionsystem(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are registered dietitians, licensed nutritionists, and certified personal trainers "
        "and need to give this man a nutrition plan based on his registered data about exercises and food.",
        food,
        userid,
        userinput,
        tool_names=["search_in_data", "search_in_food"],
    )


async def getnewstudyschedual(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are a teacher and need to give this student a study plan to get A+ in all subjects "
        "without pressure on him.",
        study,
        userid,
        userinput,
        tool_names=["search_in_data", "search_in_subjects"],
    )


async def getnewexersizes(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are a certified trainer and need to give this man a good exercise plan for big stamina "
        "and a strong muscular body. "
        "For every exercise, the 'number' field MUST be exactly 'SETS x REPS' with two integers, "
        "for example '3 x 12'. Do not write words like sets, reps, or times inside it.",
        exersizes,
        userid,
        userinput,
        tool_names=["search_in_data", "search_in_exercises"],
    )

async def getnewhabit(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are a someone with greate habits could change someone life to better "
        "give him some habits that fit his life and change it to a better one.",
        Habit,
        userid,
        userinput,
        tool_names=["search_in_data", "search_in_habits"],
    )


async def getnewfun(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are a man who has a completed life work and nice family tell this man how to have fun "
        "and this fun doesn't effect his life.",
        fun,
        userid,
        userinput,
        tool_names=["search_in_data", "search_in_fun"],
    )


async def getnewschedual(userid: int, userinput: str) -> dict:
    return await _run_agent(
        "you are someone skilled at managing time without pressure; give this man a good plan that fits his life.",
        schedual,
        userid,
        userinput,
        tool_names=["search_in_data"],
    )
