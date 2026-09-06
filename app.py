"""Kindred — warm 'auntie' confidante MVP (Streamlit). Thai-first, Speak-to-Vent."""

import hashlib
import time

import streamlit as st

from kindred.memory import MemoryStore
from kindred.responder import generate
from kindred.voice import (
    stt_available,
    synthesize,
    transcribe,
    tts_available,
    voice_error,
)

st.set_page_config(page_title="Kindred — เพื่อนใจ", page_icon="🕯️", layout="centered")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Inter:wght@400;500&family=Noto+Sans+Thai:wght@300;400;500&family=Noto+Serif+Thai:wght@500;600&display=swap');
.stApp { background-color: #F9F6F0; color: #2C2A29; font-family: 'Inter', 'Noto Sans Thai', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', 'Noto Serif Thai', serif !important; color: #2C2A29; }
.stChatMessage { border-radius: 18px !important; }
section[data-testid="stSidebar"] { background-color: #E8E5DF; }
/* gentle breathing glow while responding */
@keyframes kindred-breathe { 0%,100% { opacity: .45; } 50% { opacity: 1; } }
.kindred-typing { animation: kindred-breathe 2.2s ease-in-out infinite; color: #4A4A4A; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

STRINGS = {
    "th": {
        "title": "Kindred 🕯️",
        "caption": "พื้นที่เงียบ ๆ ให้ใจได้พัก อบอุ่น เข้าใจ และรับฟังเสมอ",
        "space": "พื้นที่ของเธอ",
        "lang_label": "ภาษา / Language",
        "vent_label": "โหมดระบาย (แค่รับฟัง ไม่แนะนำ)",
        "vent_on": "เปิดโหมดระบายแล้วนะ — ป้าจะแค่ฟังและเข้าใจ ไม่แนะนำอะไรเลย สัญญา",
        "clear": "ล้างหน้าจอแชท",
        "greeting": "สวัสดีจ้ะคนเก่ง มานั่งพักกับป้าสักแป๊บนะ — วันนี้ใจเป็นยังไงบ้าง?",
        "input": "เล่าให้ป้าฟังได้เลยนะ…",
        "listening": "Kindred กำลังฟังอยู่…",
        "voice_title": "🎙️ พูดระบาย",
        "voice_hint": "กดอัดแล้วพูดได้เลย — ระบายออกมาเป็นเสียง ไม่ต้องพิมพ์",
        "transcribing": "กำลังฟังเสียงของหนู…",
        "speaking": "ป้ากำลังตอบ…",
        "voice_reply_label": "ให้ป้าตอบเป็นเสียง (🔊)",
        "privacy": "🔒 พิมพ์คุย = ส่วนตัวในเครื่องนี้. เสียงพูดจะส่งไปถอดเสียง/ออกเสียงผ่านคลาวด์ (Google/Microsoft) นะ",
    },
    "en": {
        "title": "Kindred 🕯️",
        "caption": "A quiet space to land. Warm, wise, and here to listen.",
        "space": "Your space",
        "lang_label": "ภาษา / Language",
        "vent_label": "Venting mode (listen only, no advice)",
        "vent_on": "Venting mode on — I'll just listen and validate. No advice, I promise.",
        "clear": "Clear chat view",
        "greeting": "Hello, love. Come sit with me a moment — how is your heart today?",
        "input": "Share what's on your mind…",
        "listening": "Kindred is listening…",
        "voice_title": "🎙️ Speak to vent",
        "voice_hint": "Hit record and just talk — no need to type.",
        "transcribing": "Listening to your voice…",
        "speaking": "Kindred is answering…",
        "voice_reply_label": "Reply with voice (🔊)",
        "privacy": "🔒 Typed chat stays private on this device. Voice clips go to cloud STT/TTS (Google/Microsoft).",
    },
}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "venting" not in st.session_state:
    # Vent-first: speaking to vent is the main point of Kindred.
    st.session_state.venting = True
if "voice_reply" not in st.session_state:
    st.session_state.voice_reply = True
if "voice_done" not in st.session_state:
    st.session_state.voice_done = set()
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()
if "greeted" not in st.session_state:
    st.session_state.greeted = False
if "lang" not in st.session_state:
    st.session_state.lang = "th"  # Thai-first default


@st.cache_resource
def get_memory() -> MemoryStore:
    return MemoryStore()


mem = get_memory()

# Language selector first so all strings follow it (Thai default).
with st.sidebar:
    lang_choice = st.radio(
        STRINGS["th"]["lang_label"],
        options=["ไทย", "English"],
        index=0 if st.session_state.lang == "th" else 1,
    )
    st.session_state.lang = "th" if lang_choice == "ไทย" else "en"

T = STRINGS[st.session_state.lang]
lang = st.session_state.lang

st.title(T["title"])
st.caption(T["caption"])

with st.sidebar:
    st.header(T["space"])
    vent = st.toggle(T["vent_label"], value=st.session_state.venting)
    st.session_state.venting = vent
    if vent:
        st.info(T["vent_on"])
    vr = st.toggle(T["voice_reply_label"], value=st.session_state.voice_reply)
    st.session_state.voice_reply = vr
    if st.button(T["clear"]):
        st.session_state.messages = []
        st.session_state.greeted = False
        st.session_state.voice_done = set()
        st.rerun()
    st.caption(T["privacy"])

# --- Speak-to-Vent: the heart of Kindred. Record -> transcribe -> auntie answers. ---
st.subheader(T["voice_title"])
st.caption(T["voice_hint"])
voice_clip = st.audio_input(T["voice_title"], label_visibility="collapsed")
if not stt_available():
    st.caption("🎙️ " + voice_error("no-stt-dep", lang))
if voice_clip is not None:
    raw = voice_clip.getvalue()
    clip_id = hashlib.md5(raw).hexdigest()
    if clip_id not in st.session_state.voice_done:
        st.session_state.voice_done.add(clip_id)
        with st.spinner(T["transcribing"]):
            heard, err = transcribe(raw, lang=lang)
        if err or not heard:
            st.session_state.messages.append(
                {"role": "assistant", "content": voice_error(err or "error", lang)}
            )
        else:
            st.session_state.messages.append({"role": "user", "content": f"🎙️ {heard}"})
            mem.add_exchange(heard)
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
                if m["role"] in ("user", "assistant")
            ][:-1]
            with st.spinner(T["speaking"]):
                reply, _ = generate(heard, history, st.session_state.venting, lang=lang)
            msg = {"role": "assistant", "content": reply}
            if st.session_state.voice_reply:
                with st.spinner(T["speaking"]):
                    audio, aerr = synthesize(reply, lang=lang)
                if audio:
                    msg["audio"] = audio
                else:
                    msg["content"] = reply + f"\n\n_({voice_error(aerr or 'error', lang)})_"
            st.session_state.messages.append(msg)

# Cross-session follow-up, once per session
if not st.session_state.greeted:
    st.session_state.greeted = True
    follow = mem.follow_up(st.session_state.session_start, lang=lang)
    if follow:
        st.session_state.messages.append({"role": "assistant", "content": follow})
    else:
        st.session_state.messages.append({"role": "assistant", "content": T["greeting"]})

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("audio"):
            # Autoplay only the latest reply so old messages don't replay.
            st.audio(
                m["audio"],
                format="audio/mp3",
                autoplay=(i == len(st.session_state.messages) - 1),
            )

prompt = st.chat_input(T["input"])
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    mem.add_exchange(prompt)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages if m["role"] in ("user", "assistant")
    ][:-1]
    with st.chat_message("assistant"):
        with st.spinner(""):
            st.markdown(
                f"<span class='kindred-typing'>{T['listening']}</span>",
                unsafe_allow_html=True,
            )
            reply, _ = generate(prompt, history, st.session_state.venting, lang=lang)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
