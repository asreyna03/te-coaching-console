"""Training builder suite: data-shape round-trip + normalization, coach vs
client rendering, save flow, and the duplicate-overwrite guard (a program is
never silently replaced).

Run:  python3 tests/test_training.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest

import coachlib as cl

TRAIN = os.path.join(ROOT, "pages/5_Training.py")

SRC, TGT = "TR Src", "TR Target"
PROGRAM = {"version": 1, "block": 2, "week": 3, "weeks_total": 6,
           "days": [{"name": "Push", "exercises": [
               {"exercise": "Barbell Bench Press", "sets": "4",
                "reps": "6–8", "rir": "2",
                "cue": "Control the eccentric",
                "video": "https://youtu.be/demo-x1"},
               {"exercise": "Cable Fly", "sets": "3", "reps": "12–15",
                "rir": "1", "cue": "", "video": ""}]},
               {"name": "Pull", "exercises": []}]}


def _client_run(page, name):
    """AppTest run as an authed client session (gate must be on, else the
    role resolver treats local dev as coach). Caller keeps APP_PASSWORD set
    for any further at.run() calls."""
    at = AppTest.from_file(page, default_timeout=40)
    at.session_state["_authed"] = True
    at.session_state["_role"] = "client"
    at.session_state["_client_self"] = name
    at.run()
    return at


def _cleanup():
    cl.delete_client(SRC)
    cl.delete_client(TGT)


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


def _btn(at, key):
    hits = [b for b in at.button if getattr(b, "key", None) == key]
    assert hits, f"button {key!r} not found; have {[b.key for b in at.button]}"
    return hits[0]


def test_save_and_get_round_trip_versions_stamped():
    try:
        cl.save_training(SRC, dict(PROGRAM, version=None))
        t = cl.get_training(SRC)
        assert t["version"] == cl.TRAINING_VERSION
        assert t["block"] == 2 and t["week"] == 3 and t["weeks_total"] == 6
        assert [d["name"] for d in t["days"]] == ["Push", "Pull"]
        assert t["days"][0]["exercises"][0]["exercise"] == "Barbell Bench Press"
    finally:
        _cleanup()


def test_get_training_normalizes_old_and_junk_shapes():
    try:
        # partial exercise dicts, junk numerics, missing version — must load
        cl.upsert_client(SRC, {"training": {
            "block": "x", "days": [{"name": "Legs",
                                    "exercises": [{"exercise": "Squat"}]}]}})
        t = cl.get_training(SRC)
        assert t["version"] == cl.TRAINING_VERSION
        assert t["block"] == 1                      # junk -> default
        ex = t["days"][0]["exercises"][0]
        assert ex["exercise"] == "Squat"
        assert ex["sets"] == "" and ex["video"] == ""   # filled in
        # no training at all -> default skeleton
        cl.upsert_client(TGT, {})
        t2 = cl.get_training(TGT)
        assert [d["name"] for d in t2["days"]] == ["Push", "Pull", "Legs"]
    finally:
        _cleanup()


def test_coach_sees_builder_client_sees_placeholder():
    try:
        cl.save_training(SRC, PROGRAM)
        at = AppTest.from_file(TRAIN, default_timeout=40)   # ungated => coach
        at.session_state["client"] = SRC
        at.run()
        assert not at.exception
        _btn(at, f"tr_save::{SRC}")                          # editor + save
        _btn(at, f"tr_day::{SRC}::opt::Push")                # index-tab blocks
        assert any(getattr(t, "key", None) ==
                   f"tr::{SRC}::Push::0::exercise"
                   for t in at.text_input), "styled table cells missing"
        # client: their read-only view, never the builder
        os.environ["APP_PASSWORD"] = "tr-test-pw"
        try:
            at2 = _client_run(TRAIN, SRC)
        finally:
            os.environ.pop("APP_PASSWORD", None)
        assert not at2.exception
        assert not any((getattr(b, "key", "") or "").startswith("tr_save")
                       for b in at2.button), "client can reach the builder"
        assert "Push day." in _bodies(at2), "client program view missing"
    finally:
        _cleanup()


def test_client_program_view_read_only_with_video_links():
    os.environ["APP_PASSWORD"] = "tr-test-pw"
    try:
        cl.save_training(SRC, PROGRAM)
        at = _client_run(TRAIN, SRC)
        assert not at.exception
        body = _bodies(at)
        assert "Barbell Bench Press" in body and "Cable Fly" in body
        assert "4 × 6–8" in body, "scheme line missing"
        assert "Week 3 of 6" in body, "week chip missing"
        # video link ONLY where a video is set (bench yes, fly no)
        assert body.count("Watch demo") == 1, \
            f'expected exactly one demo link, got {body.count("Watch demo")}'
        # read-only: none of the builder's table inputs exist
        assert not any(str(getattr(ti, "key", "")).startswith("tr::")
                       for ti in at.text_input), "builder inputs leaked"
        # mark-done checkboxes exist, one per exercise
        keys = [getattr(c, "key", "") or "" for c in at.checkbox]
        assert f"tl::{SRC}::2-3::Push::0" in keys
        assert f"tl::{SRC}::2-3::Push::1" in keys
    finally:
        os.environ.pop("APP_PASSWORD", None)
        _cleanup()


def test_mark_done_round_trip_per_week():
    os.environ["APP_PASSWORD"] = "tr-test-pw"
    try:
        cl.save_training(SRC, PROGRAM)
        at = _client_run(TRAIN, SRC)
        key = f"tl::{SRC}::2-3::Push::0"
        at.checkbox(key=key).check()
        at.run()
        assert cl.get_training_log(SRC).get("2-3", {}).get("Push") == [0], \
            "tick did not persist"
        at.checkbox(key=key).uncheck()
        at.run()
        assert cl.get_training_log(SRC).get("2-3", {}).get("Push") == [], \
            "untick did not persist"
        # a different week keys separately — old week's log is untouched
        prog2 = dict(PROGRAM, week=4)
        cl.save_training(SRC, prog2)
        at2 = _client_run(TRAIN, SRC)
        at2.checkbox(key=f"tl::{SRC}::2-4::Push::1").check()
        at2.run()
        log = cl.get_training_log(SRC)
        assert log.get("2-4", {}).get("Push") == [1]
        assert log.get("2-3", {}).get("Push") == []
    finally:
        os.environ.pop("APP_PASSWORD", None)
        _cleanup()


def test_save_button_persists_week_and_exercises():
    try:
        cl.save_training(SRC, PROGRAM)
        at = AppTest.from_file(TRAIN, default_timeout=40)
        at.session_state["client"] = SRC
        at.run()
        at.number_input(key=f"tr_week::{SRC}").set_value(4)
        _btn(at, f"tr_save::{SRC}").click()
        at.run()
        assert not at.exception
        t = cl.get_training(SRC)
        assert t["week"] == 4, "week edit did not save"
        assert t["days"][0]["exercises"][0]["exercise"] == \
            "Barbell Bench Press", "exercises lost on save"
    finally:
        _cleanup()


def test_day_switch_keeps_edits():
    """The styled table's keyed inputs + keep-alive mean switching days no
    longer drops unsaved edits — and Save writes every edited day back."""
    try:
        cl.save_training(SRC, PROGRAM)
        at = AppTest.from_file(TRAIN, default_timeout=40)
        at.session_state["client"] = SRC
        at.run()
        cell = f"tr::{SRC}::Push::0::exercise"
        at.text_input(key=cell).input("Paused Bench Press")
        at.run()
        _btn(at, f"tr_day::{SRC}::opt::Pull").click()
        at.run()                                   # Push table not rendered
        _btn(at, f"tr_day::{SRC}::opt::Push").click()
        at.run()
        assert at.text_input(key=cell).value == "Paused Bench Press", \
            "edit lost when switching days"
        _btn(at, f"tr_save::{SRC}").click()
        at.run()
        t = cl.get_training(SRC)
        assert t["days"][0]["exercises"][0]["exercise"] == \
            "Paused Bench Press", "day-switched edit did not save"
    finally:
        _cleanup()


def test_duplicate_confirms_before_overwrite():
    try:
        cl.save_training(SRC, PROGRAM)
        tgt_own = {"version": 1, "block": 1, "week": 1, "weeks_total": 4,
                   "days": [{"name": "Full Body", "exercises": [
                       {"exercise": "Deadlift", "sets": "3", "reps": "5",
                        "rir": "2", "cue": "", "video": ""}]}]}
        cl.save_training(TGT, tgt_own)
        at = AppTest.from_file(TRAIN, default_timeout=40)
        at.session_state["client"] = SRC
        at.run()
        at.selectbox(key=f"tr_dup_target::{SRC}").select(TGT)
        _btn(at, f"tr_dup::{SRC}").click()
        at.run()
        # NOT overwritten yet — confirm UI is up instead
        assert cl.get_training(TGT)["days"][0]["name"] == "Full Body", \
            "existing program was silently overwritten"
        assert "already has a program" in _bodies(at), "confirm prompt missing"
        _btn(at, f"tr_dup_yes::{SRC}").click()
        at.run()
        t = cl.get_training(TGT)
        assert [d["name"] for d in t["days"]] == ["Push", "Pull"], \
            "confirmed duplicate did not copy"
    finally:
        _cleanup()


def test_duplicate_to_empty_client_copies_immediately():
    try:
        cl.save_training(SRC, PROGRAM)
        cl.upsert_client(TGT, {"goals": "Lose fat"})    # no program
        at = AppTest.from_file(TRAIN, default_timeout=40)
        at.session_state["client"] = SRC
        at.run()
        at.selectbox(key=f"tr_dup_target::{SRC}").select(TGT)
        _btn(at, f"tr_dup::{SRC}").click()
        at.run()
        assert not at.exception
        t = cl.get_training(TGT)
        assert [d["name"] for d in t["days"]] == ["Push", "Pull"], \
            "copy to program-less client should not need a confirm"
    finally:
        _cleanup()


def test_cardio_day_relabels_columns():
    prog = {"version": 1, "block": 1, "week": 1, "weeks_total": 4,
            "days": [{"name": "Cardio", "exercises": [
                {"exercise": "Incline Treadmill", "sets": "25 min",
                 "reps": "12% · 3.2 mph", "rir": "", "cue": "Zone 2",
                 "video": ""}]}]}
    os.environ["APP_PASSWORD"] = "tr-test-pw"
    try:
        cl.save_training(SRC, prog)
        # coach builder: header labels swap to Duration / Interval
        os.environ.pop("APP_PASSWORD", None)
        at = AppTest.from_file(TRAIN, default_timeout=40)
        at.session_state["client"] = SRC
        at.run()
        body = _bodies(at)
        assert "Duration" in body and "Interval" in body, \
            "cardio relabel missing in builder"
        # client view: scheme joins duration · interval
        os.environ["APP_PASSWORD"] = "tr-test-pw"
        at2 = _client_run(TRAIN, SRC)
        body2 = _bodies(at2)
        assert "25 min · 12% · 3.2 mph" in body2, \
            "cardio scheme line wrong in client view"
    finally:
        os.environ.pop("APP_PASSWORD", None)
        _cleanup()


def test_mark_workout_done_button():
    os.environ["APP_PASSWORD"] = "tr-test-pw"
    try:
        cl.save_training(SRC, PROGRAM)
        at = _client_run(TRAIN, SRC)
        key = f"tl_doneall::{SRC}::2-3::Push"
        _btn(at, key).click()
        at.run()
        assert cl.get_training_log(SRC).get("2-3", {}).get("Push") == [0, 1], \
            "workout-done did not log every exercise"
        # both checkboxes now ticked and the button flips to the done state
        assert at.checkbox(key=f"tl::{SRC}::2-3::Push::0").value is True
        assert at.checkbox(key=f"tl::{SRC}::2-3::Push::1").value is True
        done_btn = _btn(at, key)
        assert "complete" in (done_btn.label or "").lower(), \
            "button did not flip to Workout complete"
    finally:
        os.environ.pop("APP_PASSWORD", None)
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
