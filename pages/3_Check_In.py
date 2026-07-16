import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl

ui.setup("Check-in", "✳")
active = ui.client_picker()

QUESTIONS = [
    "Biggest Win of the Week",
    "Training Performance / Progressions / Regressions",
    "Training Recovery",
    "Training Readiness — Mentally, Physically",
    "General Mood & Energy",
    "Expenditure / Activity Levels",
    "Nutritional Adjustments",
    "Stimulants",
    "Digestion",
    "Body Composition",
    "Sleep",
    "Any Questions for me",
    "NEXT WEEK — Anything that will interrupt progression?",
    "Any other comments",
]

ui.hero("Check-in.",
        "The weekly check-in — prompt for prompt, captured per week, per client.",
        kicker="ACCOUNTABILITY")

if not active:
    st.info("Pick or create a client in the sidebar to run a check-in.")
    st.stop()

rec = cl.get_client(active)
checkins = rec.get("checkins", {})   # {week: {answers}}

week = st.number_input("Week #", min_value=1, value=1, step=1)
wk = str(int(week))
prev = checkins.get(wk, {})

with st.form(f"checkin::{active}::{wk}"):
    wavg = st.text_input("Date — Weight Average", value=prev.get("weight_avg", ""))
    answers = {}
    for q in QUESTIONS:
        answers[q] = st.text_area(q, value=prev.get("answers", {}).get(q, ""),
                                  height=70)
    submitted = st.form_submit_button("Save check-in", type="primary")

if submitted:
    checkins[wk] = {"weight_avg": wavg, "answers": answers}
    cl.upsert_client(active, {"checkins": checkins})
    st.success(f"Saved Week {wk} check-in for {active}.")

done = sorted((int(k) for k in checkins), key=int)
if done:
    st.caption("Weeks with saved check-ins: " + ", ".join(str(w) for w in done))
