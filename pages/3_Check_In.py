import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t

ui.setup("Check-in", "✳")
ui.require_role("coach", "client")
active = ui.client_picker()

# Question strings are storage keys for saved weeks — never reword them.
# Grouping is display-only: answers still save as one flat dict.
SECTIONS = [
    (t("ci_sec_training"), [
        "Training Performance / Progressions / Regressions",
        "Training Recovery",
        "Training Readiness — Mentally, Physically",
    ]),
    (t("ci_sec_nutrition"), [
        "Nutritional Adjustments",
        "Stimulants",
        "Digestion",
        "Body Composition",
    ]),
    (t("ci_sec_recovery"), [
        "General Mood & Energy",
        "Expenditure / Activity Levels",
        "Sleep",
    ]),
    (t("ci_sec_notes"), [
        "Biggest Win of the Week",
        "Any Questions for me",
        "NEXT WEEK — Anything that will interrupt progression?",
        "Any other comments",
    ]),
]

ui.hero(t("ci_title"), t("ci_sub"), kicker=t("ci_kicker"))

if not active:
    ui.empty_state(t("co_no_client"), t("ci_no_client_sub"),
                   kicker=t("nav_check").upper())
    st.stop()

rec = cl.get_client(active)
checkins = rec.get("checkins", {})   # {week: {answers}}

week = st.number_input(t("ci_week_num"), min_value=1, value=1, step=1)
wk = str(int(week))
prev = checkins.get(wk, {})

with st.form(f"checkin::{active}::{wk}"):
    wavg = st.text_input(t("ci_wavg"), value=prev.get("weight_avg", ""))
    answers = {}
    for section, qs in SECTIONS:
        with st.container(border=True):
            ui.label(section)
            for q in qs:
                answers[q] = st.text_area(
                    q, value=prev.get("answers", {}).get(q, ""), height=70)
    submitted = st.form_submit_button(t("ci_save"), type="primary")

if submitted:
    checkins[wk] = {"weight_avg": wavg, "answers": answers}
    cl.upsert_client(active, {"checkins": checkins})
    st.success(t("ci_saved_wk", w=wk, name=active))

done = sorted((int(k) for k in checkins), key=int)
if done:
    st.caption(t("ci_weeks_saved") + ", ".join(str(w) for w in done))
