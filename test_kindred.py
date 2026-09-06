"""Minimal persona-rule checks: run with `python test_kindred.py`."""

from kindred.persona import is_asking_for_advice
from kindred.responder import local_response

ADVICE_MARKERS = ("you should", "i suggest", "try this exercise", "action step", "do this")


def test_venting_never_gives_advice():
    r = local_response("Should I quit my job? Give me advice!", venting=True).lower()
    assert not any(m in r for m in ADVICE_MARKERS), r
    assert "no fixing" in r or "just listening" in r, r


def test_normal_mode_withholds_advice_unless_asked():
    r = local_response("Work was awful today, I'm so tired.", venting=False).lower()
    assert not any(m in r for m in ADVICE_MARKERS), r
    assert "just ask" in r, r  # invites asking before advising


def test_normal_mode_advises_only_when_asked():
    assert is_asking_for_advice("What should I do about my boss? Any suggestions?")
    r = local_response("What should I do about my boss? Any suggestions?", venting=False)
    assert "gentle thought" in r.lower(), r


def test_validation_comes_first():
    for t in ("I'm overwhelmed.", "Should I quit? Advise me."):
        for venting in (True, False):
            r = local_response(t, venting=venting)
            first = r.split(".")[0].lower()
            assert any(w in first for w in ("sounds", "understand", "makes", "glad")), r


if __name__ == "__main__":
    test_venting_never_gives_advice()
    test_normal_mode_withholds_advice_unless_asked()
    test_normal_mode_advises_only_when_asked()
    test_validation_comes_first()
    print("All Kindred persona checks passed.")
