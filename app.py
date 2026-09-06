"""Kindred — warm 'auntie' confidante MVP (Streamlit)."""

import time

import streamlit as st

from kindred.memory import MemoryStore
from kindred.responder import generate

st.set_page_config(page_title="Kindred", page_icon="🕯️", layout="centered")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Inter:wght@400;500&display=swap');
.stApp { background-color: #F9F6F0; color: #2C2A29; font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #2C2A29; }
.stChatMessage { border-radius: 18px !important; }
section[data-testid="stSidebar"] { background-color: #E8E5DF; }
/* gentle breathing glow while responding */
@keyframes kindred-breathe { 0%,100% { opacity: .45; } 50% { opacity: 1; } }
.kindred-typing { animation: kindred-breathe 2.2s ease-in-out infinite; color: #4A4A4A; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "venting" not in st.session_state:
    st.session_state.venting = False
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()
if "greeted" not in st.session_state:
    st.session_state.greeted = False


@st.cache_resource
def get_memory() -> MemoryStore:
    return MemoryStore()


mem = get_memory()

st.title("Kindred 🕯️")
st.caption("A quiet space to land. Warm, wise, and here to listen.")

with st.sidebar:
    st.header("Your space")
    vent = st.toggle("Venting mode (listen only, no advice)", value=st.session_state.venting)
    st.session_state.venting = vent
    if vent:
        st.info("Venting mode on — I'll just listen and validate. No advice, I promise.")
    if st.button("Clear chat view"):
        st.session_state.messages = []
        st.rerun()

# Cross-session follow-up, once per session
if not st.session_state.greeted:
    st.session_state.greeted = True
    follow = mem.follow_up(st.session_state.session_start)
    if follow:
        st.session_state.messages.append({"role": "assistant", "content": follow})
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello, love. Come sit with me a moment — how is your heart today?",
        })

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Share what's on your mind…")
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
                "<span class='kindred-typing'>Kindred is listening…</span>",
                unsafe_allow_html=True,
            )
            reply, _ = generate(prompt, history, st.session_state.venting)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
