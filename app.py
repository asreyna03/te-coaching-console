import html as _html
import sys
from datetime import date
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t

authed = ui.setup("Home", soft=True)

# Logged-out visitors (deployed with a gate set) get a public landing:
# the brand, the apply link — and a tucked-away login. Nothing else.
if not authed:
    st.markdown(
        '<div class="te-hero">'
        '<div class="kicker">Train &amp; Eat — coaching, measured</div>'
        '<h1>Coaching that <span class="mark">measures</span> everything '
        'that matters.</h1>'
        '<div class="sub">Apply in two minutes. We build your plan around '
        'real numbers — weight, macros, weekly check-ins — and adjust as '
        'you go.</div>'
        '</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns([0.34, 0.66], vertical_alignment="center")
    with col_a:
        st.markdown('<a class="applycta" href="/Apply" target="_self">'
                    'Apply now <span>→</span></a>', unsafe_allow_html=True)
    with col_b:
        st.button("Login  →", key="coach_access",
                  on_click=lambda: st.session_state.update(
                      show_coach_login=True))
    if st.session_state.get("show_coach_login"):
        ui.login_form()
    st.markdown('<div class="te-ruler"></div>', unsafe_allow_html=True)

    # Numbers below are honest: live food-DB count + how the program runs.
    # No invented social proof (client counts etc.) on the public page.
    lp_foods = sum(len(v) for v in cl.load_fooddb()[0].values())
    st.markdown(
        '<div class="te-stats">'
        '<div class="te-kicker">The console, at a glance</div>'
        '<div class="te-statgrid">'
        f'<div class="te-stat"><div class="cap">Foods · macro database</div>'
        f'<div class="num">{lp_foods}</div></div>'
        '<div class="te-stat"><div class="cap">Weigh-ins tracked / week</div>'
        '<div class="num">7</div></div>'
        '<div class="te-stat"><div class="cap">Coach check-in / week</div>'
        '<div class="num">1</div></div>'
        '</div></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="te-spread">'
        '<div class="te-kicker">Why it works</div>'
        '<div class="te-h2">Most plans guess. Ours <em>measure</em> — then '
        'adjust before you plateau.</div>'
        '<div class="te-proof">'
        '<div><div class="n">14</div>'
        '<div class="c">Data points / client / wk</div></div>'
        '<div><div class="n">100%</div>'
        '<div class="c">Plans built on real numbers</div></div>'
        '<div><div class="n">48h</div>'
        '<div class="c">Application response</div></div>'
        '</div>'
        '<div class="te-ruler"></div>'
        '</div>', unsafe_allow_html=True)

    st.markdown('<div class="te-ruler thin"></div>'
                '<div class="te-foot">Train &amp; Eat · Coaching, measured '
                '· ©2026</div>', unsafe_allow_html=True)
    st.stop()

active = ui.client_picker()
role = ui.require_role("coach", "client")


def _goal_direction(goals_text):
    """Which way the scale should move for this client, from their goals
    free-text. None => unknown, render the delta neutral."""
    t = (goals_text or "").lower()
    if any(w in t for w in ["build", "gain", "muscle", "bulk", "mass",
                            "strength", "bigger"]):
        return "gain"
    if any(w in t for w in ["lose", "cut", "fat", "lean", "drop", "shred",
                            "slim", "weight loss"]):
        return "loss"
    return None


def _panel_metrics(rec):
    """Metric cells for the client panel — shared by the coach console and a
    client's own home. Weight-delta color follows the client's goal: a gain
    is good news for a builder."""
    weighins = rec.get("weighins") or []
    weights = []
    for w in weighins:
        try:
            weights.append(float(w.get("Weight")))
        except (TypeError, ValueError):
            pass
    delta = None
    if len(weights) >= 2:
        change = weights[-1] - weights[0]
        arrow = "▼" if change < 0 else "▲"
        direction = _goal_direction(rec.get("goals", ""))
        if direction == "gain":
            tone = "good" if change > 0 else "over"
        elif direction == "loss":
            tone = "good" if change < 0 else "over"
        else:
            tone = "neutral"
        delta = (t("pm_since_start", arrow=arrow, n=f"{abs(change):.1f}"),
                 tone)
    td = rec.get("targets", {}).get("Training Day", {})
    cal_t = td.get("cal", rec.get("target_cal", ""))
    pro_t = td.get("protein", "")
    return [
        {"label": t("pm_bodyweight"), "value": rec.get("bodyweight") or "—",
         "delta": delta},
        {"label": t("pm_td_cal"), "value": cal_t or "—",
         "unit": "kcal" if cal_t else None},
        {"label": t("pm_td_protein"), "value": pro_t or "—",
         "unit": "g" if pro_t else None},
        {"label": t("pm_weighins"), "value": len(weighins)},
    ]


# ---- client home — the dashboard (matches te_client_dashboard.html) --------
if role == "client":
    me = active or ""
    rec = cl.get_client(me) if me else {}
    if not me:
        ui.empty_state(t("td_not_linked"), t("td_not_linked_sub"),
                       kicker=t("td_your_console"))
        st.stop()

    today = date.today()

    def _pdate(s):
        try:
            return date.fromisoformat(str(s).strip()[:10])
        except (TypeError, ValueError):
            return None

    def _pfloat(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    def _plink(page, label):
        try:
            st.page_link(page, label=label)
        except Exception:   # AppTest runs pages without the page registry
            st.markdown(f"<a href='#'>{_html.escape(label)}</a>",
                        unsafe_allow_html=True)

    entries = []
    for w in (rec.get("weighins") or []):
        d = _pdate(w.get("Date"))
        if d and d <= today:
            entries.append({"date": d, "w": _pfloat(w.get("Weight")),
                            "steps": _pfloat(w.get("Steps")),
                            "sleep": _pfloat(w.get("Sleep (hrs)"))})
    entries.sort(key=lambda e: e["date"])
    weights = [e for e in entries if e["w"] is not None]
    last_d = entries[-1]["date"] if entries else None

    start = _pdate(rec.get("start_date"))
    week_n = ((today - start).days // 7 + 1) \
        if start and start <= today else None

    # logging streak: consecutive weeks (back from now) with >=1 weigh-in;
    # an empty current week doesn't break a streak that's still alive.
    buckets = {(today - e["date"]).days // 7 for e in entries}
    streak, b = 0, (0 if 0 in buckets else (1 if 1 in buckets else None))
    if b is not None:
        while b in buckets:
            streak += 1
            b += 1

    goals_txt = (rec.get("goals") or "").strip()
    goal_line = goals_txt.splitlines()[0][:60] if goals_txt else ""
    coach = (rec.get("coach") or "").strip()
    first = _html.escape(me.split()[0])
    direction = _goal_direction(goals_txt)

    # ---- hero -----------------------------------------------------------
    kick = (f"[ {t('td_kicker_week', n=week_n)} ]" if week_n
            else f"[ {t('td_kicker')} ]")
    sub_bits = [x for x in (
        f"{t('td_goal')}: {_html.escape(goal_line.upper())}"
        if goal_line else "",
        f"{t('td_coach')}: {_html.escape(coach.upper())}" if coach else "",
        f"{t('td_started')} {_html.escape(rec['start_date'])}"
        if rec.get("start_date") else "") if x]
    streak_html = (f'<span class="td-streak">{t("td_streak", n=streak)}'
                   '</span>' if streak else "")
    st.markdown(
        f'<div class="te-hero td-hero"><div class="kicker">{kick}</div>'
        f'<h1>{t("td_hey")} <span class="mark">{first}.</span></h1>'
        f'<div class="td-sub">{" &nbsp;·&nbsp; ".join(sub_bits)}'
        f'{streak_html}</div></div>'
        '<div class="te-ruler"></div>', unsafe_allow_html=True)

    # ---- big stat strip (goal-aware) ------------------------------------
    cur_w = weights[-1]["w"] if weights else \
        _pfloat((rec.get("bodyweight") or "").split()[0]
                if rec.get("bodyweight") else None)
    w_v = f"{cur_w:g}<small> lb</small>" if cur_w is not None else "—"
    delta_html = ""
    if len(weights) >= 2:
        change = weights[-1]["w"] - weights[0]["w"]
        arrow = "▼" if change < 0 else "▲"
        if direction == "gain":
            tone = "good" if change > 0 else "over"
        elif direction == "loss":
            tone = "good" if change < 0 else "over"
        else:
            tone = "mut"
        delta_html = (f'<div class="d {tone}">{arrow} {abs(change):.1f} '
                      f'{t("td_since_start")}</div>')

    tgt = rec.get("targets", {}).get("Training Day", {})
    cal_t, pro_t = _pfloat(tgt.get("cal")), _pfloat(tgt.get("protein"))
    cal_v = f"{int(cal_t):,}<small> kcal</small>" if cal_t else "—"
    pro_d = (f'<div class="d mut">{t("td_protein_g", n=int(pro_t))}</div>'
             if pro_t else "")

    n_wi = len(rec.get("weighins") or [])
    upto = last_d is not None and (today - last_d).days <= 1
    wi_d = (f'<div class="d good">{t("td_up_to_date")}</div>' if upto
            else f'<div class="d warn">{t("td_log_due")}</div>')

    ci_done = week_n is not None and str(week_n) in (rec.get("checkins")
                                                     or {})
    ci_cell = (f'<div class="v" style="font-size:26px">{t("td_done")}</div>'
               f'<div class="d good">{t("td_this_week_chk")}</div>'
               if ci_done else
               f'<div class="v warn">{t("td_due")}</div>'
               f'<span class="td-pill">{t("td_do_it")}</span>')

    st.markdown(
        '<div class="td-stats">'
        f'<div class="stat"><div class="l">{t("peso_actual")}</div>'
        f'<div class="v">{w_v}</div>{delta_html}</div>'
        f'<div class="stat"><div class="l">{t("meta_semana")}</div>'
        f'<div class="v">{cal_v}</div>{pro_d}</div>'
        f'<div class="stat"><div class="l">{t("registros")}</div>'
        f'<div class="v">{n_wi}</div>{wi_d}</div>'
        f'<div class="stat"><div class="l">{t("checkin_semanal")}</div>'
        f'{ci_cell}</div></div>', unsafe_allow_html=True)

    # ---- quieter trend band ---------------------------------------------
    b0 = [e for e in entries if (today - e["date"]).days < 7]
    b1 = [e for e in entries if 7 <= (today - e["date"]).days < 14]
    b0w = [e["w"] for e in b0 if e["w"] is not None]
    b1w = [e["w"] for e in b1 if e["w"] is not None]
    wk_avg = (sum(b0w) / len(b0w)) if b0w else \
        ((sum(b1w) / len(b1w)) if b1w else None)
    rate = (sum(b0w) / len(b0w) - sum(b1w) / len(b1w)) \
        if b0w and b1w else None
    steps7 = [e["steps"] for e in b0 if e["steps"] is not None]
    sleep7 = [e["sleep"] for e in b0 if e["sleep"] is not None]
    rate_cls = ""
    if rate is not None and direction:
        rate_cls = "g" if ((rate > 0) if direction == "gain"
                           else (rate < 0)) else "o"
    trend = "</span><span>".join([
        (f"{t('td_weekly_avg')} <b>{wk_avg:.1f} lb</b>"
         if wk_avg is not None else f"{t('td_weekly_avg')} <b>—</b>"),
        (f'{t("td_rate")} <b class="{rate_cls}">{rate:+.1f} lb/wk</b>'
         if rate is not None else f"{t('td_rate')} <b>—</b>"),
        (f"{t('td_steps7')} <b>{int(sum(steps7) / len(steps7)):,}</b>"
         if steps7 else f"{t('td_steps7')} <b>—</b>"),
        (f"{t('td_sleep7')} <b>{sum(sleep7) / len(sleep7):.1f} h</b>"
         if sleep7 else f"{t('td_sleep7')} <b>—</b>"),
    ])
    st.markdown(f'<div class="td-trend"><span>{trend}</span></div>',
                unsafe_allow_html=True)

    # ---- where you're at: chart + this-week card ------------------------
    ui.label(t("td_where"))
    c_chart, c_week = st.columns([0.58, 0.42], gap="medium")
    with c_chart:
        with st.container(key="td_card_chart"):
            st.markdown(f'<div class="td-h3">{t("td_weight_trend")}</div>',
                        unsafe_allow_html=True)
            if len(weights) >= 2:
                import pandas as pd
                plot = pd.DataFrame(
                    [{"Date": e["date"].isoformat(), "Weight": e["w"]}
                     for e in weights])
                ui.weight_chart(plot, height=232)
            else:
                st.caption(t("td_two_logs"))
    with c_week:
        with st.container(key="td_card_week"):
            st.markdown(f'<div class="td-h3">{t("td_this_week")}</div>',
                        unsafe_allow_html=True)
            r1a, r1b, r1c = st.columns([0.13, 0.55, 0.32],
                                       vertical_alignment="center")
            r1a.markdown('<div class="td-ico">⚖</div>',
                         unsafe_allow_html=True)
            last_txt = (t("td_last", w=f"{weights[-1]['w']:g}",
                          d=(today - last_d).days)
                        if weights and last_d else t("td_no_logs"))
            r1b.markdown(f'<div class="td-todo-n">{t("td_log_today")}'
                         f'</div><div class="td-todo-s">{last_txt}</div>',
                         unsafe_allow_html=True)
            with r1c:
                with st.container(key="td_go_weigh"):
                    _plink("pages/2_Weigh_Ins.py", t("td_log_btn"))
            st.markdown('<div class="td-rule"></div>',
                        unsafe_allow_html=True)
            r2a, r2b, r2c = st.columns([0.13, 0.55, 0.32],
                                       vertical_alignment="center")
            r2a.markdown('<div class="td-ico">✎</div>',
                         unsafe_allow_html=True)
            r2b.markdown(f'<div class="td-todo-n">{t("td_weekly_checkin")}'
                         '</div><div class="td-todo-s">'
                         f'{t("td_ci_done") if ci_done else t("td_ci_due")}'
                         '</div>', unsafe_allow_html=True)
            with r2c:
                if ci_done:
                    st.markdown(f'<div class="td-done">{t("td_done_chip")}'
                                '</div>', unsafe_allow_html=True)
                else:
                    with st.container(key="td_go_check"):
                        _plink("pages/3_Check_In.py", t("td_start_btn"))
            st.markdown('<div class="td-rule"></div>',
                        unsafe_allow_html=True)
            r3a, r3b, r3c = st.columns([0.13, 0.55, 0.32],
                                       vertical_alignment="center")
            r3a.markdown('<div class="td-ico">🍽</div>',
                         unsafe_allow_html=True)
            has_plan = bool(tgt) or bool(rec.get("meal_plans"))
            r3b.markdown(f'<div class="td-todo-n">{t("td_meal_plan")}</div>'
                         '<div class="td-todo-s">'
                         f'{t("td_macros_set") if has_plan else t("td_not_set")}'
                         '</div>', unsafe_allow_html=True)
            with r3c:
                if has_plan:
                    st.markdown(f'<div class="td-done">{t("td_done_chip")}'
                                '</div>', unsafe_allow_html=True)
                else:
                    with st.container(key="td_ghost_meal"):
                        _plink("pages/1_Meal_Planner.py", t("td_view_btn"))

    # ---- quick cards -----------------------------------------------------
    ui.label(t("td_your_plan"))
    qcols = st.columns(3, gap="medium")
    for col, (num, title, desc, page, keyk) in zip(qcols, (
            ("01", t("mi_plan"), t("mi_plan_sub"),
             "pages/1_Meal_Planner.py", "td_qwrap_meal"),
            ("02", t("mi_entreno"), t("mi_entreno_sub"),
             "pages/5_Training.py", "td_qwrap_train"),
            ("03", t("mis_suplementos"), t("mis_suplementos_sub"),
             "pages/4_Supplements.py", "td_qwrap_supp"))):
        with col:
            with st.container(key=keyk):   # the WHOLE card navigates
                st.markdown(f'<div class="td-qcard"><div class="qn">'
                            f'[ {num} ]</div><h4>{title}</h4><p>{desc}</p>'
                            f'<div class="qgo">{t("abrir")}</div></div>',
                            unsafe_allow_html=True)
                _plink(page, t("abrir_a", x=title))

    # ---- note from the coach (hidden when empty) ------------------------
    note = (rec.get("coach_note") or "").strip()
    if note:
        who = _html.escape(coach) if coach else t("td_your_coach_lc")
        st.markdown(f'<div class="td-note"><div class="h">'
                    f'[ {t("td_note_from", who=who)} ]</div>'
                    f'<p>{_html.escape(note)}</p></div>',
                    unsafe_allow_html=True)
    st.stop()

# ===================== COACH — the coaching console ==========================
cats, lookup = cl.load_fooddb()
n_foods = sum(len(v) for v in cats.values())
supps = cl.load_supplements()
clients = cl.load_clients()

ui.hero("Train &amp; Eat.", kicker=t("co_kicker"))

ui.stat_row([
    (f'{n_foods}', t("co_foods_db")),
    (f'{len(cats)}', t("co_categories")),
    (f'{len(supps)}', t("co_supplements")),
    (f'{len(clients)}', t("co_clients_on_file")),
])

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

def _save_client(current):
    """Save the edited client info; handles renaming (moves the whole
    record to the new name and keeps the picker on it)."""
    k = f"cd_{current}"

    def v(field):
        return (st.session_state.get(f"{k}_{field}") or "").strip()

    patch = {"start_date": v("start"), "bodyweight": v("bw"),
             "stats": v("stats"), "goals": v("goals"),
             "contact_email": v("email"), "contact_phone": v("phone"),
             "age": v("age"), "coach": v("coach"),
             "coach_note": v("note"), "allergies": v("allergy")}
    newname = v("name") or current
    if newname != current:
        if newname in cl.load_clients():
            st.session_state["cd_msg"] = (
                "error", t("co_name_taken", name=newname))
            return
        full = cl.get_client(current)
        full.update(patch)
        cl.upsert_client(newname, full)
        cl.delete_client(current)
        st.session_state["client"] = newname
        st.session_state["client_pick_pending"] = newname
        st.session_state["cd_msg"] = ("success",
                                      t("co_renamed", name=newname))
    else:
        cl.upsert_client(current, patch)
        st.session_state["cd_msg"] = ("success", t("co_saved"))


if active:
    rec = clients.get(active, {})
    st.markdown('<span class="mono acc" style="display:block;margin:0 0 10px">'
                f'[ {t("co_active_client")} ]</span>', unsafe_allow_html=True)
    ui.allergy_bar(rec.get("allergies"))

    metrics = _panel_metrics(rec)
    contact_bits = [rec.get("contact_email", ""), rec.get("contact_phone", "")]
    if rec.get("start_date"):
        contact_bits.append(t("co_started", d=rec["start_date"]))
    ui.client_panel(active,
                    " · ".join(b for b in contact_bits if b) or "—",
                    metrics)

    if st.session_state.get("cd_msg"):
        kind, text = st.session_state.pop("cd_msg")
        (st.success if kind == "success" else st.error)(text)

    with st.expander(t("co_edit_info")):
        k = f"cd_{active}"
        with st.form("client_details"):
            a, b = st.columns(2)
            a.text_input(t("co_name"), value=active, key=f"{k}_name")
            b.text_input(t("co_start_date"), value=rec.get("start_date", ""),
                         key=f"{k}_start")
            c, d = st.columns(2)
            c.text_input(t("co_email"), value=rec.get("contact_email", ""),
                         key=f"{k}_email")
            d.text_input(t("co_phone"), value=rec.get("contact_phone", ""),
                         key=f"{k}_phone")
            e, f = st.columns(2)
            e.text_input(t("co_age"), value=rec.get("age", ""),
                         key=f"{k}_age")
            f.text_input(t("co_bodyweight"), value=rec.get("bodyweight", ""),
                         key=f"{k}_bw")
            st.text_input(t("co_stats"), value=rec.get("stats", ""),
                          placeholder="e.g. 5ft 9in — 175lbs",
                          key=f"{k}_stats")
            st.text_input(t("co_allergies"), value=rec.get("allergies", ""),
                          placeholder="e.g. Peanuts, Shellfish",
                          key=f"{k}_allergy")
            st.text_area(t("co_goals"), value=rec.get("goals", ""),
                         height=80, key=f"{k}_goals")
            st.text_input(t("co_coach_field"),
                          value=rec.get("coach", ""), key=f"{k}_coach",
                          placeholder="e.g. Eric")
            st.text_area(t("co_note_field"),
                         value=rec.get("coach_note", ""), height=70,
                         key=f"{k}_note")
            st.form_submit_button(t("co_save_info"), type="primary",
                                  on_click=_save_client, args=(active,))

        # ---- client login (set / reset) — outside the details form so a
        # password never rides along with a profile save ------------------
        st.markdown(f'<div class="mono acc" style="margin:16px 0 4px">'
                    f'[ {t("co_login_label")} ]</div>',
                    unsafe_allow_html=True)
        lg = rec.get("login") or {}
        if lg.get("active"):
            st.caption(t("co_login_current", u=lg.get("username", "—")))
        else:
            st.caption(t("co_login_none"))

        def _set_login(current):
            u = (st.session_state.get(f"cl_user_{current}") or "").strip() \
                or current.lower().replace(" ", ".")
            pw = (st.session_state.get(f"cl_pw_{current}") or "").strip()
            shown = pw or cl.generate_temp_password()
            cl.set_client_login(current, u, shown)
            st.session_state[f"cl_pw_{current}"] = ""
            # echo the password only when it was generated — a typed one is
            # already known to the coach and shouldn't be re-displayed
            st.session_state["cd_msg"] = ("success", t(
                "co_login_saved_tmp" if not pw else "co_login_saved",
                u=u, p=shown))

        lc1, lc2, lc3 = st.columns([0.38, 0.38, 0.24],
                                   vertical_alignment="bottom")
        lc1.text_input(t("co_login_user"),
                       value=lg.get("username", "") or
                       active.lower().replace(" ", "."),
                       key=f"cl_user_{active}")
        lc2.text_input(t("co_login_pw"), type="password",
                       placeholder=t("co_login_pw_ph"),
                       key=f"cl_pw_{active}")
        lc3.button(t("co_login_set"), key=f"cl_setlogin_{active}",
                   on_click=_set_login, args=(active,),
                   use_container_width=True)
else:
    ui.empty_state(t("co_no_client"), t("co_no_client_sub"),
                   kicker=t("co_active_client"))

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
st.markdown(f'<span class="mono acc">[ {t("co_whats_inside")} ]</span>',
            unsafe_allow_html=True)
st.write("")

cards = [
    ("01", t("nav_meal"), t("co_card_meal")),
    ("02", t("nav_weigh"), t("co_card_weigh")),
    ("03", t("nav_check"), t("co_card_check")),
    ("04", t("nav_supp"), t("co_card_supp", n=len(supps))),
    ("05", t("nav_train"), t("co_card_train")),
    ("06", t("nav_apps"), t("co_card_apps")),
]
cols = st.columns(3)
for i, (num, title, body) in enumerate(cards):
    with cols[i % 3]:
        st.markdown(ui.card(num, title, body), unsafe_allow_html=True)
        st.write("")

ui.marquee("TRAIN & EAT")
st.markdown('<div class="mono" style="margin-top:14px">'
            'Food database cached from your Google Sheet · client data in '
            'Supabase · independent of SOLARos</div>', unsafe_allow_html=True)
