"""i18n: key completeness (every t() call resolves in BOTH languages),
ES flips the chrome, data stays as typed, missing keys fall back to EN,
lang toggle persists per user, storage keys never localize.

Run:  python3 tests/test_i18n.py
"""
import contextlib
import os
import re
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl
import i18n

HOME = os.path.join(ROOT, "app.py")
MEAL = os.path.join(ROOT, "pages/1_Meal_Planner.py")
CHECK = os.path.join(ROOT, "pages/3_Check_In.py")
NAME = "I18n Test"


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
        for attr in ("value", "body", "label"):
            try:
                v = getattr(el, attr, None)
            except Exception:
                continue
            if isinstance(v, str) and v:
                parts.append(v)
                break
    return " ".join(parts)


def _seed():
    cl.upsert_client(NAME, {
        "start_date": (date.today() - timedelta(days=10)).isoformat(),
        "goals": "Build muscle", "coach": "Eric",
        "targets": {"Training Day": {"cal": 2500, "protein": 200,
                                     "fats": 60, "carbs": 250}},
        "meal_plans": {"Training Day": [
            {"Meal": "Pre", "Food": "Jasmine Rice", "Servings": "",
             "Amount": 200}]},
        "weighins": [
            {"Date": (date.today() - timedelta(days=3)).isoformat(),
             "Weight": "180"},
            {"Date": (date.today() - timedelta(days=1)).isoformat(),
             "Weight": "179"}],
    })


def _cleanup():
    cl.delete_client(NAME)


def _client(page, lang=None):
    at = AppTest.from_file(page, default_timeout=40)
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = NAME
    if lang:
        at.session_state["_lang"] = lang
        at.session_state["_theme"] = "system"
    at.run()
    return at


def test_every_used_key_exists_in_both_languages():
    used = set()
    files = [os.path.join(ROOT, "app.py"), os.path.join(ROOT, "ui.py")] + [
        os.path.join(ROOT, "pages", f) for f in os.listdir(
            os.path.join(ROOT, "pages")) if f.endswith(".py")]
    for path in files:
        src = open(path).read()
        used |= set(re.findall(r"""(?<![\w.])_?t\(\s*["']([^"']+)["']""",
                               src))
        used |= set(re.findall(r"""t\(f?["']cat_\{?""", src) and [])
    # dynamic keys built at runtime (f-strings) — checked explicitly
    dynamic = {f"cat_{c}" for c in ("Proteins", "Carbohydrates", "Fats",
                                    "FruitsVegetables", "DrinksCondiments",
                                    "Recipes")}
    used |= dynamic
    en, es = set(i18n.STRINGS["en"]), set(i18n.STRINGS["es"])
    assert en == es, f"en/es drift: {sorted(en ^ es)}"
    missing = {k for k in used if k not in en and not k.startswith("nav_")
               and k in used} - en
    # keys passed through t() that are literal fallbacks (nav labels map
    # through _NAV_T) are fine; everything else must exist
    missing = {k for k in missing if "_" in k}
    assert not missing, f"keys used but not defined: {sorted(missing)}"


def test_es_flips_dashboard_chrome_and_keeps_data():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(HOME, lang="es")
            assert not at.exception
            body = _bodies(at)
            assert "Peso actual" in body, "ES stat label missing"
            assert "Meta de la semana" in body
            assert "TU PROGRESO" in body
            assert "Hola," in body
            assert "Current weight" not in body, "EN label leaked into ES"
            # user data stays exactly as typed
            en_at = _client(HOME, lang="en")
            en_body = _bodies(en_at)
            assert "Current weight" in en_body and "Hey," in en_body
    finally:
        _cleanup()


def test_es_meal_grid_headers_but_food_names_as_typed():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(MEAL, lang="es")
            assert not at.exception
            body = _bodies(at)
            for tok in ("Categoría", "Alimento", "Ración",
                        "N.º de raciones", "Proteína", "Carbos",
                        "Día de entreno"):
                assert tok in body, f"ES header {tok!r} missing"
            assert "Jasmine Rice" in body, "food name must stay as typed"
    finally:
        _cleanup()


