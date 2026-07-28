import sys
from datetime import date
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import ui
import coachlib as cl
from i18n import t, w_out, w_in

ui.setup("Weigh-ins", "✳")
ui.require_role("coach", "client")
active = ui.client_picker()

ui.hero(t("wi_title"), t("wi_sub"), kicker=t("wi_kicker"))

if not active:
    ui.empty_state(t("co_no_client"), t("wi_no_client_sub"),
                   kicker=t("nav_weigh").upper())
    st.stop()

rec = cl.get_client(active)

MSGK = "wi_msg"
if st.session_state.get(MSGK):
    st.success(st.session_state.pop(MSGK))

WI_COLS = [
    {"field": "Date", "label": t("wi_date"), "width": 0.9, "mono": True,
     "kind": "date"},
    {"field": "Weight", "label": t("wi_weight"), "width": 0.75,
     "mono": True},
    {"field": "Steps", "label": t("wi_steps"), "width": 0.7, "mono": True},
    {"field": "Sleep (hrs)", "label": t("wi_sleep"), "width": 0.75,
     "mono": True},
    {"field": "Notes", "label": t("wi_notes"), "width": 1.9},
]
table_key = f"wi::{active}"
_lang_now = st.session_state.get("_lang", "en")
if st.session_state.get(f"wi_units::{active}") != _lang_now:
    for _k in [k for k in st.session_state
               if str(k).startswith(f"wi::{active}::")]:
        del st.session_state[_k]
    st.session_state[f"wi_units::{active}"] = _lang_now
_disp_rows = [dict(r, Weight=(f"{w_out(r.get('Weight')):g}"
                              if str(r.get("Weight", "")).strip() else ""))
              for r in rec.get("weighins", [])]
ui.ensure_table(table_key, WI_COLS, _disp_rows)

wi_rows = ui.read_table_rows(table_key, WI_COLS)
clean = pd.DataFrame([r for r in wi_rows if r["Date"]])
if clean.empty:
    clean = pd.DataFrame(columns=[c["field"] for c in WI_COLS])
plot = clean[clean["Weight"].astype(str).str.strip() != ""].copy()
if len(plot):
    # rows can be newest-first (Add day prepends) — chart/stats sort by date
    plot = plot.sort_values("Date")
    plot["Weight"] = pd.to_numeric(plot["Weight"], errors="coerce")

# ---- stat cards on top ------------------------------------------------------
if len(plot) >= 2:
    delta = plot["Weight"].iloc[-1] - plot["Weight"].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric(t("wi_latest"),
              f'{plot["Weight"].iloc[-1]:g} {t("unit_w")}')
    c2.metric(t("wi_change"), f'{delta:+.1f} {t("unit_w")}')
    c3.metric(t("wi_average"),
              f'{plot["Weight"].mean():.1f} {t("unit_w")}')

# ---- toolbar right above the log: calendar picker + add-day (auto-today) ---
tb1, tb2, _tsp = st.columns([0.22, 0.2, 0.58], vertical_alignment="bottom")
tb1.date_input(t("wi_date"), value=date.today(), key=f"wi_date::{active}")


def _add_day():
    d = st.session_state.get(f"wi_date::{active}") or date.today()
    ui.add_table_row(table_key, WI_COLS, defaults={"Date": d},
                     prepend=True)   # the new row appears just under the button


tb2.button(t("wi_add_day"), key=f"wi_add::{active}", on_click=_add_day,
           type="primary")

ui.label(t("wi_daily_log"))
ui.editable_table(table_key, WI_COLS,
                  initial_rows=rec.get("weighins", []), add_label=None)

# ---- weight trend below the log --------------------------------------------
if len(plot) < 2:
    ui.empty_state(t("wi_no_trend"), t("wi_no_trend_sub"),
                   kicker=t("wi_trend"))
else:
    ui.label(t("wi_trend"))
    ui.weight_chart(plot, height=300)

st.divider()


def _save_log():
    rows = ui.read_table_rows(table_key, WI_COLS, require="Date")
    for r in rows:
        if str(r.get("Weight", "")).strip():
            r["Weight"] = f"{w_in(r['Weight']):g}"
    cl.upsert_client(active, {"weighins": rows})
    st.session_state.pop(f"wi_units::{active}", None)   # re-seed clean
    st.session_state[MSGK] = t("wi_saved_n", n=len(rows), name=active)


st.button(t("wi_save_btn"), type="primary", key=f"wi_save::{active}",
          on_click=_save_log)
