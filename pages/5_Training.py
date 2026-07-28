"""Training — the coach's program builder (clients get their read-only view
in the next phase; until then they see a friendly placeholder).

One styled editable table per training day (ui.editable_table — real keyed
inputs, so edits persist across day switches via the keep-alive loop), day
management via callbacks, and duplicate-to-client with an explicit overwrite
confirm — an existing program is never silently replaced. Save program is a
callback that writes EVERY edited day back to the record; day add/rename/
delete write immediately (renames migrate the table's session keys).
"""
import html as _html
import copy
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t as _t

ui.setup("Training", "✳")
role = ui.require_role("coach", "client")
active = ui.client_picker()

# ---- client view: their program, read-only + per-week mark-done ------------
if role == "client":
    if not active or not cl.has_program(active):
        ui.hero(f'{_t("nav_my_train")}.', _t("tc_hero_sub"),
                kicker=_t("nav_train").upper())
        ui.empty_state(_t("tc_almost"), _t("tc_almost_sub"),
                       kicker=_t("nav_my_train").upper())
        st.stop()

    t = cl.get_training(active)
    DAYS = [d["name"] for d in t["days"]]
    day_key = f"tl_day::{active}"
    if st.session_state.get(day_key) not in DAYS:
        st.session_state[day_key] = DAYS[0]
    day = st.session_state[day_key]
    week_key = f"{t['block']}-{t['week']}"

    def _mark_done(day_name, n):
        """Persist this day's ticked indexes for the current block-week."""
        idxs = [i for i in range(n) if st.session_state.get(
            f"tl::{active}::{week_key}::{day_name}::{i}")]
        cl.set_training_done(active, week_key, day_name, idxs)

    ui.hero(_t("tc_day_title", day=_html.escape(day)),
            _t("tc_day_sub"),
            kicker=_t("tc_kicker", b=t["block"]))

    pc1, pc2 = st.columns([0.76, 0.24], vertical_alignment="center")
    with pc1:
        ui.index_tabs(day_key, DAYS)
    pc2.markdown(f'<div class="te-blockchip" style="text-align:right">'
                 f'{_t("tc_week_of", w=t["week"], t=t["weeks_total"])}</div>',
                 unsafe_allow_html=True)

    day_rec = next(d for d in t["days"] if d["name"] == day)
    exercises = day_rec["exercises"]
    saved_done = set(cl.get_training_log(active)
                     .get(week_key, {}).get(day, []))

    if not exercises:
        ui.empty_state(_t("tc_rest"), _t("tc_rest_sub"),
                       kicker=_t("nav_my_train").upper())
        st.stop()

    with st.container(key="tl_list"):
        for idx, ex in enumerate(exercises):
            k = f"tl::{active}::{week_key}::{day}::{idx}"
            if k not in st.session_state:
                st.session_state[k] = idx in saved_done
            c_box, c_card = st.columns([0.05, 0.95],
                                       vertical_alignment="center")
            c_box.checkbox("Done", key=k, label_visibility="collapsed",
                           on_change=_mark_done,
                           args=(day, len(exercises)))
            bits = []
            sets, reps, rir = ex["sets"], ex["reps"], ex["rir"]
            if "cardio" in day.lower():
                parts = [x for x in (sets, reps) if x]
                if parts:
                    bits.append("<b>" + _html.escape(" · ".join(parts))
                                + "</b>")
            elif sets and reps:
                bits.append(f"<b>{_html.escape(sets)} × "
                            f"{_html.escape(reps)}</b>")
            elif sets:
                bits.append(f"<b>{_html.escape(sets)} "
                            f"{_t('tc_sets_word')}</b>")
            elif reps:
                bits.append(f"<b>{_html.escape(reps)} "
                            f"{_t('tc_reps_word')}</b>")
            if rir:
                bits.append(f"RIR {_html.escape(rir)}")
            scheme = ("<div class='scheme'>"
                      + " &nbsp;·&nbsp; ".join(bits) + "</div>") if bits else ""
            cue = (f"<div class='cue'>{_html.escape(ex['cue'])}</div>"
                   if ex["cue"] else "")
            vid = ""
            if ex["video"].startswith(("http://", "https://")):
                href = _html.escape(ex["video"], quote=True)
                vid = (f'<a class="vid" href="{href}" target="_blank" '
                       f'rel="noopener">▶&nbsp; ' + _t("tc_watch") + '</a>')
            c_card.markdown(
                f'<div class="te-ex"><div class="name">'
                f'{_html.escape(ex["exercise"])}</div>'
                f'{scheme}{cue}{vid}</div>', unsafe_allow_html=True)

    done_now = sum(bool(st.session_state.get(
        f"tl::{active}::{week_key}::{day}::{i}"))
        for i in range(len(exercises)))
    st.markdown(f'<div class="mono" style="margin-top:16px">'
                + _t("tc_progress", done=done_now, n=len(exercises),
                     day=day, w=t["week"]) + '</div>',
                unsafe_allow_html=True)

    def _mark_workout_done(day_name, n):
        """One tap = the whole day done: tick every box, save the log."""
        for i in range(n):
            st.session_state[f"tl::{active}::{week_key}::{day_name}::{i}"] \
                = True
        cl.set_training_done(active, week_key, day_name, list(range(n)))

    all_done = done_now == len(exercises)
    if all_done:
        st.button(_t("tc_complete"),
                  key=f"tl_doneall::{active}::{week_key}::{day}",
                  disabled=True)
    else:
        st.button(_t("tc_mark"), type="primary",
                  key=f"tl_doneall::{active}::{week_key}::{day}",
                  on_click=_mark_workout_done,
                  args=(day, len(exercises)))
    st.stop()

