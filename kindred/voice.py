"""Voice for Speak-to-Vent: Thai-first speech-to-text + text-to-speech.

Design (privacy/latency aware):
- STT: SpeechRecognition + free Google Web Speech API (th-TH by default).
  No API key needed, but audio IS sent to Google — same tradeoff as any
  cloud voice. Fully-offline typing mode stays 100% local/private.
- TTS: edge-tts (free Microsoft neural voices, no key). Warm female Thai
  voice fits the 'auntie' persona. Audio also goes to Microsoft's service.
- All imports are lazy so the text chat works even without voice deps
  or network. Functions return (result, error_key) — never raise.
"""

import io

# Thai-first voice map: warm female voices matching the auntie persona.
VOICES = {
    "th": "th-TH-PremwadeeNeural",
    "en": "en-US-AriaNeural",
}

STT_LANGS = {"th": "th-TH", "en": "en-US"}


def stt_available() -> bool:
    try:
        import speech_recognition  # noqa: F401
        return True
    except ImportError:
        return False


def tts_available() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def transcribe(audio_bytes: bytes, lang: str = "th") -> tuple[str | None, str | None]:
    """Transcribe WAV bytes -> (text, error_key). error_key is a short code."""
    if not audio_bytes:
        return None, "empty"
    try:
        import speech_recognition as sr
    except ImportError:
        return None, "no-stt-dep"
    try:
        rec = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as src:
            audio = rec.record(src)
        text = rec.recognize_google(audio, language=STT_LANGS.get(lang, "th-TH"))
        text = (text or "").strip()
        return (text, None) if text else (None, "unclear")
    except Exception as e:  # noqa: BLE001 — map to friendly keys
        name = type(e).__name__
        if "UnknownValue" in name:
            return None, "unclear"
        if "RequestError" in name:
            return None, "network"
        return None, "error"


def synthesize(text: str, lang: str = "th") -> tuple[bytes | None, str | None]:
    """Synthesize text -> (mp3_bytes, error_key). Keeps audio in memory only."""
    text = (text or "").strip()
    if not text:
        return None, "empty"
    try:
        import asyncio
        import edge_tts
    except ImportError:
        return None, "no-tts-dep"
    voice = VOICES.get(lang, VOICES["th"])
    # Edge voices handle a few hundred chars best; replies are short by design.
    text = text[:600]

    async def _run() -> bytes:
        buf = io.BytesIO()
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk["type"] == "audio" and chunk.get("data"):
                buf.write(chunk["data"])
        return buf.getvalue()

    try:
        data = asyncio.run(_run())
        return (data, None) if data else (None, "error")
    except RuntimeError:
        # Already inside an event loop (rare in Streamlit): use a new loop.
        import threading

        out: dict = {}

        def _worker() -> None:
            out["data"] = asyncio.run(_run())

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=30)
        data = out.get("data")
        return (data, None) if data else (None, "error")
    except Exception:  # noqa: BLE001 — network down, voice removed, etc.
        return None, "network"


# Friendly Thai-first error lines shown in the UI (validation before info).
VOICE_ERRORS = {
    "th": {
        "empty": "ยังไม่ได้ยินเสียงเลยนะ ลองกดอัดแล้วเล่าใหม่อีกทีได้ไหม?",
        "unclear": "ฟังไม่ชัดเลยจ้ะ เสียงเบาหรือมีเสียงแทรกหรือเปล่า — ลองพูดใกล้ ๆ อีกทีนะ ป้าฟังอยู่",
        "network": "ตอนนี้ป้าหูอื้อ (เน็ตมีปัญหา) เลยถอดเสียงไม่ได้ — พิมพ์เล่าแทนก่อนได้เลยนะ",
        "error": "มีอะไรติดขัดนิดหน่อย ลองอัดใหม่อีกทีนะ หรือพิมพ์เล่าก็ได้เหมือนกัน",
        "no-stt-dep": "เครื่องนี้ยังถอดเสียงพูดไม่ได้ (ขาด SpeechRecognition) — พิมพ์เล่าแทนก่อนนะ",
        "no-tts-dep": "เครื่องนี้ยังไม่มีเสียงพูดตอบ (ขาด edge-tts) — ป้าตอบเป็นตัวหนังสือแทนนะ",
    },
    "en": {
        "empty": "I didn't catch any audio — try recording again?",
        "unclear": "I couldn't make that out — try speaking a little closer?",
        "network": "My ears are fuzzy right now (network issue) — feel free to type instead.",
        "error": "Something hiccuped — try recording again, or type it out.",
        "no-stt-dep": "Speech transcription isn't installed here — typing works too.",
        "no-tts-dep": "Spoken replies aren't installed here — I'll answer in text.",
    },
}


def voice_error(key: str, lang: str = "th") -> str:
    return VOICE_ERRORS.get(lang, VOICE_ERRORS["th"]).get(key, VOICE_ERRORS["th"]["error"])
