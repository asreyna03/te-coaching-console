import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import altair as alt
import ui
import coachlib as cl

ui.setup("Weigh-ins", "⚖️")
active = ui.client_picker()

ui.hero("Weigh-ins.",
        "Daily weight, steps and sleep — charted as a trend that actually reads.",
        kicker="TRACKING")

if not active:
    st.info("👈 Pick or create a client in the sidebar first.")
    st.stop()

rec = cl.get_client(active)
cols = ["Date", "Weight", "Steps", "Sleep (hrs)", "Notes"]
data = rec.get("weighins", [])
df = pd.DataFrame(data) if data else pd.DataFrame(
    [{"Date": "", "Weight": None, "Steps": None, "Sleep (hrs)": None, "Notes": ""}])
for c in cols:
    if c not in df.columns:
        df[c] = None
df = df[cols]

st.markdown("#### 📅 Daily log")
edited = st.data_editor(
    df, num_rows="dynamic", width="stretch", hide_index=True,
    column_config={
        "Date": st.column_config.TextColumn("Date", help="e.g. 2026-07-01"),
        "Weight": st.column_config.NumberColumn("Weight (lbs)", step=0.1, format="%.1f"),
        "Steps": st.column_config.NumberColumn("Steps", step=100, format="%d"),
        "Sleep (hrs)": st.column_config.NumberColumn("Sleep (hrs)", step=0.5, format="%.1f"),
        "Notes": st.column_config.TextColumn("Notes", width="large"),
    },
    key=f"wi::{active}",
)

clean = edited.dropna(how="all")
clean = clean[clean["Date"].astype(str).str.strip() != ""]

# trend
plot = clean.dropna(subset=["Weight"]).copy()
if len(plot) >= 2:
    st.markdown("#### 📈 Weight trend")
    plot["Weight"] = pd.to_numeric(plot["Weight"], errors="coerce")
    lo, hi = plot["Weight"].min(), plot["Weight"].max()
    pad = max((hi - lo) * 0.25, 1.0)
    chart = (alt.Chart(plot).mark_line(point=True, color="#E5383B", strokeWidth=3)
             .encode(
                 x=alt.X("Date:N", title=None, sort=None),
                 y=alt.Y("Weight:Q", title="Weight (lbs)",
                         scale=alt.Scale(domain=[lo - pad, hi + pad])),
                 tooltip=["Date", "Weight"])
             .properties(height=300))
    st.altair_chart(chart, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Latest", f'{plot["Weight"].iloc[-1]:g} lbs')
    c2.metric("Change", f'{plot["Weight"].iloc[-1]-plot["Weight"].iloc[0]:+.1f} lbs')
    c3.metric("Avg", f'{plot["Weight"].mean():.1f} lbs')

st.divider()
if st.button("💾 Save log to client", type="primary"):
    cl.upsert_client(active, {"weighins": clean.to_dict("records")})
    st.success(f"Saved {len(clean)} entries for {active}.")
