# AGENTS.md — Kindred_AI

## Current state
- Greenfield: no code, build, test, or lint config yet. Only source of truth is `project_proposal_kindred_ai.md` — read it first.
- No `README`, manifests, lockfiles, CI, or `opencode.json` as of 2026-09-06. Do not assume a stack (parent folder name suggests Java, but nothing in-repo confirms it).
- When a stack/build is added, update this file with exact commands.

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
- Do not invent toolchain commands; if you introduce one (Maven/Gradle/npm/etc.), document the exact verify command here.
- Keep privacy/latency/persona impact in mind for any dependency or architecture choice.