ui.hero(f'{_t("nav_train")}.', _t("ct_sub"), kicker=_t("ct_kicker"))

if not active:
    ui.empty_state(_t("co_no_client"), _t("ct_no_client_sub"),
                   kicker=_t("nav_train").upper())
    st.stop()

MSG_KEY = "tr_msg"
if st.session_state.get(MSG_KEY):
    kind, text = st.session_state.pop(MSG_KEY)
    (st.success if kind == "success" else st.error)(text)

# keep every day's table edits alive across day switches / reruns
ui.keep_table_alive(f"tr::{active}::")

training = cl.get_training(active)
DAYS = [d["name"] for d in training["days"]]

TABLE_COLS = [
    {"field": "exercise", "label": _t("ct_col_exercise"), "width": 2.3,
     "ph": "e.g. Barbell Bench Press"},
    {"field": "sets", "label": _t("ct_col_sets"), "width": 0.55, "mono": True},
    {"field": "reps", "label": _t("ct_col_reps"), "width": 0.75, "mono": True,
     "ph": "6–8"},
    {"field": "rir", "label": _t("ct_col_rir"), "width": 0.55, "mono": True},
    {"field": "cue", "label": _t("ct_col_cue"), "width": 2.1},
    {"field": "video", "label": _t("ct_col_video"), "width": 1.15, "ph": "https://…"},
]


def _is_cardio(day_name):
    return "cardio" in str(day_name).lower()


def _cols_for(day_name):
    """Cardio days keep the same row shape — the numeric columns just
    relabel (Duration / Interval), so old programs stay fully compatible."""
    if not _is_cardio(day_name):
        return TABLE_COLS
    cols = [dict(c) for c in TABLE_COLS]
    cols[1].update(label=_t("ct_col_duration"), width=0.8, ph="25 min")
    cols[2].update(label=_t("ct_col_interval"), width=0.95, ph="12% · 3.2 mph")
    return cols


# ---------- callbacks (day structure writes to the record immediately) ------
def _add_day():
    nm = (st.session_state.get(f"tr_newday::{active}") or "").strip()
    if not nm:
        st.session_state[MSG_KEY] = ("error", _t("ct_day_name_req"))
        return
    t = cl.get_training(active)
    if nm in [d["name"] for d in t["days"]]:
        st.session_state[MSG_KEY] = ("error", _t("ct_day_exists", name=nm))
        return
    t["days"].append({"name": nm, "exercises": []})
    cl.save_training(active, t)
    st.session_state[f"tr_day::{active}"] = nm
    st.session_state[f"tr_newday::{active}"] = ""
    st.session_state[MSG_KEY] = ("success", _t("ct_added", name=nm))


