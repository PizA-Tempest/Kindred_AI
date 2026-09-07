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

st.set_page_config(
    page_title="Kindred — เพื่อนใจ",
    page_icon="🕯️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Inter:wght@400;500&family=Noto+Sans+Thai:wght@300;400;500&family=Noto+Serif+Thai:wght@500;600&display=swap');

/* --- base / quiet luxury --- */
.stApp { background-color: #F9F6F0; color: #2C2A29; font-family: 'Inter', 'Noto Sans Thai', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', 'Noto Serif Thai', serif !important; color: #2C2A29; }

/* center column: comfortable on PC, full-width on mobile */
.block-container { max-width: 780px !important; margin: 0 auto; padding: 2rem 1.5rem 7rem !important; }

/* header */
.kindred-hero { text-align: center; padding: 0.5rem 0 0.25rem; }
.kindred-hero h1 { margin-bottom: 0.15rem; }
.kindred-hero p { color: #4A4A4A; margin-top: 0; }
.kindred-pill { display: inline-block; background: #E8E5DF; color: #2C2A29; border-radius: 999px;
  padding: 0.35rem 0.9rem; font-size: 0.85rem; margin: 0.4rem 0 0.8rem; }
.kindred-pill.on { background: #A3B19B; color: #fff; }

/* cards */
.kindred-card { background: #FFFFFF; border: 1px solid #E8E5DF; border-radius: 20px;
  padding: 1rem 1.1rem; box-shadow: 0 2px 12px rgba(44,42,41,0.05); margin-bottom: 0.9rem; }

/* chat bubbles */
.stChatMessage { border-radius: 18px !important; border: 1px solid #E8E5DF !important;
  background: #FFFFFF !important; box-shadow: 0 1px 6px rgba(44,42,41,0.04);
  padding: 0.6rem 0.9rem !important; margin-bottom: 0.6rem; max-width: 100%; }
[data-testid="stChatMessageAvatarUser"] + div { background: #F3E9E4 !important; }

/* touch targets: buttons / toggles / inputs */
.stButton > button { min-height: 48px !important; border-radius: 999px !important;
  font-size: 16px !important; padding: 0.6rem 1.4rem !important;
  background: #fff !important; color: #2C2A29 !important; border: 1px solid #CBAEAB !important; width: 100%; }
.stButton > button:hover { background: #CBAEAB !important; color: #fff !important; }
[data-testid="stToggle"] { min-height: 48px; }
[data-testid="stAudioInput"] button { min-height: 52px !important; min-width: 52px !important; border-radius: 999px !important; }
input, textarea, [data-testid="stChatInput"] textarea { font-size: 16px !important; } /* stops iOS zoom */
[data-testid="stChatInput"] { padding-bottom: max(1rem, env(safe-area-inset-bottom)) !important; }
[data-testid="stSegmentedControl"] button, [data-testid="stRadio"] label { min-height: 44px !important; font-size: 16px !important; }
section[data-testid="stSidebar"] { background-color: #E8E5DF; }

/* gentle breathing glow while responding */
@keyframes kindred-breathe { 0%,100% { opacity: .45; } 50% { opacity: 1; } }
.kindred-typing { animation: kindred-breathe 2.2s ease-in-out infinite; color: #4A4A4A; }

/* --- mobile --- */
@media (max-width: 768px) {
  .block-container { padding: 1rem 0.9rem 8rem !important; }
  h1 { font-size: 1.65rem !important; }
  h2 { font-size: 1.25rem !important; }
  h3 { font-size: 1.1rem !important; }
  .kindred-card { padding: 0.9rem; border-radius: 16px; }
  .stChatMessage { font-size: 16px !important; line-height: 1.65 !important; }
  /* stack Streamlit columns vertically on phones */
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] { flex: 1 1 100% !important; min-width: 100% !important; }
  [data-testid="stAudioInput"] { width: 100% !important; }
}
/* --- desktop niceties --- */
@media (min-width: 769px) {
  .kindred-hero h1 { font-size: 2.4rem; }
  .stChatMessage { font-size: 15.5px; line-height: 1.7; }
}
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
        "vent_off": "โหมดปกติ — ถ้าอยากได้คำแนะนำบอกป้าได้เลยนะ",
        "clear": "🧹 ล้างหน้าจอแชท",
        "greeting": "สวัสดีจ้ะคนเก่ง มานั่งพักกับป้าสักแป๊บนะ — วันนี้ใจเป็นยังไงบ้าง?",
        "input": "เล่าให้ป้าฟังได้เลยนะ…",
        "listening": "Kindred กำลังฟังอยู่…",
        "voice_title": "🎙️ พูดระบาย",
        "voice_hint": "กดอัดแล้วพูดได้เลย — ระบายออกมาเป็นเสียง ไม่ต้องพิมพ์",
        "transcribing": "กำลังฟังเสียงของหนู…",
        "speaking": "ป้ากำลังตอบ…",
        "voice_reply_label": "ให้ป้าตอบเป็นเสียง (🔊)",
        "privacy": "🔒 พิมพ์คุย = ส่วนตัวในเครื่องนี้. เสียงพูดจะส่งไปถอดเสียง/ออกเสียงผ่านคลาวด์ (Google/Microsoft) นะ",
        "settings": "⚙️ ตั้งค่าเพิ่มเติม",
        "chat_tab_hint": "พิมพ์หรือพูดก็ได้ ป้าอยู่ตรงนี้เสมอ",
    },
    "en": {
        "title": "Kindred 🕯️",
        "caption": "A quiet space to land. Warm, wise, and here to listen.",
        "space": "Your space",
        "lang_label": "ภาษา / Language",
        "vent_label": "Venting mode (listen only, no advice)",
        "vent_on": "Venting mode on — I'll just listen and validate. No advice, I promise.",
        "vent_off": "Venting off — ask me anytime if you'd like gentle suggestions.",
        "clear": "🧹 Clear chat view",
        "greeting": "Hello, love. Come sit with me a moment — how is your heart today?",
        "input": "Share what's on your mind…",
        "listening": "Kindred is listening…",
        "voice_title": "🎙️ Speak to vent",
        "voice_hint": "Hit record and just talk — no need to type.",
        "transcribing": "Listening to your voice…",
        "speaking": "Kindred is answering…",
        "voice_reply_label": "Reply with voice (🔊)",
        "privacy": "🔒 Typed chat stays private on this device. Voice clips go to cloud STT/TTS (Google/Microsoft).",
        "settings": "⚙️ More settings",
        "chat_tab_hint": "Type or speak — I'm right here.",
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

# ---------- Header (mobile-first, centered) ----------
# Language first so all strings follow it (Thai default).
with st.container():
    st.markdown("<div class='kindred-hero'>", unsafe_allow_html=True)
    # compact language switcher that works with big touch targets
    if hasattr(st, "segmented_control"):
        lang_choice = st.segmented_control(
            STRINGS["th"]["lang_label"],
            options=["ไทย", "English"],
            default="ไทย" if st.session_state.lang == "th" else "English",
            label_visibility="collapsed",
        )
        if lang_choice in ("ไทย", "English"):
            st.session_state.lang = "th" if lang_choice == "ไทย" else "en"
    else:
        lang_choice = st.radio(
            STRINGS["th"]["lang_label"],
            options=["ไทย", "English"],
            index=0 if st.session_state.lang == "th" else 1,
            horizontal=True,
        )
        st.session_state.lang = "th" if lang_choice == "ไทย" else "en"
    st.markdown("</div>", unsafe_allow_html=True)

T = STRINGS[st.session_state.lang]
lang = st.session_state.lang

st.markdown(
    f"<div class='kindred-hero'><h1>{T['title']}</h1><p>{T['caption']}</p>"
    f"<span class='kindred-pill {'on' if st.session_state.venting else ''}'>"
    f"{'🌿 ' + T['vent_on'] if st.session_state.venting else '🍵 ' + T['vent_off']}</span></div>",
    unsafe_allow_html=True,
)

# ---------- Main control card: vent mode front-and-center (no sidebar hunting on mobile) ----------
with st.container(border=True):
    st.markdown(f"**{T['space']}** · {T['chat_tab_hint']}")
    vent = st.toggle(T["vent_label"], value=st.session_state.venting)
    st.session_state.venting = vent
    if vent:
        st.info(T["vent_on"])
    else:
        st.caption(T["vent_off"])

# Keep a slim sidebar for desktop users who open it; mirrors the same state.
with st.sidebar:
    st.header(T["space"])
    s_vent = st.toggle(T["vent_label"], value=st.session_state.venting, key="vent_sidebar")
    st.session_state.venting = s_vent
    s_vr = st.toggle(T["voice_reply_label"], value=st.session_state.voice_reply, key="vr_sidebar")
    st.session_state.voice_reply = s_vr
    st.caption(T["privacy"])

# ---------- Speak-to-Vent card: the heart of Kindred ----------
with st.container(border=True):
    st.subheader(T["voice_title"])
    st.caption(T["voice_hint"])
    voice_clip = st.audio_input(T["voice_title"], label_visibility="collapsed")
    if not stt_available():
        st.caption("🎙️ " + voice_error("no-stt-dep", lang))
    if not tts_available():
        st.caption("🔊 " + voice_error("no-tts-dep", lang))

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

# ---------- Settings / footer (reachable on both PC + mobile) ----------
with st.expander(T["settings"]):
    vr = st.toggle(T["voice_reply_label"], value=st.session_state.voice_reply)
    st.session_state.voice_reply = vr
    if st.button(T["clear"], use_container_width=True):
        st.session_state.messages = []
        st.session_state.greeted = False
        st.session_state.voice_done = set()
        st.rerun()

st.caption(T["privacy"])