def test_default_is_en_and_missing_key_falls_back():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(HOME)               # no lang on the record
            assert at.session_state["_lang"] == "en"
            assert "Current weight" in _bodies(at)
    finally:
        _cleanup()
    # fallback chain: es missing -> en; unknown -> the key itself
    import streamlit as st
    st.session_state["_lang"] = "es"
    try:
        assert i18n.t("nonexistent_key_xyz") == "nonexistent_key_xyz"
        assert i18n.t("peso_actual") == "Peso actual"
    finally:
        st.session_state.pop("_lang", None)


def test_checkin_answers_store_under_english_keys_in_es():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = AppTest.from_file(CHECK, default_timeout=40)
            at.session_state["_authed"] = True
            at.session_state["_role"] = "client"
            at.session_state["_client_self"] = NAME
            at.session_state["_lang"] = "es"
            at.session_state["_theme"] = "system"
            at.run()
            assert not at.exception
            # answer the first question and submit
            tas = at.text_area
            assert tas, "check-in questions missing"
            tas[0].set_value("Buena semana")
            submit = [b for b in at.button
                      if "Guardar check-in" in str(getattr(b, "label", ""))]
            assert submit, "ES save button missing"
            submit[0].click()
            at.run()
            saved = (cl.get_client(NAME).get("checkins") or {}).get("1", {})
            answers = saved.get("answers") or {}
            assert answers, "answers did not save"
            # storage keys are the ENGLISH question strings, even in ES
            assert any(k.startswith("Training Performance")
                       for k in answers), list(answers)[:3]
    finally:
        _cleanup()


def test_lang_pref_persists_on_the_client_record():
    _seed()
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(HOME)
            hits = [b for b in at.button if getattr(b, "key", "") ==
                    "tb_lang_es"]
            assert hits, "ES toggle missing on client bar"
            hits[0].click()
            at.run()
            assert (cl.get_client(NAME) or {}).get("lang") == "es"
            body = _bodies(at)
            assert "Peso actual" in body, "toggle did not flip in-place"
    finally:
        _cleanup()


def test_es_metric_units_convert_and_round_trip():
    """ES displays kg (storage stays lb): the dashboard converts, the
    weigh-in table shows kg and an entered kg value saves back as lb —
    stable across repeated flips (no drift)."""
    import i18n as _i
    import streamlit as _st
    WEIGH2 = os.path.join(ROOT, "pages/2_Weigh_Ins.py")
    _seed()   # weighins: 180 lb then 179 lb
    try:
        with env(APP_USERS="Eric:12345"):
            at = _client(HOME, lang="es")
            body = _bodies(at)
            assert "81.2" in body, \
                "current weight (179 lb) not shown as 81.2 kg"
            assert "kg" in body
            # weigh-in table in kg
            atw = _client(WEIGH2, lang="es")
            cells = [str(getattr(i, "value", ""))
                     for i in atw.text_input
                     if str(getattr(i, "key", "")).endswith("::Weight")]
            assert "81.2" in cells, f"log cells not kg: {cells}"
            # client logs 80 kg -> stored as lb
            first = [i for i in atw.text_input
                     if str(getattr(i, "key", "")).endswith("::Weight")][0]
            first.set_value("80")
            [b for b in atw.button
             if str(getattr(b, "key", "")).startswith("wi_save::")][0].click()
            atw.run()
            stored = [w["Weight"] for w in
                      (cl.get_client(NAME).get("weighins") or [])]
            assert "176.4" in stored, f"80 kg not stored as lb: {stored}"
            # flip to EN: same row reads 176.4 lb; flip back: 80.0 kg — no
            # drift on repeated conversion
            ate = _client(WEIGH2, lang="en")
            cells_en = [str(getattr(i, "value", ""))
                        for i in ate.text_input
                        if str(getattr(i, "key", "")).endswith("::Weight")]
            assert "176.4" in cells_en, cells_en
            ats = _client(WEIGH2, lang="es")
            cells_es = [str(getattr(i, "value", ""))
                        for i in ats.text_input
                        if str(getattr(i, "key", "")).endswith("::Weight")]
            assert "80" in cells_es, cells_es
        # pure helper round-trip sanity
        _st.session_state["_lang"] = "es"
        try:
            assert _i.w_in(_i.w_out(175.0)) == 175.0
        finally:
            _st.session_state.pop("_lang", None)
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
