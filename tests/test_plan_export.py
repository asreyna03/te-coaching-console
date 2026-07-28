"""Shopping-list aggregation + plan grid + PDF export.

Run:  python3 tests/test_plan_export.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import coachlib as cl
import pdfexport

NAME = "Export Test"


def _seed():
    cl.upsert_client(NAME, {
        "targets": {"Training Day": {"cal": 2800, "protein": 220,
                                     "fats": 70, "carbs": 320}},
        "meal_plans": {
            "Training Day": [
                {"Meal": "Pre", "Food": "Low Fat Chicken Thigh",
                 "Servings": "", "Amount": 180},
                {"Meal": "Meal 2", "Food": "Low Fat Chicken Thigh",
                 "Servings": "", "Amount": 120},
                {"Meal": "Meal 2", "Food": "Jasmine Rice",
                 "Servings": "", "Amount": 200},
            ],
            "Non-Training Day": [
                {"Meal": "Meal 1", "Food": "Low Fat Chicken Thigh",
                 "Servings": "", "Amount": 100},
                {"Meal": "Meal 1", "Food": "Oats", "Servings": "",
                 "Amount": 80},
            ],
        },
        "training": {"version": 1, "block": 1, "week": 2, "weeks_total": 4,
                     "days": [{"name": "Push", "exercises": [
                         {"exercise": "Bench", "sets": "4", "reps": "6",
                          "rir": "2", "cue": "", "video": ""}]}]},
    })


def test_shopping_list_sums_same_food_across_meals_and_days():
    _seed()
    try:
        sl = cl.shopping_list(NAME)
        assert "Proteins" in sl, f"categories: {list(sl)}"
        chicken = next(i for i in sl["Proteins"]
                       if i["food"] == "Low Fat Chicken Thigh")
        assert chicken["amount"] == 400, \
            f'chicken should sum 180+120+100=400, got {chicken["amount"]}'
        assert chicken["label"] == "400 g"
        carbs = {i["food"]: i for i in sl.get("Carbohydrates", [])}
        assert carbs["Jasmine Rice"]["amount"] == 200
        assert carbs["Oats"]["amount"] == 80
        # grouped in FOOD_CATS order: proteins before carbs
        assert list(sl).index("Proteins") < list(sl).index("Carbohydrates")
    finally:
        cl.delete_client(NAME)


def test_plan_grid_totals_are_consistent():
    _seed()
    try:
        grid = cl.plan_grid(NAME)
        td = grid["Training Day"]
        meal_cal = sum(m["totals"][0] for m in td["meals"])
        assert abs(meal_cal - td["totals"][0]) < 0.01
        assert td["targets"].get("cal") == 2800
        # every computed row carries macros + serving math
        row = td["meals"][0]["rows"][0]
        assert row["food"] == "Low Fat Chicken Thigh"
        assert row["cal"] > 0 and row["n"] > 0
    finally:
        cl.delete_client(NAME)


def test_pdf_builds_bytes():
    _seed()
    try:
        assert pdfexport.engine() in ("weasyprint", "fpdf"), \
            "no PDF engine installed — fpdf2 should be present"
        data = pdfexport.build_plan_pdf(NAME)
        assert data and bytes(data[:5]) == b"%PDF-", "not a PDF payload"
        assert len(data) > 2000, "suspiciously small PDF"
    finally:
        cl.delete_client(NAME)


def test_pdf_degrades_to_none_without_engines(monkeypatch=None):
    _seed()
    try:
        orig = pdfexport.engine
        pdfexport.engine = lambda: None
        try:
            assert pdfexport.build_plan_pdf(NAME) is None
        finally:
            pdfexport.engine = orig
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