def _migrate_table_keys(old, new):
    """A renamed day keeps its unsaved table edits — move its session keys."""
    old_prefix = f"tr::{active}::{old}::"
    new_prefix = f"tr::{active}::{new}::"
    for k in [k for k in st.session_state if str(k).startswith(old_prefix)]:
        ks = str(k)
        if ks.endswith("::del") or ks.endswith("::addrow"):
            continue
        try:
            st.session_state[new_prefix + ks[len(old_prefix):]] = \
                st.session_state[k]
            del st.session_state[k]
        except Exception:
            pass


def _purge_table_keys(old):
    prefix = f"tr::{active}::{old}::"
    for k in [k for k in st.session_state if str(k).startswith(prefix)]:
        try:
            del st.session_state[k]
        except Exception:
            pass


def _rename_day(old):
    nm = (st.session_state.get(f"tr_rename::{active}::{old}") or "").strip()
    if not nm or nm == old:
        return
    t = cl.get_training(active)
    if nm in [d["name"] for d in t["days"]]:
        st.session_state[MSG_KEY] = ("error", _t("ct_day_exists", name=nm))
        return
    for d in t["days"]:
        if d["name"] == old:
            d["name"] = nm
    cl.save_training(active, t)
    _migrate_table_keys(old, nm)
    st.session_state[f"tr_day::{active}"] = nm
    st.session_state[MSG_KEY] = ("success",
                                 _t("ct_renamed", old=old, name=nm))


def _delete_day(old):
    t = cl.get_training(active)
    if len(t["days"]) <= 1:
        st.session_state[MSG_KEY] = ("error", _t("ct_need_one"))
        return
    t["days"] = [d for d in t["days"] if d["name"] != old]
    cl.save_training(active, t)
    _purge_table_keys(old)
    st.session_state[f"tr_day::{active}"] = t["days"][0]["name"]
    st.session_state[MSG_KEY] = ("success", _t("ct_deleted", name=old))


def _save_program():
    """Write block/week + EVERY day whose table has session edits."""
    t = cl.get_training(active)
    t["block"] = int(st.session_state.get(f"tr_block::{active}")
                     or t["block"])
    t["week"] = int(st.session_state.get(f"tr_week::{active}") or t["week"])
    t["weeks_total"] = int(st.session_state.get(f"tr_total::{active}")
                           or t["weeks_total"])
    touched = []
    for d in t["days"]:
        kb = f"tr::{active}::{d['name']}"
        if f"{kb}::rows" in st.session_state:
            d["exercises"] = ui.read_table_rows(kb, TABLE_COLS,
                                                require="exercise")
            touched.append(f'{d["name"]} ({len(d["exercises"])})')
    cl.save_training(active, t)
    st.session_state[MSG_KEY] = (
        "success", _t("ct_saved",
                      days=", ".join(touched) or _t("ct_program_word"),
                      b=t["block"], w=t["week"], t=t["weeks_total"]))


def _request_duplicate(src):
    """Copy the SAVED program to another client — but never silently over a
    program they already have; that asks for an explicit confirm first."""
    target = st.session_state.get(f"tr_dup_target::{src}")
    if not target:
        return
    if cl.has_program(target):
        st.session_state["tr_dup_pending"] = {"src": src, "target": target}
    else:
        _do_duplicate(src, target)


def _do_duplicate(src, target):
    t = copy.deepcopy(cl.get_training(src))
    cl.save_training(target, t)
    st.session_state.pop("tr_dup_pending", None)
    st.session_state[MSG_KEY] = (
        "success", _t("ct_copied", name=target, n=len(t["days"])))


def _cancel_duplicate():
    st.session_state.pop("tr_dup_pending", None)


