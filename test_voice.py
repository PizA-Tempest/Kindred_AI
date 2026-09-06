"""Voice checks (offline-safe): run with `python test_voice.py` or pytest."""

from kindred.voice import (
    STT_LANGS,
    VOICES,
    stt_available,
    synthesize,
    transcribe,
    tts_available,
    voice_error,
)


def test_transcribe_empty_never_raises():
    text, err = transcribe(b"", lang="th")
    assert text is None and err == "empty"


def test_transcribe_garbage_never_raises():
    # Invalid WAV bytes: must return a friendly error key, never raise,
    # and work fully offline (fails at local parse, before any network).
    text, err = transcribe(b"\x00\x01not-a-wav-file", lang="th")
    assert text is None and isinstance(err, str)


def test_synthesize_empty_never_raises():
    audio, err = synthesize("   ", lang="th")
    assert audio is None and err == "empty"


def test_synthesize_graceful_without_network_or_dep():
    # No edge-tts installed here / no network: must degrade gracefully.
    audio, err = synthesize("วันนี้เหนื่อยมากเลย", lang="th")
    assert err is None or audio is None  # either speaks or explains, never crashes
    if err:
        assert isinstance(voice_error(err, "th"), str)


def test_thai_voices_configured():
    assert VOICES["th"].startswith("th-TH-")
    assert VOICES["en"].startswith("en-")
    assert STT_LANGS == {"th": "th-TH", "en": "en-US"}


def test_voice_errors_thai_first():
    assert "ป้า" in voice_error("unclear", "th") or "ฟัง" in voice_error("unclear", "th")
    assert isinstance(voice_error("network", "en"), str)


def test_availability_flags_are_bool():
    assert isinstance(stt_available(), bool)
    assert isinstance(tts_available(), bool)


if __name__ == "__main__":
    test_transcribe_empty_never_raises()
    test_transcribe_garbage_never_raises()
    test_synthesize_empty_never_raises()
    test_synthesize_graceful_without_network_or_dep()
    test_thai_voices_configured()
    test_voice_errors_thai_first()
    test_availability_flags_are_bool()
    print("All Kindred voice checks passed.")
