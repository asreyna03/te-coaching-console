"""Auth suite (streamlit.testing.v1): the gate blocks visitors, an authed session
renders the console, and logout (from the avatar menu, key tb_logout) clears the
session. Env is set per-test with try/finally so no gate leaks into other tests.

Run:  python3 tests/test_auth.py     (also pytest-discoverable if pytest is installed)
"""
import os
import sys
import contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl

MEAL = os.path.join(ROOT, "pages/1_Meal_Planner.py")
HOME = os.path.join(ROOT, "app.py")
APPS = os.path.join(ROOT, "pages/7_Applications.py")
WEIGH = os.path.join(ROOT, "pages/2_Weigh_Ins.py")


@contextlib.contextmanager
def env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update({k: v for k, v in kv.items()})
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _has_key(seq, key):
    return any(getattr(el, "key", None) == key for el in seq)


def test_gate_blocks_unauthed_console_page():
    with env(APP_PASSWORD="secret"):
        at = AppTest.from_file(MEAL, default_timeout=40)
        at.run()
    assert not at.exception
    # console must NOT leak past the gate (logout only exists inside the console)
    assert not _has_key(at.button, "tb_logout"), "console rendered without auth"
    # a password entry must be offered
    assert len(at.text_input) >= 1, "no login field on the gate screen"


def test_authed_session_renders_console():
    with env(APP_PASSWORD="secret"):
        at = AppTest.from_file(MEAL, default_timeout=40)
        at.session_state["_authed"] = True
        at.run()
    assert not at.exception
    assert _has_key(at.button, "tb_logout"), "authed console did not render"


def test_logout_clears_session():
    with env(APP_USERS="Eric:12345"):
        at = AppTest.from_file(HOME, default_timeout=40)
        at.session_state["_authed"] = True
        at.session_state["_coach"] = "Eric"
        at.run()
        assert not at.exception
        logout_btns = [b for b in at.button if b.key == "tb_logout"]
        assert logout_btns, f"tb_logout not found; buttons={[b.key for b in at.button]}"
        logout_btns[0].click().run()
    authed_after = at.session_state["_authed"] if "_authed" in at.session_state else False
    assert not authed_after, "logout did not clear _authed"


# ---------------- roles: client accounts + isolation -------------------------
# THE most important tests in this suite: a client reaching another client's
# data — by nav, link, or poked session state — is a hard failure.

def _md_bodies(at):
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


def _client_session(at, name):
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = name
    return at


def test_client_login_resolves_role_and_lands_on_client_home():
    cl.set_client_login("Role Test A", "role.a@test.co", "pw-a-1")
    try:
        assert cl.verify_client_login("role.a@test.co", "wrong") is None
        assert cl.verify_client_login("ROLE.A@test.co", "pw-a-1") == "Role Test A"
        with env(APP_USERS="Eric:12345"):
            at = AppTest.from_file(HOME, default_timeout=40)
            at.run()
            [b for b in at.button if b.key == "coach_access"][0].click()
            at.run()
            at.text_input[0].input("role.a@test.co")
            at.text_input[1].input("pw-a-1")
            [b for b in at.button if "Log in" in (b.label or "")][0].click()
            at.run()
            assert not at.exception
            assert at.session_state["_role"] == "client"
            assert at.session_state["client"] == "Role Test A"
            body = _md_bodies(at)
            assert "Hey," in body and "YOUR PROGRESS" in body, \
                "client dashboard hero missing"
            assert "CLIENTS ON FILE" not in body, "coach console leaked"
            assert not _has_key(at.button, "te_create"), "client switcher leaked"
            assert _has_key(at.button, "tb_logout")
    finally:
        cl.delete_client("Role Test A")


def test_client_blocked_from_coach_pages():
    cl.set_client_login("Role Test A", "role.a@test.co", "pw-a-1")
    try:
        with env(APP_USERS="Eric:12345"):
            for page in (APPS,):
                at = _client_session(
                    AppTest.from_file(page, default_timeout=40), "Role Test A")
                at.run()
                assert not at.exception
                body = _md_bodies(at)
                assert "COACH ONLY" in body, f"role gate missing on {page}"
                assert len(at.tabs) == 0, "coach page content leaked past gate"
                assert "inbox" not in body.lower()
    finally:
        cl.delete_client("Role Test A")


