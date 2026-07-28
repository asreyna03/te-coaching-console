"""Theme engine: token injection on every route, manual + system modes,
per-user persistence (client record / coach _settings), isolation, chart
palette resolution, legacy alias bridge.

Run:  python3 tests/test_theme.py
"""
import contextlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl
import ui as ui_mod

HOME = os.path.join(ROOT, "app.py")
WEIGH = os.path.join(ROOT, "pages/2_Weigh_Ins.py")
A, B = "Theme A", "Theme B"


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


def _md(at):
    return " ".join(str(getattr(m, "value", "")) for m in at.main.markdown)


def _btn(at, key):
    hits = [b for b in at.button if getattr(b, "key", None) == key]
    assert hits, f"button {key!r} missing"
    return hits[0]


def _client(page, name):
    at = AppTest.from_file(page, default_timeout=40)
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = name
    at.run()
    return at


def _cleanup():
    cl.delete_client(A)
    cl.delete_client(B)
    cl.delete_client("_settings")


def test_tokens_injected_with_aliases_and_system_default():
    at = AppTest.from_file(HOME, default_timeout=40)
    at.run()
    assert not at.exception
    body = _md(at)
    # light tokens + the dark media block (default pref = system)
    assert "--bg:#EFEDE6" in body, "light tokens missing"
    assert "prefers-color-scheme: dark" in body, "system media block missing"
    assert "--bg:#15120C" in body, "dark tokens missing from system block"
    # legacy names bridge to the semantic roles
    for alias in ("--cream:var(--bg)", "--ink:var(--fg)",
                  "--line:var(--border)", "--accent2:var(--accent-2)"):
        assert alias in body, f"alias {alias} missing"
    assert at.session_state["_theme"] == "system"
    assert at.session_state["_lang"] == "en"


def test_cycle_reaches_dark_and_drops_media_query():
    at = AppTest.from_file(HOME, default_timeout=40)
    at.run()
    _btn(at, "tb_theme").click()          # system -> light
    at.run()
    assert at.session_state["_theme"] == "light"
    assert "prefers-color-scheme" not in _md(at), "manual light still system"
    _btn(at, "tb_theme").click()          # light -> dark
    at.run()
    assert at.session_state["_theme"] == "dark"
    body = _md(at)
    assert "--bg:#15120C" in body and "prefers-color-scheme" not in body
    _btn(at, "tb_theme").click()          # dark -> system (full cycle)
    at.run()
    assert at.session_state["_theme"] == "system"


def test_client_prefs_persist_and_reload():
    cl.upsert_client(A, {"goals": "x"})
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(WEIGH, A)
            _btn(at, "tb_lang_es").click()
            at.run()
            _btn(at, "tb_theme").click()
            at.run()
            _btn(at, "tb_theme").click()
            at.run()
            rec = cl.get_client(A)
            assert rec.get("lang") == "es" and rec.get("theme") == "dark"
            # a brand-new session (fresh login) restores both
            at2 = _client(WEIGH, A)
            assert at2.session_state["_lang"] == "es"
            assert at2.session_state["_theme"] == "dark"
            assert "--bg:#15120C" in _md(at2)
    finally:
        _cleanup()


def test_client_prefs_never_leak_between_clients():
    cl.upsert_client(A, {"goals": "x", "theme": "dark", "lang": "es"})
    cl.upsert_client(B, {"goals": "y"})
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(WEIGH, B)
            assert at.session_state["_theme"] == "system", \
                "A's theme leaked to B"
            assert at.session_state["_lang"] == "en", "A's lang leaked to B"
            # B flipping theme touches only B's record
            _btn(at, "tb_theme").click()
            at.run()
            assert (cl.get_client(A) or {}).get("theme") == "dark"
            assert (cl.get_client(B) or {}).get("theme") == "light"
    finally:
        _cleanup()


def test_coach_prefs_live_in_settings_not_client_records():
    cl.upsert_client(A, {"goals": "x"})
    try:
        with env(APP_USERS="coach:12345"):
            at = AppTest.from_file(HOME, default_timeout=40)
            at.session_state["_authed"] = True
            at.session_state["_role"] = "coach"
            at.session_state["_coach"] = "coach"
            at.run()
            assert not at.exception
            _btn(at, "tb_lang_es").click()
            at.run()
            prefs = cl.get_settings()["coach_prefs"]
            assert prefs.get("coach", {}).get("lang") == "es"
            # never written onto a client record
            assert "lang" not in (cl.get_client(A) or {})
            # the _settings record stays invisible to the client list
            assert "_settings" not in cl.load_clients()
    finally:
        _cleanup()


def test_records_without_prefs_default_cleanly():
    cl.upsert_client(A, {"goals": "x"})          # pre-theme record shape
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(WEIGH, A)
            assert not at.exception
            assert at.session_state["_theme"] == "system"
            assert at.session_state["_lang"] == "en"
    finally:
        _cleanup()


def test_chart_palette_follows_effective_theme():
    import streamlit as st
    st.session_state["_theme"] = "dark"
    try:
        pal = ui_mod.chart_palette()
        assert pal["fg"] == "#F1EEE7" and pal["accent"] == "#F2662F"
        st.session_state["_theme"] = "light"
        pal = ui_mod.chart_palette()
        assert pal["fg"] == "#17150F" and pal["accent"] == "#E4531F"
        assert ui_mod._hex_rgba(pal["accent"], 0.22) == "rgba(228,83,31,0.22)"
    finally:
        st.session_state.pop("_theme", None)


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
