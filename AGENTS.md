# AGENTS.md — Kindred_AI

## Current state
- Stack: Python + Streamlit web MVP (`app.py` entrypoint, `kindred/` lib). Proposal doc is product source of truth.
- Verify: `python test_kindred.py` (persona rules) · run: `python -m streamlit run app.py`

## Product constraints (from proposal — do not dilute)
- Persona: warm, wise "auntie" confidante. Validate feelings first, every turn.
- No unsolicited advice unless explicitly asked. Venting mode: listen + validate only, advice strictly disabled.
- Contextual memory required: recall past stressors, follow up across sessions.
- Tone: warm/comforting, never clinical/robotic; gentle encouragement, no toxic positivity.
- Non-functionals: end-to-end encrypted conversation logs; ≤1.5s response latency feel.

## UI — 'Quiet Luxury' (when building frontend)
- Backgrounds: Cashmere Cream `#F9F6F0` / Soft Taupe `#E8E5DF`; text: Deep Espresso `#2C2A29` / Slate Grey `#4A4A4A`; accents: Muted Sage `#A3B19B` / Dusty Rose `#CBAEAB`.
- Headers: serif (`Playfair Display` or `Lora`); body/chat: clean sans (`Inter` or `Proxima Nova`).
- Minimal clutter, soft rounded bubbles, slow/gentle micro-interactions only.

## Workflow
- Setup: `pip install -r requirements.txt`. Memory encryption key auto-generates to `.kindred.key` (gitignored) or set `KINDRED_KEY`; logs in `data/` (gitignored).
- Optional LLM: set `KINDRED_API_URL` + `KINDRED_API_KEY` (OpenAI-compatible `/chat/completions`); unset = warm local fallback. Never let LLM break venting-mode silence on advice.
- Keep privacy/latency/persona impact in mind for any dependency or architecture choice.