def test_client_cannot_load_another_clients_data():
    cl.set_client_login("Role Test A", "role.a@test.co", "pw-a-1")
    # marker values must never collide with app chrome (the CSS blob rides in
    # the same markdown stream — e.g. border-radius:999px)
    cl.upsert_client("Role Test B", {
        "goals": "SECRET-B-MARKER build muscle",
        "bodyweight": "987.3 lbs",
        "weighins": [{"Date": "2026-07-01", "Weight": "987.3"}]})
    try:
        with env(APP_USERS="Eric:12345"):
            for page in (HOME, WEIGH):
                at = _client_session(
                    AppTest.from_file(page, default_timeout=40), "Role Test A")
                # hostile session pokes — every scope key forced to another client
                at.session_state["client"] = "Role Test B"
                at.session_state["_active_client"] = "Role Test B"
                at.session_state["client_pick_pending"] = "Role Test B"
                at.run()
                assert not at.exception
                assert at.session_state["client"] == "Role Test A", \
                    f"scope not forced back to self on {page}"
                body = _md_bodies(at)
                assert "SECRET-B-MARKER" not in body, "another client's data leaked"
                assert "Role Test B" not in body, "another client's name leaked"
                assert "987.3" not in body, "another client's weight leaked"
                # grids too — weigh-in rows render as dataframes, not markdown
                for grid in (list(getattr(at, "dataframe", []))
                             + list(getattr(at, "data_editor", []))):
                    v = getattr(grid, "value", None)
                    if v is not None:
                        assert "987.3" not in str(v), \
                            "another client's weigh-ins leaked in a grid"
                # and keyed inputs — the styled log renders as text cells
                for ti in at.text_input:
                    assert "987.3" not in str(getattr(ti, "value", "") or ""), \
                        "another client's weigh-ins leaked in an input"
    finally:
        cl.delete_client("Role Test A")
        cl.delete_client("Role Test B")


def test_coach_still_sees_everything():
    with env(APP_USERS="Eric:12345"):
        at = AppTest.from_file(HOME, default_timeout=40)
        at.session_state["_authed"] = True
        at.session_state["_role"] = "coach"
        at.session_state["_coach"] = "Eric"
        at.run()
        assert not at.exception
        assert _has_key(at.button, "te_create"), "coach lost the switcher"
        assert "CLIENTS ON FILE" in _md_bodies(at), "coach console missing"
        at2 = AppTest.from_file(APPS, default_timeout=40)
        at2.session_state["_authed"] = True
        at2.session_state["_role"] = "coach"
        at2.session_state["_coach"] = "Eric"
        at2.run()
        assert not at2.exception
        body2 = _md_bodies(at2)
        assert "Applications." in body2, "coach lost the Applications inbox"
        assert "COACH ONLY" not in body2, "coach hit the role gate"


def test_convert_creates_client_login_and_flips_status():
    import re
    aid = cl.save_application({
        "first_name": "Conv", "last_name": "Test",
        "email": "conv.test@example.com", "phone": "555-010-7777",
        "age": "25–35", "height": "5'10\"", "current_weight": "180 lbs",
        "primary_goal": "Build muscle", "days_per_week": "3–4",
        "injuries": "None", "allergies": "None", "biggest_struggle": "x",
        "coached_before": "No", "ready_to_invest": "Yes"})
    try:
        at = AppTest.from_file(APPS, default_timeout=40)   # ungated => coach
        at.run()
        convs = [b for b in at.button if getattr(b, "key", None) == f"conv_{aid}"]
        assert convs, "Convert to client button missing from the inbox card"
        convs[0].click()
        at.run()
        # client record built from the application
        rec = cl.get_client("Conv Test")
        assert rec, "convert did not create the client"
        assert rec.get("contact_email") == "conv.test@example.com"
        assert rec.get("bodyweight") == "180 lbs"
        assert rec.get("start_date"), "start date not set"
        assert "Build muscle" in rec.get("goals", "")
        # status flipped + client set active
        app_now = next(x for x in cl.load_applications() if x["id"] == aid)
        assert app_now.get("status") == "converted"
        assert at.session_state["client"] == "Conv Test"
        # login created; temp credentials shown exactly once and verify
        body = _md_bodies(at)
        assert "is now a client" in body, "success banner missing"
        m = re.search(r"te-[0-9a-f]{6}", body)
        assert m, "temp credentials were not shown to the coach"
        assert cl.verify_client_login("conv.test@example.com",
                                      m.group(0)) == "Conv Test", \
            "converted login does not verify"
        at.run()
        assert m.group(0) not in _md_bodies(at), \
            "temp password shown more than once"
    finally:
        cl.delete_client("Conv Test")
        cl.delete_application(aid)


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
