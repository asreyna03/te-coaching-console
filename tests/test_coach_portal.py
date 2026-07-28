"""Coach portal: Clients sheet landing, row-open detail, allergy bars,
supplement cost math, weigh-in add-today, Sync removal integrity.

Run:  python3 tests/test_coach_portal.py
"""
import contextlib
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl
import ui as ui_mod

HOME = os.path.join(ROOT, "app.py")
CLIENTS = os.path.join(ROOT, "pages/8_Clients.py")
MEAL = os.path.join(ROOT, "pages/1_Meal_Planner.py")
SUPPS = os.path.join(ROOT, "pages/4_Supplements.py")
WEIGH = os.path.join(ROOT, "pages/2_Weigh_Ins.py")

A, B = "Portal A", "Portal B"


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


def _bodies(at):
    parts = []
    for el in at.main:
        for attr in ("value", "body"):
            try:
                v = getattr(el, attr, None)
            except Exception:
                continue
            if isinstance(v, str) and v:
                parts.append(v)
                break
    return " ".join(parts)


def _btn(at, key):
    hits = [b for b in at.button if getattr(b, "key", None) == key]
    assert hits, f"button {key!r} missing; have {[b.key for b in at.button]}"
    return hits[0]


def _seed():
    today = date.today()
    cl.upsert_client(A, {          # no program, check-in due, has allergy
        "start_date": (today - timedelta(days=15)).isoformat(),
        "goals": "Lose fat",
        "allergies": "Peanuts, Shellfish",
        "targets": {"Training Day": {"cal": 2500, "protein": 200,
                                     "fats": 60, "carbs": 250}},
        "weighins": [
            {"Date": (today - timedelta(days=9)).isoformat(),
             "Weight": "180"},
            {"Date": (today - timedelta(days=1)).isoformat(),
             "Weight": "178.5"}],
    })
    cl.upsert_client(B, {          # program set, check-in done, no allergy
        "start_date": (today - timedelta(days=8)).isoformat(),
        "goals": "Build muscle",
        "training": {"version": 1, "block": 1, "week": 1, "weeks_total": 4,
                     "days": [{"name": "Push", "exercises": [
                         {"exercise": "Bench", "sets": "3", "reps": "5",
                          "rir": "", "cue": "", "video": ""}]}]},
        "checkins": {"2": {"weight_avg": "", "answers": {}}},
    })


def _cleanup():
    cl.delete_client(A)
    cl.delete_client(B)
    cl.delete_client("_settings")


def test_coach_home_restored_console():
    _seed()
    try:
        at = AppTest.from_file(HOME, default_timeout=40)
        at.run()
        assert not at.exception
        body = _bodies(at)
        assert "CLIENTS ON FILE" in body, "console stats missing"
        assert "WHAT" in body, "what's-inside cards missing"
        assert "YOUR CLIENTS" not in body, "sheet leaked onto Home"
    finally:
        _cleanup()


def test_clients_tab_sheet():
    _seed()
    try:
        at = AppTest.from_file(CLIENTS, default_timeout=40)
        at.run()
        assert not at.exception
        body = _bodies(at)
        assert "YOUR CLIENTS" in body, "sheet label missing"
        assert "ACTIVE CLIENTS" in body, "summary tiles missing"
        _btn(at, f"cs_open::{A}")                       # row click targets
        _btn(at, f"cs_open::{B}")
        assert "⚠ Peanuts, Shellfish" in body, "allergy cell missing"
        assert "Build program" in body, "to-do phrase missing"
        assert "All good" in body, "B should be all good"
        assert "Missing" in body and "Set" in body, "program chips missing"
    finally:
        _cleanup()


def test_row_click_sets_client_and_routes_home():
    _seed()
    try:
        at = AppTest.from_file(CLIENTS, default_timeout=40)
        at.run()
        _btn(at, f"cs_open::{B}").click()
        at.run()
        assert at.session_state["client"] == B, "row did not set client"
        # _goto_home consumed by the switch_page guard (no-op in AppTest)
        assert "_goto_home" not in at.session_state \
            or not at.session_state["_goto_home"]
        # client role can never reach this page
        with env(APP_USERS="Eric:12345"):
            atc = AppTest.from_file(CLIENTS, default_timeout=40)
            atc.session_state["_authed"] = True
            atc.session_state["_role"] = "client"
            atc.session_state["_client_self"] = A
            atc.run()
            assert "COACH ONLY" in _bodies(atc), "client reached Clients tab"
    finally:
        _cleanup()


def test_allergy_bar_shows_hides_and_never_leaks():
    _seed()
    try:
        # coach meal planner: A shows the bar, B doesn't
        at = AppTest.from_file(MEAL, default_timeout=40)
        at.session_state["client"] = A
        at.run()
        b1 = _bodies(at)
        assert "⚠ Allergy" in b1 and "Peanuts" in b1, "coach bar missing"
        at2 = AppTest.from_file(MEAL, default_timeout=40)
        at2.session_state["client"] = B
        at2.run()
        assert "⚠ Allergy" not in _bodies(at2), "empty allergy bar rendered"
        # client My Plan: A sees their own bar; B never sees A's allergens
        with env(APP_USERS="Eric:12345"):
            for me, expect in ((A, True), (B, False)):
                atc = AppTest.from_file(MEAL, default_timeout=40)
                atc.session_state["_authed"] = True
                atc.session_state["_role"] = "client"
                atc.session_state["_client_self"] = me
                atc.run()
                has = "Peanuts" in _bodies(atc)
                assert has is expect, \
                    f"allergy leak/miss for {me}: {has}"
    finally:
        _cleanup()


