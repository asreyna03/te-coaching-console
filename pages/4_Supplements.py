import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl

ui.setup("Supplements", "💊")
ui.client_picker()
supps = cl.load_supplements()

ui.hero("Supplements.",
        f"{len(supps)} supplements from your database — reason for use, directions, "
        "buy links.", kicker="STACK")

q = st.text_input("Search", placeholder="Filter by name or reason…").strip().lower()
shown = 0
for s in supps:
    if not str(s["name"]).strip():
        continue
    blob = f'{s["name"]} {s["reason"]}'.lower()
    if q and q not in blob:
        continue
    shown += 1
    link = s.get("link", "")
    link_html = ""
    if link and str(link).startswith("http"):
        link_html = f' &nbsp;·&nbsp; <a href="{link}" target="_blank">Buy</a>'
    st.markdown(
        f'<div class="supp"><b>{s["name"]}</b>{link_html}'
        f'<div class="r">{s["reason"]}</div>'
        f'<div class="d">➜ {s["directions"]}</div></div>',
        unsafe_allow_html=True)

if q and shown == 0:
    st.info("No supplements match that search.")
