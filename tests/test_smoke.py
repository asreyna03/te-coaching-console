"""Smoke suite (streamlit.testing.v1): every page renders without an exception,
and the console top bar exposes its keyed widgets. Runs gate-free (no APP_PASSWORD
/ APP_USERS in the env) so is_authed() is True and the console renders.

Run:  python3 tests/test_smoke.py     (also pytest-discoverable if pytest is installed)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

PAGES = [
    "app.py", "pages/1_Meal_Planner.py", "pages/2_Weigh_Ins.py",
    "pages/3_Check_In.py", "pages/4_Supplements.py", "pages/5_Training.py",
    "pages/7_Applications.py", "pages/8_Clients.py",
]


def _run(rel, **session):
    at = AppTest.from_file(os.path.join(ROOT, rel), default_timeout=40)
    for k, v in session.items():
        at.session_state[k] = v
    at.run()
    return at


def test_all_pages_render_without_exception():
    for rel in PAGES:
        at = _run(rel)
        assert not at.exception, f"{rel} raised: {at.exception}"


def test_topbar_switcher_present():
    # the switcher is a custom popover now; its create-client control proves it rendered
    at = _run("app.py")
    assert any(b.key == "te_create" for b in at.button), \
        f"client switcher popover missing; buttons={[b.key for b in at.button]}"


def test_topbar_logout_button_present():
    at = _run("app.py")
    assert any(b.key == "tb_logout" for b in at.button), \
        f"tb_logout missing; buttons={[b.key for b in at.button]}"


def test_active_client_returned_by_picker():
    # coachlib local JSON has 'Demo Client'; the seed should select a real client.
    at = _run("app.py")
    val = at.session_state["_active_client"] if "_active_client" in at.session_state else None
    assert val, "client_picker did not resolve an active client"


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
