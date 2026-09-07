"""Kindred — warm 'auntie' confidante MVP (Streamlit). Thai-first, Speak-to-Vent.

Premium popular-app design: Home ritual (greeting + mood check-in + breathe +
daily quote), Chat (voice + text), Memories (encrypted timeline + gentle stats).
Quiet Luxury theme, mobile-first, PC-friendly.
"""

import datetime
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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@400;500;600&family=Noto+Sans+Thai:wght@300;400;500&family=Noto+Serif+Thai:wght@500;600&display=swap');

.stApp { background-color: #F9F6F0; color: #2C2A29; font-family: 'Inter', 'Noto Sans Thai', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', 'Noto Serif Thai', serif !important; color: #2C2A29; }
.block-container { max-width: 860px !important; margin: 0 auto; padding: 1.2rem 1.5rem 7rem !important; }

/* fade-in on load */
@keyframes kindred-fade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.block-container > div { animation: kindred-fade .5s ease both; }

/* sticky app nav */
.kindred-nav { position: sticky; top: 0; z-index: 50; background: #F9F6F0EE; backdrop-filter: blur(8px);
  padding: .5rem 0; margin: 0 -4px .6rem; }
[data-testid="stSegmentedControl"] { width: 100%; }
[data-testid="stSegmentedControl"] button { min-height: 48px !important; font-size: 16px !important;
  border-radius: 999px !important; flex: 1; }

/* hero */
.kindred-hero { background: linear-gradient(135deg, #FFFDF8 0%, #F3EEE5 55%, #E8E5DF 100%);
  border: 1px solid #E8E5DF; border-radius: 28px; padding: 1.6rem 1.4rem 1.3rem; text-align: center;
  box-shadow: 0 8px 30px rgba(44,42,41,.07); margin-bottom: 1rem; position: relative; overflow: hidden; }
.kindred-hero h1 { margin: .2rem 0 .1rem; letter-spacing: .2px; }
.kindred-hero p { color: #4A4A4A; margin: .1rem 0 .4rem; }
@keyframes kindred-glow { 0%,100% { transform: scale(1); opacity: .7; } 50% { transform: scale(1.12); opacity: 1; } }
.kindred-candle { font-size: 2.6rem; display: inline-block; animation: kindred-glow 3.2s ease-in-out infinite;
  filter: drop-shadow(0 0 14px rgba(203,174,171,.8)); }
.kindred-pill { display: inline-block; background: #E8E5DF; color: #2C2A29; border-radius: 999px;
  padding: .35rem .95rem; font-size: .85rem; margin: .25rem .2rem; }
.kindred-pill.on { background: #A3B19B; color: #fff; }
.kindred-pill.streak { background: #fff; border: 1px solid #CBAEAB; }

/* section titles */
.kindred-section { font-family: 'Playfair Display','Noto Serif Thai',serif; font-size: 1.15rem; margin: 1.1rem 0 .5rem; }

/* mood buttons: big, tappable, popular-app style */
[data-testid="column"] .stButton > button { font-size: 1.5rem !important; line-height: 1.2 !important;
  padding: .7rem .2rem !important; }
.mood-label { text-align: center; font-size: .78rem; color: #4A4A4A; margin-top: -6px; }

/* breathe */
@keyframes kindred-breathe-circle { 0%,100% { transform: scale(.82); } 50% { transform: scale(1.08); } }
.kindred-breathe-wrap { display: flex; align-items: center; gap: 1rem; }
.kindred-breathe-circle { width: 92px; height: 92px; border-radius: 50%; flex: none;
  background: radial-gradient(circle at 35% 35%, #DCE4D6, #A3B19B);
  animation: kindred-breathe-circle 8s ease-in-out infinite;
  box-shadow: 0 0 0 10px #A3B19B22, 0 0 0 22px #A3B19B11; }

/* quote */
.kindred-quote { border-left: 3px solid #CBAEAB; padding: .2rem 0 .2rem .9rem; color: #4A4A4A;
  font-style: italic; margin: .4rem 0; }

/* chat bubbles */
.stChatMessage { border-radius: 20px !important; border: 1px solid #E8E5DF !important;
  background: #FFFFFF !important; box-shadow: 0 1px 6px rgba(44,42,41,.04);
  padding: .6rem .95rem !important; margin-bottom: .6rem; max-width: 100%; }
[data-testid="stChatMessageAvatarUser"] + div { background: #F6ECE7 !important; }

/* touch targets */
.stButton > button { min-height: 48px !important; border-radius: 999px !important;
  font-size: 16px !important; border: 1px solid #CBAEAB !important;
  background: #fff !important; color: #2C2A29 !important; }
.stButton > button:hover { background: #CBAEAB !important; color: #fff !important; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: #A3B19B !important; border-color: #A3B19B !important; color: #fff !important; }
[data-testid="stToggle"] { min-height: 48px; }
[data-testid="stAudioInput"] button { min-height: 54px !important; min-width: 54px !important; border-radius: 999px !important; }
input, textarea, [data-testid="stChatInput"] textarea { font-size: 16px !important; }
[data-testid="stChatInput"] { padding-bottom: max(1rem, env(safe-area-inset-bottom)) !important; }
section[data-testid="stSidebar"] { background-color: #E8E5DF; }

@keyframes kindred-breathe { 0%,100% { opacity: .45; } 50% { opacity: 1; } }
.kindred-typing { animation: kindred-breathe 2.2s ease-in-out infinite; color: #4A4A4A; }

/* memory timeline */
.kindred-memory { background: #fff; border: 1px solid #E8E5DF; border-radius: 16px;
  padding: .7rem .95rem; margin-bottom: .55rem; }
.kindred-memory small { color: #8a8580; }
.kindred-stat { text-align: center; }
.kindred-stat b { font-size: 1.5rem; font-family: 'Playfair Display',serif; display: block; }
.kindred-stat span { font-size: .8rem; color: #4A4A4A; }

@media (max-width: 768px) {
  .block-container { padding: .9rem .85rem 8rem !important; }
  h1 { font-size: 1.7rem !important; }
  .kindred-hero { border-radius: 22px; padding: 1.2rem .95rem 1rem; }
  .kindred-candle { font-size: 2.1rem; }
  .kindred-breathe-circle { width: 76px; height: 76px; }
  .stChatMessage { font-size: 16px !important; line-height: 1.65 !important; }
  [data-testid="stAudioInput"] { width: 100% !important; }
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

STRINGS = {
    "th": {
        "tagline": "พื้นที่เงียบ ๆ ให้ใจได้พัก อบอุ่น เข้าใจ และรับฟังเสมอ",
        "lang_label": "ภาษา / Language",
        "nav_home": "🏠 โฮม", "nav_chat": "💬 คุยกับป้า", "nav_mem": "🌙 ความทรงจำ",
        "morning": "สวัสดียามเช้าจ้ะคนเก่ง ☀️", "afternoon": "สวัสดีตอนบ่ายจ้ะคนเก่ง 🌤️",
        "evening": "สวัสดีตอนค่ำจ้ะคนเก่ง 🌙",
        "hero_sub": "วันนี้ใจเป็นยังไงบ้าง? แวะพักตรงนี้ก่อนได้นะ",
        "vent_label": "โหมดระบาย (แค่รับฟัง ไม่แนะนำ)",
        "vent_on": "🌿 โหมดระบาย: ป้าแค่ฟัง ไม่แนะนำ",
        "vent_off": "🍵 โหมดปกติ: ขอคำแนะนำได้เลย",
        "vent_on_long": "เปิดโหมดระบายแล้วนะ — ป้าจะแค่ฟังและเข้าใจ ไม่แนะนำอะไรเลย สัญญา",
        "days": "วันที่แวะมา", "chats": "ครั้งที่เล่าให้ฟัง", "themes": "เรื่องในใจ",
        "mood_title": "เช็กอินหัวใจวันนี้",
        "mood_sub": "แตะตามความรู้สึกตอนนี้ได้เลย — ไม่มีผิดถูก",
        "moods": [("🌤️", "เบา ๆ"), ("🙂", "โอเค"), ("😐", "เฉย ๆ"), ("😔", "หนัก ๆ"), ("😭", "อยากร้อง")],
        "mood_saved": "บันทึกแล้วนะ ป้าอยู่ตรงนี้กับหนูเสมอ",
        "breathe_title": "พักหายใจ 1 นาที",
        "breathe_sub": "หายใจเข้าทางจมูก 4 วินาที… กลั้นไว้ 4… แล้วผ่อนออกยาว ๆ ทางปาก",
        "breathe_in": "หายใจเข้า…",
        "quote_title": "คำเบา ๆ ประจำวัน",
        "quotes": [
            "พักได้โดยไม่ต้องรู้สึกผิดนะ คนเก่ง",
            "ใจที่เหนื่อยก็ต้องการที่พักเหมือนกัน",
            "ไม่ต้องรีบหาย แค่ค่อย ๆ ดีขึ้นก็พอ",
            "เล่าออกมาได้เลย ป้าฟังอยู่ตรงนี้",
            "วันนี้แค่ผ่านไปได้ก็เก่งมากแล้ว",
        ],
        "cta": "💬 เริ่มคุยกับป้า",
        "voice_title": "🎙️ พูดระบาย",
        "voice_hint": "กดอัดแล้วพูดได้เลย — ระบายออกมาเป็นเสียง ไม่ต้องพิมพ์",
        "transcribing": "กำลังฟังเสียงของหนู…",
        "speaking": "ป้ากำลังตอบ…",
        "greeting": "สวัสดีจ้ะคนเก่ง มานั่งพักกับป้าสักแป๊บนะ — วันนี้ใจเป็นยังไงบ้าง?",
        "input": "เล่าให้ป้าฟังได้เลยนะ…",
        "listening": "Kindred กำลังฟังอยู่…",
        "voice_reply_label": "ให้ป้าตอบเป็นเสียง (🔊)",
        "privacy": "🔒 พิมพ์คุย = ส่วนตัวในเครื่องนี้ (เข้ารหัส). เสียงพูดจะส่งไปถอดเสียง/ออกเสียงผ่านคลาวด์ (Google/Microsoft) นะ",
        "settings": "⚙️ ตั้งค่าเพิ่มเติม",
        "clear": "🧹 ล้างหน้าจอแชท",
        "mem_title": "ป้าจำได้นะ",
        "mem_sub": "เรื่องที่เคยเล่าไว้ ป้าเก็บไว้อย่างปลอดภัยในเครื่องนี้",
        "mem_empty": "ยังไม่มีเรื่องที่บันทึกไว้ — เล่าให้ป้าฟังครั้งแรกได้เลยนะ",
        "mem_enc": "🔐 เข้ารหัสในเครื่องนี้",
        "space": "พื้นที่ของเธอ",
    },
    "en": {
        "tagline": "A quiet space to land. Warm, wise, and here to listen.",
        "lang_label": "ภาษา / Language",
        "nav_home": "🏠 Home", "nav_chat": "💬 Chat", "nav_mem": "🌙 Memories",
        "morning": "Good morning, love ☀️", "afternoon": "Good afternoon, love 🌤️",
        "evening": "Good evening, love 🌙",
        "hero_sub": "How is your heart today? Come rest here a while.",
        "vent_label": "Venting mode (listen only, no advice)",
        "vent_on": "🌿 Venting: just listening, no advice",
        "vent_off": "🍵 Open mode: gentle advice welcome",
        "vent_on_long": "Venting mode on — I'll just listen and validate. No advice, I promise.",
        "days": "days visited", "chats": "times shared", "themes": "heart themes",
        "mood_title": "Today's heart check-in",
        "mood_sub": "Tap what matches right now — no wrong answers.",
        "moods": [("🌤️", "Light"), ("🙂", "Okay"), ("😐", "Meh"), ("😔", "Heavy"), ("😭", "Tearful")],
        "mood_saved": "Saved, love. I'm right here with you.",
        "breathe_title": "One-minute breather",
        "breathe_sub": "In through the nose for 4… hold for 4… release slowly through the mouth.",
        "breathe_in": "Breathe in… out…",
        "quote_title": "A gentle daily note",
        "quotes": [
            "Rest is allowed — no guilt needed.",
            "A tired heart needs shelter too.",
            "No rush to heal. Slowly is fine.",
            "Tell me anything. I'm listening.",
            "Getting through today is already brave.",
        ],
        "cta": "💬 Talk with Kindred",
        "voice_title": "🎙️ Speak to vent",
        "voice_hint": "Hit record and just talk — no need to type.",
        "transcribing": "Listening to your voice…",
        "speaking": "Kindred is answering…",
        "greeting": "Hello, love. Come sit with me a moment — how is your heart today?",
        "input": "Share what's on your mind…",
        "listening": "Kindred is listening…",
        "voice_reply_label": "Reply with voice (🔊)",
        "privacy": "🔒 Typed chat stays encrypted on this device. Voice clips go to cloud STT/TTS (Google/Microsoft).",
        "settings": "⚙️ More settings",
        "clear": "🧹 Clear chat view",
        "mem_title": "I remember, sweetheart",
        "mem_sub": "Things you've shared — kept safely encrypted on this device.",
        "mem_empty": "Nothing saved yet — share your first story whenever you're ready.",
        "mem_enc": "🔐 Encrypted on this device",
        "space": "Your space",
    },
}

# ---------- session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "venting" not in st.session_state:
    st.session_state.venting = True  # Vent-first: the point of Kindred.
if "voice_reply" not in st.session_state:
    st.session_state.voice_reply = True
if "voice_done" not in st.session_state:
    st.session_state.voice_done = set()
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()
if "greeted" not in st.session_state:
    st.session_state.greeted = False
if "lang" not in st.session_state:
    st.session_state.lang = "th"
if "nav" not in st.session_state:
    st.session_state.nav = "home"
if "mood_today" not in st.session_state:
    st.session_state.mood_today = None


@st.cache_resource
def get_memory() -> MemoryStore:
    return MemoryStore()


mem = get_memory()

# ---------- top bar:lang (compact, mobile-friendly) ----------
top_l, top_r = st.columns([3, 2])
with top_l:
    st.markdown("**Kindred 🕯️**")
with top_r:
    if hasattr(st, "segmented_control"):
        _lc = st.segmented_control(
            STRINGS["th"]["lang_label"],
            options=["ไทย", "English"],
            default="ไทย" if st.session_state.lang == "th" else "English",
            label_visibility="collapsed",
        )
        if _lc in ("ไทย", "English"):
            st.session_state.lang = "th" if _lc == "ไทย" else "en"
    else:
        _lc = st.radio(
            STRINGS["th"]["lang_label"], ["ไทย", "English"],
            index=0 if st.session_state.lang == "th" else 1, horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state.lang = "th" if _lc == "ไทย" else "en"

T = STRINGS[st.session_state.lang]
lang = st.session_state.lang

# ---------- sticky nav (popular-app tab bar) ----------
st.markdown("<div class='kindred-nav'>", unsafe_allow_html=True)
_nav_opts = [T["nav_home"], T["nav_chat"], T["nav_mem"]]
_nav_cur = {"home": _nav_opts[0], "chat": _nav_opts[1], "mem": _nav_opts[2]}[st.session_state.nav]
if hasattr(st, "segmented_control"):
    _nav = st.segmented_control("nav", options=_nav_opts, default=_nav_cur, label_visibility="collapsed")
else:
    _nav = st.radio("nav", options=_nav_opts, index=_nav_opts.index(_nav_cur), horizontal=True, label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)
if _nav == _nav_opts[0]:
    st.session_state.nav = "home"
elif _nav == _nav_opts[2]:
    st.session_state.nav = "mem"
else:
    st.session_state.nav = "chat"
nav = st.session_state.nav

# ---------- helpers ----------
def _time_of_day() -> str:
    h = datetime.datetime.now().hour
    if h < 11:
        return T["morning"]
    if h < 17:
        return T["afternoon"]
    return T["evening"]


def _stats():
    ex = mem.data.get("exchanges", [])
    st_ = mem.data.get("stressors", [])
    days = len({datetime.datetime.fromtimestamp(e["ts"]).date() for e in ex}) if ex else (1 if st_ else 0)
    return max(days, 1 if (ex or st_) else 0), len(ex), len(st_)


def _timeago(ts: float) -> str:
    mins = max(1, int((time.time() - ts) // 60))
    if lang == "th":
        if mins < 60:
            return f"{mins} นาทีที่แล้ว"
        hrs = mins // 60
        if hrs < 24:
            return f"{hrs} ชม. ที่แล้ว"
        return f"{hrs // 24} วันที่แล้ว"
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h ago"
    return f"{hrs // 24}d ago"


def _daily_quote() -> str:
    doy = datetime.date.today().timetuple().tm_yday
    return T["quotes"][doy % len(T["quotes"])]


def _handle_voice_clip(voice_clip) -> None:
    raw = voice_clip.getvalue()
    clip_id = hashlib.md5(raw).hexdigest()
    if clip_id in st.session_state.voice_done:
        return
    st.session_state.voice_done.add(clip_id)
    with st.spinner(T["transcribing"]):
        heard, err = transcribe(raw, lang=lang)
    if err or not heard:
        st.session_state.messages.append({"role": "assistant", "content": voice_error(err or "error", lang)})
        return
    st.session_state.messages.append({"role": "user", "content": f"🎙️ {heard}"})
    mem.add_exchange(heard)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages if m["role"] in ("user", "assistant")
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


# Cross-session follow-up, once per session (persona: contextual memory).
if not st.session_state.greeted:
    st.session_state.greeted = True
    follow = mem.follow_up(st.session_state.session_start, lang=lang)
    st.session_state.messages.append(
        {"role": "assistant", "content": follow if follow else T["greeting"]}
    )

# ============================================================ HOME
if nav == "home":
    _days, _chats, _themes = _stats()
    st.markdown(
        "<div class='kindred-hero'>"
        "<span class='kindred-candle'>🕯️</span>"
        f"<h1>{_time_of_day()}</h1><p>{T['hero_sub']}</p>"
        f"<span class='kindred-pill {'on' if st.session_state.venting else ''}'>"
        f"{T['vent_on'] if st.session_state.venting else T['vent_off']}</span>"
        f"<span class='kindred-pill streak'>🔥 {_days} {T['days']} · 💬 {_chats} {T['chats']}</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(f"<div class='kindred-section'>{T['mood_title']}</div>", unsafe_allow_html=True)
        st.caption(T["mood_sub"])
        cols = st.columns(5)
        for i, (emoji, label) in enumerate(T["moods"]):
            with cols[i]:
                if st.button(emoji, key=f"mood_{i}", use_container_width=True):
                    mood_text = f"{emoji} {label}"
                    mem.add_exchange(f"Mood check-in: {mood_text}")
                    st.session_state.mood_today = mood_text
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages if m["role"] in ("user", "assistant")
                    ]
                    reply, _ = generate(mood_text, history, st.session_state.venting, lang=lang)
                    st.session_state.messages.append({"role": "user", "content": mood_text})
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.toast(T["mood_saved"])
                st.markdown(f"<div class='mood-label'>{label}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"<div class='kindred-section'>{T['breathe_title']}</div>", unsafe_allow_html=True)
        st.caption(T["breathe_sub"])
        st.markdown(
            "<div class='kindred-breathe-wrap'><div class='kindred-breathe-circle'></div>"
            f"<div><b>{T['breathe_in']}</b><br><small>4 · 4 · 6 — slow & gentle</small></div></div>",
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(f"<div class='kindred-section'>{T['quote_title']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kindred-quote'>{_daily_quote()}</div>", unsafe_allow_html=True)
        if st.button(T["cta"], type="primary", use_container_width=True):
            st.session_state.nav = "chat"
            st.rerun()

    st.caption(T["privacy"])

# ============================================================ CHAT
elif nav == "chat":
    with st.container(border=True):
        st.markdown(f"**{T['space']}**")
        vent = st.toggle(T["vent_label"], value=st.session_state.venting)
        st.session_state.venting = vent
        if vent:
            st.info(T["vent_on_long"])

    with st.container(border=True):
        st.subheader(T["voice_title"])
        st.caption(T["voice_hint"])
        voice_clip = st.audio_input(T["voice_title"], label_visibility="collapsed")
        if not stt_available():
            st.caption("🎙️ " + voice_error("no-stt-dep", lang))
        if not tts_available():
            st.caption("🔊 " + voice_error("no-tts-dep", lang))
    if voice_clip is not None:
        _handle_voice_clip(voice_clip)

    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/mp3",
                         autoplay=(i == len(st.session_state.messages) - 1))

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
                st.markdown(f"<span class='kindred-typing'>{T['listening']}</span>",
                            unsafe_allow_html=True)
                reply, _ = generate(prompt, history, st.session_state.venting, lang=lang)
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.expander(T["settings"]):
        vr = st.toggle(T["voice_reply_label"], value=st.session_state.voice_reply)
        st.session_state.voice_reply = vr
        if st.button(T["clear"], use_container_width=True):
            st.session_state.messages = []
            st.session_state.greeted = False
            st.session_state.voice_done = set()
            st.rerun()
    st.caption(T["privacy"])

# ============================================================ MEMORIES
else:
    _days, _chats, _themes = _stats()
    st.markdown(f"<div class='kindred-section'>{T['mem_title']}</div>", unsafe_allow_html=True)
    st.caption(f"{T['mem_sub']} · {T['mem_enc']}")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        for c, val, lab in ((c1, _days, T["days"]), (c2, _chats, T["chats"]), (c3, _themes, T["themes"])):
            with c:
                st.markdown(f"<div class='kindred-stat'><b>{val}</b><span>{lab}</span></div>",
                            unsafe_allow_html=True)

    stressors = list(reversed(mem.data.get("stressors", [])))
    if not stressors:
        with st.container(border=True):
            st.markdown(f"🌱 {T['mem_empty']}")
            if st.button(T["cta"], type="primary", use_container_width=True):
                st.session_state.nav = "chat"
                st.rerun()
    else:
        for s in stressors[:15]:
            st.markdown(
                f"<div class='kindred-memory'>🌿 {s['text']}<br><small>{_timeago(s['ts'])}</small></div>",
                unsafe_allow_html=True,
            )

    with st.expander(T["settings"]):
        if st.button(T["clear"], use_container_width=True):
            st.session_state.messages = []
            st.session_state.greeted = False
            st.session_state.voice_done = set()
            st.rerun()
    st.caption(T["privacy"])

# Slim sidebar mirror for desktop users.
with st.sidebar:
    st.header(T["space"])
    s_vent = st.toggle(T["vent_label"], value=st.session_state.venting, key="vent_sidebar")
    st.session_state.venting = s_vent
    s_vr = st.toggle(T["voice_reply_label"], value=st.session_state.voice_reply, key="vr_sidebar")
    st.session_state.voice_reply = s_vr
    st.caption(T["privacy"])
