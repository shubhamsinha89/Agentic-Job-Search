"""
llm_client.py
Lightweight LLM abstraction supporting multiple free/paid providers.

Set LLM_PROVIDER in .env to switch:
  LLM_PROVIDER=groq        (default — free, fast, Llama 3.3 70B)
  LLM_PROVIDER=gemini      (free tier — Gemini 1.5 Flash)
  LLM_PROVIDER=ollama      (local, fully free — needs Ollama installed)
  LLM_PROVIDER=anthropic   (paid — original Claude)

Required env vars per provider:
  groq      → GROQ_API_KEY      (free at console.groq.com)
  gemini    → GEMINI_API_KEY    (free at aistudio.google.com)
  ollama    → OLLAMA_MODEL      (optional, default: llama3.2)
  anthropic → ANTHROPIC_API_KEY
"""

import os
import json
import re


PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def complete(prompt: str, max_tokens: int = 2048, model: str = None) -> str:
    """
    Send a prompt to the configured LLM and return the response text.
    Automatically picks the right client based on LLM_PROVIDER env var.
    """
    if PROVIDER == "groq":
        return _groq(prompt, max_tokens, model)
    elif PROVIDER == "gemini":
        return _gemini(prompt, max_tokens, model)
    elif PROVIDER == "ollama":
        return _ollama(prompt, max_tokens, model)
    elif PROVIDER == "anthropic":
        return _anthropic(prompt, max_tokens, model)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER!r}. Use: groq, gemini, ollama, anthropic")


def complete_json(prompt: str, max_tokens: int = 2048, model: str = None) -> dict:
    """Send prompt, parse response as JSON, return dict."""
    raw = complete(prompt, max_tokens, model)
    return json.loads(_clean_json(raw))


# ── Groq (free) ────────────────────────────────────────────────────────────

def _groq(prompt: str, max_tokens: int, model: str = None) -> str:
    from openai import OpenAI
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set. Get a free key at console.groq.com")
    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    resp = client.chat.completions.create(
        model=model or "llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    return resp.choices[0].message.content


# ── Google Gemini (free tier) ───────────────────────────────────────────────

def _gemini(prompt: str, max_tokens: int, model: str = None) -> str:
    import google.generativeai as genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY not set. Get a free key at aistudio.google.com")
    genai.configure(api_key=key)
    m = genai.GenerativeModel(model or "gemini-1.5-flash")
    resp = m.generate_content(
        prompt,
        generation_config={"max_output_tokens": max_tokens, "temperature": 0.1},
    )
    return resp.text


# ── Ollama (local, free) ───────────────────────────────────────────────────

def _ollama(prompt: str, max_tokens: int, model: str = None) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key="ollama",
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    )
    resp = client.chat.completions.create(
        model=model or os.environ.get("OLLAMA_MODEL", "llama3.2"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    return resp.choices[0].message.content


# ── Anthropic Claude (paid) ────────────────────────────────────────────────

def _anthropic(prompt: str, max_tokens: int, model: str = None) -> str:
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not set.")
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=model or "claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def provider_info() -> str:
    labels = {
        "groq":      "Groq  (Llama 3.3 70B — free)",
        "gemini":    "Google Gemini Flash (free tier)",
        "ollama":    f"Ollama local ({os.environ.get('OLLAMA_MODEL', 'llama3.2')})",
        "anthropic": "Anthropic Claude (paid)",
    }
    return labels.get(PROVIDER, PROVIDER)