def test_supplements_same_grid_both_roles_and_buy_links():
    """Coach Supplements now RENDERS THE CLIENT GRID (cost sheet parked).
    Buy links come from coach-set URL overrides; junk text in the food-DB
    link column never renders; no URL -> no Buy link at all."""
    _seed()
    try:
        at = AppTest.from_file(SUPPS, default_timeout=40)   # coach
        at.run()
        assert not at.exception
        body = _bodies(at)
        assert "Dose / timing" in body, "coach grid header missing"
        assert "Essential" in body, "essential pill missing"
        for tok in ("Per unit", "Total stack", "COST BREAKDOWN",
                    "Cost per day"):
            assert tok not in body, f"parked cost grid leaked: {tok!r}"
        # coach-only: the buy-link editor exists, with per-supplement inputs
        slinks = [i for i in at.text_input
                  if str(getattr(i, "key", "")).startswith("slink::")]
        assert slinks, "buy-link editor missing for coach"
        # set a URL override -> the grid links it; junk text never links
        name = str(slinks[0].key).split("::", 1)[1]
        slinks[0].set_value("https://example.com/product")
        [b for b in at.button if b.key == "slink_save"][0].click()
        at.run()
        assert cl.get_settings()["supp_links"][name] == \
            "https://example.com/product"
        assert 'href="https://example.com/product"' in _bodies(at), \
            "override URL not linked in the grid"
        # client: same grid, editor absent, override link visible
        with env(APP_USERS="Eric:12345"):
            atc = AppTest.from_file(SUPPS, default_timeout=40)
            atc.session_state["_authed"] = True
            atc.session_state["_role"] = "client"
            atc.session_state["_client_self"] = A
            atc.run()
            cbody = _bodies(atc)
            assert "Dose / timing" in cbody
            assert not [i for i in atc.text_input
                        if str(getattr(i, "key", "")).startswith("slink::")], \
                "buy-link editor leaked to the client"
            assert 'href="https://example.com/product"' in cbody
    finally:
        cl.save_settings({"supp_links": {}})
        _cleanup()


def test_weighin_add_day_prefills_today_and_saves():
    _seed()
    try:
        at = AppTest.from_file(WEIGH, default_timeout=40)
        at.session_state["client"] = A
        at.run()
        _btn(at, f"wi_add::{A}").click()
        at.run()
        date_cells = [d for d in at.date_input
                      if str(getattr(d, "key", "")).startswith(f"wi::{A}::")
                      and str(getattr(d, "key", "")).endswith("::Date")]
        assert date_cells, "Date cells are not calendar pickers"
        assert any(d.value == date.today() for d in date_cells), \
            "new row not pre-dated to today"
        # edit the new date via the calendar, save, persists
        newest = max(date_cells,
                     key=lambda t: int(str(t.key).split("::")[2]))
        newest.set_value(date(2026, 1, 1))
        _btn(at, f"wi_save::{A}").click()
        at.run()
        dates = [w.get("Date") for w in
                 (cl.get_client(A).get("weighins") or [])]
        assert "2026-01-01" in dates, "edited date did not persist"
        # prepend: the new row is FIRST in the log
        assert dates[0] == "2026-01-01", "new row did not prepend"
    finally:
        _cleanup()


def test_client_login_control_sets_and_resets():
    """Coach console 'client login' control: a chosen password verifies and
    is never echoed back; a blank one generates a temp shown exactly once;
    a reset invalidates the old password."""
    import re
    cl.upsert_client(A, {"goals": "x"})
    try:
        at = AppTest.from_file(HOME, default_timeout=40)
        at.session_state["client"] = A
        at.run()
        assert not at.exception
        at.text_input(f"cl_user_{A}").set_value("portal.a")
        at.text_input(f"cl_pw_{A}").set_value("chosen-pw-1")
        _btn(at, f"cl_setlogin_{A}").click()
        at.run()
        assert cl.verify_client_login("portal.a", "chosen-pw-1") == A
        assert "chosen-pw-1" not in _bodies(at), "typed password echoed"
        at.text_input(f"cl_pw_{A}").set_value("")
        _btn(at, f"cl_setlogin_{A}").click()
        at.run()
        succ = " ".join(str(getattr(s, "value", ""))
                        for s in at.main.success)
        m = re.search(r"te-[0-9a-f]{6}", succ)
        assert m, "generated temp password not shown"
        assert cl.verify_client_login("portal.a", m.group(0)) == A
        assert cl.verify_client_login("portal.a", "chosen-pw-1") is None, \
            "old password survived the reset"
    finally:
        _cleanup()


def test_sync_removed_clean():
    assert not os.path.exists(os.path.join(ROOT, "pages/6_Sync.py")), \
        "Sync page still exists"
    assert "/Sync" not in ui_mod._PAGE_FILE, "Sync still in page map"
    assert all(lbl != "Sync" for lbl, *_ in ui_mod._RAIL_NAV), \
        "Sync still in the nav rail"
    assert "Sync" not in ui_mod._PAGE_KEY, "Sync still in page keys"


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