# ---------- block / week context --------------------------------------------
st.markdown(
    f'<div class="mono" style="margin:2px 0 12px">{_t("ct_building")} '
    f'<b style="color:var(--ink)">{_html.escape(active)}</b>'
    f' &nbsp;·&nbsp; {_t("ct_block_up")} {training["block"]}'
    f' &nbsp;·&nbsp; {_t("ct_week_up")} {training["week"]} '
    f'{_t("ct_of_up")} {training["weeks_total"]}'
    f'</div>', unsafe_allow_html=True)

c_blk, c_wk, c_tot, _sp = st.columns([0.14, 0.14, 0.17, 0.55])
blk = c_blk.number_input(_t("ct_block"), 1, 99, int(training["block"]),
                         key=f"tr_block::{active}")
wk = c_wk.number_input(_t("ct_week"), 1, 52, int(training["week"]),
                       key=f"tr_week::{active}")
tot = c_tot.number_input(_t("ct_weeks_total"), 1, 52, int(training["weeks_total"]),
                         key=f"tr_total::{active}")

# ---------- day tabs (squared index blocks) + management --------------------
day_key = f"tr_day::{active}"
d_pick, d_add, d_manage = st.columns([0.6, 0.18, 0.22],
                                     vertical_alignment="bottom")
with d_pick:
    day = ui.index_tabs(day_key, DAYS)
with d_add:
    with st.popover(_t("ct_add_day"), use_container_width=True):
        st.text_input(_t("ct_day_name"), key=f"tr_newday::{active}",
                      placeholder="e.g. Upper A or Cardio")
        st.caption(_t("ct_tip"))
        st.button(_t("ct_add_day_btn"), key=f"tr_addday::{active}", on_click=_add_day,
                  use_container_width=True)
with d_manage:
    with st.popover(_t("ct_manage", day=day), use_container_width=True):
        st.text_input(_t("ct_rename_to"), value=day,
                      key=f"tr_rename::{active}::{day}")
        st.button(_t("ct_rename_btn"), key=f"tr_renamebtn::{active}::{day}",
                  on_click=_rename_day, args=(day,),
                  use_container_width=True)
        st.divider()
        st.button(_t("ct_delete_day", day=day),
                  key=f"tr_delday::{active}::{day}",
                  on_click=_delete_day, args=(day,),
                  use_container_width=True)

# ---------- the day's table (styled rows — data_editor is off-brand) --------
day_rec = next(d for d in training["days"] if d["name"] == day)
ui.label(_t("ct_exercises", day=day.upper()))
ui.editable_table(f"tr::{active}::{day}", _cols_for(day),
                  initial_rows=day_rec["exercises"],
                  add_label=_t("ct_add_ex"))
st.caption(_t("ct_edits_note"))

st.button(_t("ct_save"), type="primary", key=f"tr_save::{active}",
          on_click=_save_program)

# ---------- duplicate to another client -------------------------------------
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
ui.label(_t("ct_dup_label"))
others = [n for n in sorted(cl.load_clients()) if n != active]
if not others:
    st.caption(_t("ct_dup_none"))
else:
    dc1, dc2, _dsp = st.columns([0.34, 0.28, 0.38],
                                vertical_alignment="bottom")
    dc1.selectbox(_t("ct_dup_to"), others,
                  key=f"tr_dup_target::{active}")
    dc2.button(_t("ct_dup_btn"), key=f"tr_dup::{active}",
               on_click=_request_duplicate, args=(active,),
               use_container_width=True)
    st.caption(_t("ct_dup_note"))

pending = st.session_state.get("tr_dup_pending")
if pending and pending.get("src") == active:
    tgt = pending["target"]
    st.warning(_t("ct_overwrite", name=tgt, src=active))
    pc1, pc2, _psp = st.columns([0.28, 0.2, 0.52])
    pc1.button(_t("ct_yes", name=tgt),
               key=f"tr_dup_yes::{active}",
               on_click=_do_duplicate, args=(active, tgt),
               use_container_width=True)
    pc2.button(_t("ct_cancel"), key=f"tr_dup_no::{active}",
               on_click=_cancel_duplicate, use_container_width=True)
