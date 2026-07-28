"""Clients — the coach's roster sheet (moved to its own tab per Sam).

One row per client with week/weight/check-in/program/allergy status and a
plain-language to-do; the WHOLE row is the click target (invisible keyed
buttons overlaid on the styled HTML table). Clicking sets that client active
and opens their console on Home via SPA navigation. Coach-only.
"""
import html as _html
import sys
from datetime import date
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t

ui.setup("Clients", "✳")
ui.require_role("coach")
ui.client_picker()

clients = cl.load_clients()


def _progress_week(rec):
    try:
        sd = date.fromisoformat(str(rec.get("start_date", "")).strip()[:10])
    except (TypeError, ValueError):
        return None
    t = date.today()
    return ((t - sd).days // 7 + 1) if sd <= t else None


def _open_client(name):
    st.session_state["client"] = name
    st.session_state["_goto_home"] = True


def _create_client_sheet():
    """Create flow: profile + login, temp credentials shown once, then
    straight to their console on Home."""
    nm = (st.session_state.get("cs_newname") or "").strip()
    if not nm:
        st.session_state["cs_msg"] = ("error", t("cs_name_req"))
        return
    if nm in cl.load_clients():
        st.session_state["cs_msg"] = ("error", t("cs_exists", name=nm))
        return
    cl.upsert_client(nm, {})
    username = nm.lower().replace(" ", ".")
    temp_pw = cl.generate_temp_password()
    cl.set_client_login(nm, username, temp_pw)
    st.session_state["_onb_creds"] = {"name": nm, "username": username,
                                     "password": temp_pw}
    st.session_state["cs_newname"] = ""
    st.session_state["client"] = nm
    st.session_state["cs_msg"] = ("success", t("cs_created", name=nm))


# row click / create → open their console on Home (SPA, session survives).
# CAREFUL: st.switch_page navigates by RAISING a control-flow exception — a
# blanket except would swallow the navigation. Catch only the page-not-found
# case (AppTest runs this file standalone, without the page registry).
if st.session_state.pop("_goto_home", False):
    try:
        st.switch_page("app.py")
    except st.errors.StreamlitAPIException:
        pass

if st.session_state.get("cs_msg"):
    _k, _t = st.session_state.pop("cs_msg")
    (st.success if _k == "success" else st.error)(_t)
if st.session_state.get("_onb_creds"):
    _c = st.session_state.pop("_onb_creds")
    st.warning(t("onb_creds", name=_c["name"], u=_c["username"],
                 p=_c["password"]))

ui.hero(f'{t("nav_clients")}.', t("cs_sub"), kicker=t("co_kicker"))

sheet = []
for name in sorted(clients):
    rec = clients[name] or {}
    t_raw = rec.get("training") or {}
    has_prog = any(d.get("exercises") for d in t_raw.get("days", [])
                   if isinstance(d, dict))
    wk = _progress_week(rec)
    ci_state = ("done" if (wk is not None and str(wk) in
                           (rec.get("checkins") or {}))
                else ("due" if wk is not None else "unknown"))
    weights = []
    for w in (rec.get("weighins") or []):
        try:
            weights.append(float(w.get("Weight")))
        except (TypeError, ValueError):
            pass
    delta = tone = None
    if len(weights) >= 2:
        delta = weights[-1] - weights[0]
        direction = None
        gt = (rec.get("goals") or "").lower()
        if any(x in gt for x in ("build", "gain", "muscle", "bulk", "mass",
                                 "strength", "bigger")):
            direction = "gain"
        elif any(x in gt for x in ("lose", "cut", "fat", "lean", "drop",
                                   "shred", "slim", "weight loss")):
            direction = "loss"
        if direction == "gain":
            tone = "good" if delta > 0 else "over"
        elif direction == "loss":
            tone = "good" if delta < 0 else "over"
        else:
            tone = "mut"
    goals_txt = (rec.get("goals") or "").strip()
    sheet.append({
        "name": name,
        "goal": (goals_txt.splitlines()[0][:34] if goals_txt else "—"),
        "week": wk,
        "weeks_total": (t_raw.get("weeks_total") if has_prog else None),
        "cur_w": weights[-1] if weights else None,
        "delta": delta, "tone": tone,
        "n_wi": len(rec.get("weighins") or []),
        "ci": ci_state, "has_prog": has_prog,
        "allergy": (rec.get("allergies") or "").strip(),
    })

apps_all = cl.load_applications()
due = sum(1 for r in sheet if r["ci"] == "due")
to_build = sum(1 for r in sheet if not r["has_prog"])
new_apps = sum(1 for a in apps_all if a.get("status", "new") == "new")
ui.stat_row([
    (len(sheet), t("cs_active")),
    (due, t("cs_ci_due")),
    (to_build, t("cs_to_build")),
    (new_apps, t("cs_new_apps")),
])
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

hc1, hc2 = st.columns([0.82, 0.18], vertical_alignment="center")
with hc1:
    ui.label(t("cs_your_clients"))
with hc2:
    with st.popover(t("cs_new_client"), use_container_width=True):
        st.text_input(t("cs_client_name"), key="cs_newname",
                      placeholder="e.g. Eric Alvarez")
        st.button(t("cs_create"), key="cs_create",
                  on_click=_create_client_sheet, use_container_width=True)

if not sheet:
    ui.empty_state(t("cs_none"), t("cs_none_sub"),
                   kicker=t("nav_clients").upper())
    st.stop()


def _chip(txt, kind):
    return f'<span class="cs-chip {kind}">{txt}</span>'


trs = []
for r in sheet:
    nm = _html.escape(r["name"])
    wk_cell = (f'{r["week"]}' if r["week"] else "—") + " / " + \
        (f'{r["weeks_total"]}' if r["weeks_total"] else "—")
    if r["cur_w"] is not None:
        wt = f'{r["cur_w"]:g}'
        if r["delta"] is not None:
            arrow = "▼" if r["delta"] < 0 else "▲"
            wt += (f' <b class="{r["tone"]}">{arrow}'
                   f'{abs(r["delta"]):.1f}</b>')
    else:
        wt = "—"
    ci_cell = {"done": _chip(t("cs_done"), "done"),
               "due": _chip(t("cs_due"), "due"),
               "unknown": _chip("—", "none")}[r["ci"]]
    prog_cell = (_chip(t("cs_set"), "done") if r["has_prog"]
                 else _chip(t("cs_missing"), "miss"))
    al = r["allergy"]
    if al and al.lower() not in ("none", "n/a", "no", "-", "—"):
        al_cell = f'<span class="cs-al">⚠ {_html.escape(al)}</span>'
    else:
        al_cell = _chip(t("cs_none_chip"), "none")
    todo = []
    if not r["has_prog"]:
        todo.append(t("cs_build"))
    if r["ci"] == "due":
        todo.append(t("cs_checkin_todo"))
    todo_cls = ("over" if not r["has_prog"]
                else ("warn" if r["ci"] == "due" else "good"))
    todo_txt = " · ".join(todo) if todo else t("cs_all_good")
    trs.append(
        f'<tr><td><div class="cs-client"><div class="cs-av">'
        f'{_html.escape(r["name"][:1].upper())}</div>'
        f'<span class="cs-nm">{nm}</span></div></td>'
        f'<td class="cs-goal">{_html.escape(r["goal"])}</td>'
        f'<td class="cs-week">{wk_cell}</td>'
        f'<td class="cs-wt">{wt}</td>'
        f'<td class="cs-week">{r["n_wi"]}</td>'
        f'<td style="text-align:center">{ci_cell}</td>'
        f'<td style="text-align:center">{prog_cell}</td>'
        f'<td>{al_cell}</td>'
        f'<td class="cs-todo {todo_cls}">{todo_txt}</td>'
        f'<td class="cs-open">{t("cs_open_arrow")}</td></tr>')

HEAD_H, ROW_H = 83, 57   # bar + column-header height; verified in-browser
st.markdown("<style>" + "".join(
    f'.st-key-csrow_{i}{{position:absolute;'
    f'top:{HEAD_H + i * ROW_H}px;left:0;right:0;height:{ROW_H}px;'
    'z-index:4;margin:0}'
    f'.st-key-csrow_{i} [data-testid="stVerticalBlock"]{{gap:0}}'
    f'.st-key-csrow_{i} [data-testid="stLayoutWrapper"],'
    f'.st-key-csrow_{i} [data-testid="stElementContainer"],'
    f'.st-key-csrow_{i} .stButton{{width:100%!important}}'
    f'.st-key-csrow_{i} button{{width:100%!important;'
    f'height:{ROW_H}px!important;opacity:0!important;'
    'min-height:0!important;padding:0!important;border:none!important;'
    'border-radius:0!important}'
    for i in range(len(sheet))) + "</style>",
    unsafe_allow_html=True)
with st.container(key="clients_sheet"):
    st.markdown(
        f'<div class="cs-wrap"><div class="cs-bar">'
        f'<span>{t("cs_bar")}</span>'
        f'<span class="mt">{t("cs_bar_sub", n=len(sheet))}</span></div>'
        '<div class="cs-scroll"><table class="cs-tbl"><thead><tr>'
        f'<th>{t("cs_col_client")}</th><th>{t("cs_col_goal")}</th>'
        f'<th class="c">{t("cs_col_week")}</th>'
        f'<th class="r">{t("cs_col_weight")}</th>'
        f'<th class="c">{t("cs_col_weighins")}</th>'
        f'<th class="c">{t("cs_col_checkin")}</th>'
        f'<th class="c">{t("cs_col_program")}</th>'
        f'<th>{t("cs_col_allergy")}</th><th>{t("cs_col_todo")}</th>'
        f'<th class="r">{t("cs_col_open")}</th>'
        f'</tr></thead><tbody>{"".join(trs)}</tbody></table>'
        '</div></div>', unsafe_allow_html=True)
    for i, r in enumerate(sheet):
        with st.container(key=f"csrow_{i}"):
            st.button(f'Open {r["name"]}', key=f'cs_open::{r["name"]}',
                      on_click=_open_client, args=(r["name"],))
