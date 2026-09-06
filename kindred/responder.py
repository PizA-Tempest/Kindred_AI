"""Response generation: optional LLM, warm local fallback that honors persona rules."""

import hashlib
import json
import os
import urllib.request

from .persona import SYSTEM_PROMPT, VENTING_REMINDER, detect_lang, is_asking_for_advice

VALIDATIONS_TH = [
    "ฟังแล้วเข้าใจเลยว่าทำไมถึงรู้สึกแบบนี้.",
    "มันหนักมากเลยนะ ที่รัก.",
    "เข้าใจเลยจริง ๆ ความรู้สึกแบบนี้มันสมเหตุสมผลมาก.",
    "ดีใจนะที่เล่าให้ฟัง ฟังแล้วเหนื่อยแทนเลย.",
]

VALIDATIONS_EN = [
    "That sounds incredibly heavy, sweetheart.",
    "I completely understand why you feel that way.",
    "That makes so much sense — of course you feel like this.",
    "I'm really glad you told me. That sounds exhausting.",
]

# Keep legacy name for backwards-compat (tests / imports).
VALIDATIONS = VALIDATIONS_EN

LOCAL_ADVICE_TH = (
    "ไหน ๆ ก็ถามมาแล้ว ขอแชร์หนึ่งความคิดเบา ๆ นะ — "
    "อันไหนใช่ก็เก็บไว้ อันไหนไม่ใช่ก็วางลงได้เลย: "
    "ลองซอยก้าวต่อไปให้เล็กที่สุด แค่ห้านาทีก็พอ แล้วพักโดยไม่ต้องรู้สึกผิดนะ "
    "ไม่ต้องแลกความพักด้วยการทำงานให้เหนื่อยก่อนก็ได้ คนเก่ง."
)

LOCAL_ADVICE_EN = (
    "Since you asked, here's one gentle thought — take only what feels right, "
    "and leave the rest: break the tiniest next step into something "
    "five minutes small, and let yourself rest without guilt around it. "
    "You don't have to earn rest, love."
)
LOCAL_ADVICE = LOCAL_ADVICE_EN


def _pick_validation(text: str, lang: str = "th") -> str:
    pool = VALIDATIONS_TH if lang == "th" else VALIDATIONS_EN
    i = int(hashlib.md5(text.encode()).hexdigest(), 16) % len(pool)
    return pool[i]


def _reflect(text: str, lang: str = "th") -> str:
    snippet = text.strip().split("\n")[0][:160]
    if len(snippet) < 12:
        return "ป้าอยู่ตรงนี้กับหนูนะ." if lang == "th" else "I'm right here with you."
    if lang == "th":
        return f'เข้าใจเลยว่าทำไมถึงรู้สึกแบบนี้กับเรื่อง "{snippet}".'
    return f'It makes complete sense you\'d feel this way about "{snippet}".'


def local_response(user_text: str, venting: bool, lang: str = "th") -> str:
    # Thai-first: auto-switch to Thai when Thai script is present.
    lang = detect_lang(user_text, default=lang)
    v = _pick_validation(user_text, lang)
    r = _reflect(user_text, lang)
    if lang == "th":
        if venting:
            return (
                f"{v} {r} ไม่ต้องแก้ ไม่ต้องรีบหาทางออกนะ — "
                "ป้าแค่ฟังอยู่ตรงนี้ เล่าต่อได้เลย ป้าไม่ไปไหน."
            )
        if is_asking_for_advice(user_text):
            return f"{v} {r} {LOCAL_ADVICE_TH}"
        return (
            f"{v} {r} แบกอะไรไว้เยอะเลยนะ แต่ยังผ่านแต่ละวันมาได้ — "
            "เก่งมากแล้วนะ. "
            "ป้าอยู่ตรงนี้เป็นเพื่อนเสมอ. "
            "ถ้าวันไหนอยากได้ความคิดเบา ๆ ว่าจะทำยังไงต่อ แค่บอกได้เลยนะ."
        )
    if venting:
        return (
            f"{v} {r} No fixing, no advice from me — "
            "just listening. Keep going if you need to, I'm not going anywhere."
        )
    if is_asking_for_advice(user_text):
        return f"{v} {r} {LOCAL_ADVICE_EN}"
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


def generate(user_text: str, history: list[dict], venting: bool, lang: str = "th") -> tuple[str, str]:
    """Returns (reply, source) where source is 'llm' or 'local'. Thai-first."""
    lang = detect_lang(user_text, default=lang)
    llm = try_llm(user_text, history, venting)
    if llm:
        return llm, "llm"
    # Safety net: even if an LLM is misconfigured, venting mode never gives advice.
    reply = local_response(user_text, venting, lang=lang)
    if venting and is_asking_for_advice(user_text):
        # User asked but venting mode overrides: acknowledge, withhold advice.
        reply = local_response(user_text, venting=True, lang=lang)
    return reply, "local"
