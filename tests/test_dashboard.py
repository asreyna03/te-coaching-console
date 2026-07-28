"""Client dashboard suite: role-routed Home, streak/week math, due/done
states, the coach-note block, and the coach-side note input.

Run:  python3 tests/test_dashboard.py
"""
import contextlib
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl

HOME = os.path.join(ROOT, "app.py")
NAME = "Dash Test"
TODAY = date.today()


@contextlib.contextmanager
def env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update(kv)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _seed(**extra):
    rec = {
        "start_date": (TODAY - timedelta(days=22)).isoformat(),   # week 4
        "goals": "Build muscle",
        "coach": "Eric",
        "bodyweight": "175 lbs",
        "targets": {"Training Day": {"cal": 2814, "protein": 219,
                                     "fats": 80, "carbs": 300}},
        "weighins": [
            {"Date": (TODAY - timedelta(days=8)).isoformat(),
             "Weight": "173.2", "Steps": "9000", "Sleep (hrs)": "7"},
            {"Date": (TODAY - timedelta(days=1)).isoformat(),
             "Weight": "175.1", "Steps": "11000", "Sleep (hrs)": "7.5"},
        ],
    }
    rec.update(extra)
    cl.upsert_client(NAME, rec)


def _client_home():
    at = AppTest.from_file(HOME, default_timeout=40)
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = NAME
    at.run()
    return at


def _bodies(at):
    parts = []
    for el in at.main:
        for attr in ("value", "body"):
            try:   # some elements (st.page_link) raise on .value access
                v = getattr(el, attr, None)
            except Exception:
                continue
            if isinstance(v, str) and v:
                parts.append(v)
                break
    return " ".join(parts)


def test_client_dashboard_renders_with_streak_and_states():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client_home()
            assert not at.exception, at.exception
            body = _bodies(at)
            assert "Hey," in body and "Dash" in body, "personal hero missing"
            assert "WEEK 4" in body, "progress week wrong/missing"
            assert "2-WEEK LOGGING STREAK" in body, "streak chip wrong"
            assert "Current weight" in body and "175.1" in body
            assert "2,814" in body and "219g protein" in body
            assert "✓ up to date" in body, "weigh-in state wrong"
            assert "Due" in body, "check-in should be due"
            assert "COACH: ERIC" in body
            assert "My training" in body, "quick cards missing"
            # goal-aware: building + gaining => good
            assert '"d good">▲' in body.replace("class=", '"').replace(
                '""', '"') or "▲ 1.9 since start" in body
            # nothing coach-side leaks
            assert "CLIENTS ON FILE" not in body
            assert not any(getattr(b, "key", None) == "te_create"
                           for b in at.button)
    finally:
        cl.delete_client(NAME)


def test_checkin_done_state_and_note_block():
    _seed(checkins={"4": {"weight_avg": "175", "answers": {}}},
          coach_note="Push Meal 3 carbs up 20g on training days.")
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client_home()
            body = _bodies(at)
            assert "✓ this week" in body, "check-in done state missing"
            assert "Note from Eric" in body, "coach note header missing"
            assert "Meal 3 carbs" in body, "coach note text missing"
    finally:
        cl.delete_client(NAME)


def test_note_block_hidden_when_empty():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client_home()
            assert "Note from" not in _bodies(at), \
                "empty coach note should hide the block"
    finally:
        cl.delete_client(NAME)


def test_coach_console_unchanged():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = AppTest.from_file(HOME, default_timeout=40)
            at.session_state["_authed"] = True
            at.session_state["_role"] = "coach"
            at.session_state["_coach"] = "Eric"
            at.run()
            assert not at.exception
            assert "CLIENTS ON FILE" in _bodies(at), "coach console broken"
    finally:
        cl.delete_client(NAME)


def test_coach_note_input_saves():
    _seed()
    try:
        at = AppTest.from_file(HOME, default_timeout=40)   # ungated => coach
        at.session_state["client"] = NAME
        at.session_state["coach_detail"] = True            # open their detail
        at.run()
        key = f"cd_{NAME}_note"
        hits = [t for t in at.text_area if getattr(t, "key", None) == key]
        assert hits, f"coach-side note input missing ({key})"
        hits[0].input("Great week — keep protein high.")
        [b for b in at.button
         if "Save client info" in (b.label or "")][0].click()
        at.run()
        assert cl.get_client(NAME).get("coach_note") == \
            "Great week — keep protein high.", "note did not save"
    finally:
        cl.delete_client(NAME)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
