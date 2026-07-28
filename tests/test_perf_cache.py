"""Perf pass: cached readers actually cache, every write path invalidates
(saves are visible on the very next read), per-name cache keys, and the
fingerprint-keyed PDF rebuilds only when the plan changes.

Run:  python3 tests/test_perf_cache.py
"""
import json
import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import coachlib as cl

A, B = "Cache A", "Cache B"


def _cleanup():
    cl.delete_client(A)
    cl.delete_client(B)
    cl.delete_client("_settings")


def test_reads_are_cached_until_cleared():
    """Bypass the write path (raw file edit) — the cache must serve the old
    value until _clear_store_caches(), proving reads don't hit the store."""
    cl.upsert_client(A, {"goals": "v1"})
    try:
        assert cl.get_client(A).get("goals") == "v1"
        raw = json.load(open(cl.CLIENTS_PATH))
        raw[A]["goals"] = "v2-direct"
        json.dump(raw, open(cl.CLIENTS_PATH, "w"), indent=2)
        assert cl.get_client(A).get("goals") == "v1", \
            "read hit the store — cache is not active"
        cl._clear_store_caches()
        assert cl.get_client(A).get("goals") == "v2-direct", \
            "clear did not invalidate"
    finally:
        _cleanup()


def test_every_write_path_is_visible_immediately():
    try:
        cl.upsert_client(A, {"goals": "x"})
        assert cl.get_client(A).get("goals") == "x"
        assert A in cl.load_clients()

        cl.upsert_client(A, {"goals": "y"})            # update
        assert cl.get_client(A).get("goals") == "y"

        cl.set_client_login(A, "cache.a", "pw-123456")  # login write
        assert (cl.get_client(A).get("login") or {}).get("username") \
            == "cache.a"
        assert cl.verify_client_login("cache.a", "pw-123456") == A

        cl.save_training(A, {"block": 2, "week": 3, "weeks_total": 6,
                             "days": [{"name": "Push", "exercises": [
                                 {"exercise": "Bench", "sets": "3",
                                  "reps": "5", "rir": "", "cue": "",
                                  "video": ""}]}]})     # training write
        assert cl.get_training(A)["block"] == 2
        assert cl.has_program(A)

        cl.set_training_done(A, "2-3", "Push", [0])     # log write
        assert cl.get_training_log(A)["2-3"]["Push"] == [0]

        cl.save_settings({"currency": "€"})             # settings write
        assert cl.get_settings()["currency"] == "€"

        cl.delete_client(A)                             # delete
        assert A not in cl.load_clients()
        assert cl.get_client(A) == {}
    finally:
        _cleanup()


def test_get_client_cache_is_per_name():
    cl.upsert_client(A, {"goals": "a-goal"})
    cl.upsert_client(B, {"goals": "b-goal"})
    try:
        assert cl.get_client(A).get("goals") == "a-goal"
        assert cl.get_client(B).get("goals") == "b-goal"
        cl.upsert_client(B, {"goals": "b-goal-2"})
        assert cl.get_client(A).get("goals") == "a-goal"
        assert cl.get_client(B).get("goals") == "b-goal-2"
    finally:
        _cleanup()


def test_cached_returns_are_copies_not_shared_state():
    """Mutating what a cached reader returned must never poison the cache
    (pages do `rec.get('meal_plans', {})[...] = ...` before saving)."""
    cl.upsert_client(A, {"targets": {"Training Day": {"cal": 2000}}})
    try:
        rec = cl.get_client(A)
        rec["targets"]["Training Day"]["cal"] = 9999    # local mutation
        fresh = cl.get_client(A)
        assert fresh["targets"]["Training Day"]["cal"] == 2000, \
            "cache returned shared mutable state"
    finally:
        _cleanup()


def test_applications_cache_invalidates_on_all_writes():
    aid = cl.save_application({"first_name": "Cache", "last_name": "App"})
    try:
        apps = cl.load_applications()
        assert any(a["id"] == aid for a in apps), "new app not visible"
        cl.set_application_status(aid, "reviewed")
        assert next(a for a in cl.load_applications()
                    if a["id"] == aid)["status"] == "reviewed"
    finally:
        cl.delete_application(aid)
        assert all(a["id"] != aid for a in cl.load_applications()), \
            "deleted app still cached"


def test_pdf_rebuilds_when_plan_changes_and_not_otherwise():
    import pdfexport
    calls = {"n": 0}
    real = pdfexport.build_plan_pdf

    def counting(name):
        calls["n"] += 1
        return real(name)

    cl.upsert_client(A, {
        "start_date": (date.today() - timedelta(days=7)).isoformat(),
        "targets": {"Training Day": {"cal": 2500, "protein": 200,
                                     "fats": 60, "carbs": 250}},
        "meal_plans": {"Training Day": [
            {"Meal": "Pre", "Food": "Jasmine Rice", "Servings": "",
             "Amount": 200}]},
    })
    pdfexport.build_plan_pdf = counting
    try:
        from streamlit.testing.v1 import AppTest
        import contextlib

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

        with env(APP_USERS="Eric:12345"):
            at = AppTest.from_file(
                os.path.join(ROOT, "pages/1_Meal_Planner.py"),
                default_timeout=60)
            at.session_state["_authed"] = True
            at.session_state["_role"] = "client"
            at.session_state["_client_self"] = A
            at.run()
            assert not at.exception
            first = calls["n"]
            assert first >= 1, "PDF never built"
            at.run()                       # same plan -> cache hit
            assert calls["n"] == first, \
                f"PDF rebuilt on unchanged rerun ({calls['n']} builds)"
            cl.upsert_client(A, {"targets": {"Training Day": {
                "cal": 2600, "protein": 200, "fats": 60, "carbs": 250}}})
            at.run()                       # plan changed -> new fingerprint
            assert calls["n"] == first + 1, "changed plan did not rebuild"
    finally:
        pdfexport.build_plan_pdf = real
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
