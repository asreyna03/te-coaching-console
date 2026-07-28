"""Client portal pass: client-side weigh-in toolbar (shared component),
shopping list collapsed on screen but complete in the PDF.

Run:  python3 tests/test_client_portal.py
"""
import contextlib
import os
import re
import sys
import zlib
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl
import pdfexport

WEIGH = os.path.join(ROOT, "pages/2_Weigh_Ins.py")
MEAL = os.path.join(ROOT, "pages/1_Meal_Planner.py")
NAME = "CP Test"


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


def _seed():
    cl.upsert_client(NAME, {
        "start_date": (date.today() - timedelta(days=10)).isoformat(),
        "goals": "Lose fat",
        "targets": {"Training Day": {"cal": 2500, "protein": 200,
                                     "fats": 60, "carbs": 250}},
        "meal_plans": {
            "Training Day": [
                {"Meal": "Pre", "Food": "Low Fat Chicken Thigh",
                 "Servings": "", "Amount": 180},
                {"Meal": "Meal 2", "Food": "Jasmine Rice",
                 "Servings": "", "Amount": 200},
            ],
            "Non-Training Day": [
                {"Meal": "Meal 1", "Food": "Oats", "Servings": "",
                 "Amount": 80},
            ],
        },
        "weighins": [{"Date": (date.today() - timedelta(days=2)).isoformat(),
                      "Weight": "181"}],
    })


def _cleanup():
    cl.delete_client(NAME)


def _client(page):
    at = AppTest.from_file(page, default_timeout=40)
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = NAME
    at.run()
    return at


def _pdf_text(data):
    """Raw + inflated PDF stream bytes — enough to grep printed strings."""
    chunks = [bytes(data)]
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", bytes(data), re.S):
        try:
            chunks.append(zlib.decompress(m.group(1)))
        except Exception:
            pass
    return b"".join(chunks)


def test_client_weighins_toolbar_add_today_scoped_to_self():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(WEIGH)
            assert not at.exception
            # same shared component the coach page uses
            add = [b for b in at.button
                   if getattr(b, "key", None) == f"wi_add::{NAME}"]
            assert add, "client add-day toolbar button missing"
            assert any(getattr(d, "key", None) == f"wi_date::{NAME}"
                       for d in at.date_input), "calendar picker missing"
            add[0].click()
            at.run()
            date_cells = [d for d in at.date_input
                          if str(getattr(d, "key", ""))
                          .startswith(f"wi::{NAME}::")
                          and str(d.key).endswith("::Date")]
            assert date_cells, "Date cells are not calendar pickers"
            assert any(d.value == date.today() for d in date_cells), \
                "client add-day did not pre-fill today"
            # scoped to self: no other client's table keys exist
            assert all(str(d.key).startswith(f"wi::{NAME}::")
                       for d in date_cells)
    finally:
        _cleanup()


def test_shopping_list_collapsed_on_screen():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(MEAL)
            assert not at.exception
            exps = [e for e in at.expander
                    if "Shopping list" in str(getattr(e, "label", ""))]
            assert exps, "shopping list expander missing"
            # checkable items live inside it and stay keyed
            assert any(str(getattr(c, "key", "")).startswith(f"sl::{NAME}::")
                       for c in at.checkbox), "shopping checkboxes missing"
    finally:
        _cleanup()


def test_pdf_prints_full_shopping_list_regardless_of_ui_state():
    _seed()
    try:
        # PDF is built straight from the data — no page/expander involved
        data = pdfexport.build_plan_pdf(NAME)
        assert data and bytes(data[:5]) == b"%PDF-"
        text = _pdf_text(data)
        for food in (b"Low Fat Chicken Thigh", b"Jasmine Rice", b"Oats"):
            assert food in text, f"{food!r} missing from the PDF"
        assert b"SHOPPING LIST" in text, "shopping section header missing"
        # aggregation intact: chicken appears with its summed gram total
        sl = cl.shopping_list(NAME)
        chicken = next(i for i in sl["Proteins"]
                       if i["food"] == "Low Fat Chicken Thigh")
        assert chicken["label"].encode() in text, \
            "aggregated amount missing from the PDF"
    finally:
        _cleanup()


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
