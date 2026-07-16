import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
import streamlit as st
import ui
import coachlib as cl

ui.setup("Home")
active = ui.client_picker()

cats, lookup = cl.load_fooddb()
n_foods = sum(len(v) for v in cats.values())
supps = cl.load_supplements()
clients = cl.load_clients()

ui.hero("Train &amp; Eat.",
        "A coaching template, rebuilt as a live console. Plan the food. "
        "Track the weight. Run the check-in — every macro from your own database.",
        kicker="COACHING CONSOLE")

ui.stat_row([
    (f'{n_foods}', "FOODS · DATABASE"),
    (f'{len(cats)}', "CATEGORIES"),
    (f'{len(supps)}', "SUPPLEMENTS"),
    (f'{len(clients)}', "CLIENTS ON FILE"),
])

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

if active:
    rec = clients.get(active, {})
    st.markdown(f'<span class="mono acc">[ ACTIVE CLIENT ]</span>'
                f'<h2 style="margin-top:2px">{active}</h2>',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Start date", rec.get("start_date", "—"))
    c2.metric("Bodyweight", rec.get("bodyweight", "—"))
    td = rec.get("targets", {}).get("Training Day", {})
    c3.metric("TD cal target", td.get("cal", rec.get("target_cal", "—")))
    c4.metric("Weigh-ins", len(rec.get("weighins", [])))

    with st.expander("Edit client details"):
        with st.form("client_details"):
            a, b = st.columns(2)
            start = a.text_input("Start date", value=rec.get("start_date", ""))
            bw = b.text_input("Bodyweight", value=rec.get("bodyweight", ""))
            stats = st.text_input("Stats", value=rec.get("stats", ""),
                                  placeholder="e.g. 5ft 9in — 175lbs")
            goals = st.text_area("Goals", value=rec.get("goals", ""), height=80)
            if st.form_submit_button("Save details", type="primary"):
                cl.upsert_client(active, {"start_date": start, "bodyweight": bw,
                                          "stats": stats, "goals": goals})
                st.success("Saved.")
                st.rerun()
else:
    st.info("Pick or create a client in the sidebar to begin.")

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
st.markdown('<span class="mono acc">[ WHAT&apos;S INSIDE ]</span>',
            unsafe_allow_html=True)
st.write("")

cards = [
    ("01", "Meal Planner", "Pick foods, set servings — calories &amp; macros "
     "total live against target, training day or rest day."),
    ("02", "Weigh-ins", "Daily weight, steps &amp; sleep, charted as a trend "
     "that actually reads at scale."),
    ("03", "Check-in", "The weekly check-in, prompt for prompt — captured per "
     "week, per client."),
    ("04", "Supplements", f"{len(supps)} supplements. Reason for use, directions, "
     "buy links. Searchable."),
    ("05", "Training", "Program viewer — PUSH / PULL / LEGS, coming next."),
    ("06", "Sheet Sync", "Two-way with Google Sheets. Refresh the DB, push &amp; "
     "pull clients — on the app&apos;s own keys."),
]
cols = st.columns(3)
for i, (num, title, body) in enumerate(cards):
    with cols[i % 3]:
        st.markdown(ui.card(num, title, body), unsafe_allow_html=True)
        st.write("")

ui.marquee("TRAIN & EAT")
st.markdown('<div class="mono" style="margin-top:14px">'
            'Food database cached from your Google Sheet · client data stored '
            'locally · independent of SOLARos</div>', unsafe_allow_html=True)
