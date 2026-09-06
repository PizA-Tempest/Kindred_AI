"""Encrypted local memory: past stressors + recent exchanges."""

import json
import os
import re
import time
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # handled at runtime with a clear error
    Fernet = None

DEFAULT_PATH = Path("data/kindred_memory.enc")
KEY_PATH = Path(".kindred.key")

_FEELING_WORDS = [
    "stress", "tired", "frustrat", "anxious", "overwhelm", "sad",
    "angry", "exhaust", "worried", "burnout", "lonely", "upset",
    "drain", "pressure", "deadline", "boss", "work", "family",
    # Thai-first: common stress / feeling words
    "เครียด", "เหนื่อย", "ท้อ", "กังวล", "เศร้า", "เหงา",
    "โกรธ", "โมโห", "กดดัน", "หมดไฟ", "เบิร์นเอาต์", "นอนไม่หลับ",
    "ร้องไห้", "น้ำตา", "หนักใจ", "ลำบากใจ", "เกรงใจ",
    "งาน", "เจ้านาย", "หัวหน้า", "เพื่อนร่วมงาน", "ลูกค้า",
    "ครอบครัว", "พ่อ", "แม่", "แฟน", "สามี", "ภรรยา", "ลูก",
    "เงิน", "หนี้", "ค่ารถ", "รถติด", "สอบ", "เรียน", "เกรด",
]


def _load_key() -> bytes:
    env_key = os.getenv("KINDRED_KEY")
    if env_key:
        return env_key.encode()
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes().strip()
    if Fernet is None:
        raise RuntimeError("cryptography package is required (pip install -r requirements.txt)")
    key = Fernet.generate_key()
    KEY_PATH.write_bytes(key)
    return key


def extract_stressor_snippet(text: str, limit: int = 120) -> str | None:
    low = text.lower()
    if not any(w in low for w in _FEELING_WORDS):
        return None
    snippet = re.sub(r"\s+", " ", text.strip())
    return snippet[:limit]


class MemoryStore:
    def __init__(self, path: Path = DEFAULT_PATH):
        if Fernet is None:
            raise RuntimeError("Install dependencies first: pip install -r requirements.txt")
        self.path = Path(path)
        self.cipher = Fernet(_load_key())
        self.data = {"exchanges": [], "stressors": []}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = self.path.read_bytes()
            self.data = json.loads(self.cipher.decrypt(raw).decode())
        except (InvalidToken, json.JSONDecodeError, OSError):
            self.data = {"exchanges": [], "stressors": []}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        blob = self.cipher.encrypt(json.dumps(self.data).encode())
        self.path.write_bytes(blob)

    def add_exchange(self, user_text: str) -> None:
        snippet = extract_stressor_snippet(user_text)
        now = time.time()
        if snippet and snippet not in [s["text"] for s in self.data["stressors"]]:
            self.data["stressors"].append({"text": snippet, "ts": now})
            self.data["stressors"] = self.data["stressors"][-20:]
        self.data["exchanges"].append({"text": user_text[:500], "ts": now})
        self.data["exchanges"] = self.data["exchanges"][-50:]
        self.save()

    def follow_up(self, session_start: float, lang: str = "th") -> str | None:
        """Recall a stressor from a previous session, if any. Thai-first."""
        old = [s for s in self.data["stressors"] if s["ts"] < session_start]
        if not old:
            return None
        last = old[-1]["text"]
        if lang == "th":
            return (
                f"ก่อนจะเริ่มคุยกันนะคนเก่ง — คราวก่อนหนูเล่าว่า \"{last}\" "
                "วันนี้เรื่องนั้นเป็นยังไงบ้าง ยังค้างในใจอยู่ไหม?"
            )
        return (
            f"Before we begin, sweetheart — last time you mentioned \"{last}\". "
            "How has that been sitting with you today?"
        )
