"""Response generation: optional LLM, warm local fallback that honors persona rules."""

import hashlib
import json
import os
import urllib.request

from .persona import SYSTEM_PROMPT, VENTING_REMINDER, is_asking_for_advice

VALIDATIONS = [
    "That sounds incredibly heavy, sweetheart.",
    "I completely understand why you feel that way.",
    "That makes so much sense — of course you feel like this.",
    "I'm really glad you told me. That sounds exhausting.",
]

LOCAL_ADVICE = (
    "Since you asked, here's one gentle thought — take only what feels right, "
    "and leave the rest: break the tiniest next step into something "
    "five minutes small, and let yourself rest without guilt around it. "
    "You don't have to earn rest, love."
)


def _pick_validation(text: str) -> str:
    i = int(hashlib.md5(text.encode()).hexdigest(), 16) % len(VALIDATIONS)
    return VALIDATIONS[i]


def _reflect(text: str) -> str:
    snippet = text.strip().split("\n")[0][:160]
    if len(snippet) < 12:
        return "I'm right here with you."
    return f'It makes complete sense you\'d feel this way about "{snippet}".'


def local_response(user_text: str, venting: bool) -> str:
    v = _pick_validation(user_text)
    r = _reflect(user_text)
    if venting:
        return (
            f"{v} {r} No fixing, no advice from me — "
            "just listening. Keep going if you need to, I'm not going anywhere."
        )
    if is_asking_for_advice(user_text):
        return f"{v} {r} {LOCAL_ADVICE}"
    return (
        f"{v} {r} You're carrying a lot, and still showing up — "
        "that says something about your strength. "
        "I'm here for as long as you need. "
        "If you ever want a thought on what to do, just ask and I'll share gently."
    )


def try_llm(user_text: str, history: list[dict], venting: bool) -> str | None:
    """Call an OpenAI-compatible endpoint if configured. Returns None if unset/fails."""
    url = os.getenv("KINDRED_API_URL", "").strip()
    key = os.getenv("KINDRED_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("KINDRED_MODEL", "gpt-4o-mini")
    if not url or not key:
        return None
    system = SYSTEM_PROMPT + ("\n\n" + VENTING_REMINDER if venting else "")
    msgs = [{"role": "system", "content": system}]
    msgs += history[-10:]
    msgs.append({"role": "user", "content": user_text})
    body = json.dumps({"model": model, "messages": msgs, "temperature": 0.7}).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
        return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def generate(user_text: str, history: list[dict], venting: bool) -> tuple[str, str]:
    """Returns (reply, source) where source is 'llm' or 'local'."""
    llm = try_llm(user_text, history, venting)
    if llm:
        return llm, "llm"
    # Safety net: even if an LLM is misconfigured, venting mode never gives advice.
    reply = local_response(user_text, venting)
    if venting and is_asking_for_advice(user_text):
        # User asked but venting mode overrides: acknowledge, withhold advice.
        reply = local_response(user_text, venting=True)
    return reply, "local"
