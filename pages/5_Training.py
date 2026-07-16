import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl

ui.setup("Training", "✳")
ui.client_picker()

ui.hero("Training.",
        "Program viewer — next up, this renders your TRAINING tabs "
        "(PUSH / PULL / LEGS, sets, reps, cues) as clean pages.",
        kicker="PROGRAMMING")

st.info("Coming next. Your sheet has a full program library "
        "(TRAINING - M1..M7, PUSH/PULL/LEGS rotations with exercises, sets, "
        "reps, RIR and coaching cues). I'll wire this page to display and edit "
        "those programs — say the word and I'll pull them in.")

st.markdown("For now, the interactive pieces live under **Meal Planner**, "
            "**Weigh-ins**, **Check-in** and **Supplements** in the sidebar.")
