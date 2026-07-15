import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import ui
import coachlib as cl

ui.setup("Meal Planner", "🍽")
active = ui.client_picker()
cats, lookup = cl.load_fooddb()
FOODS = cl.all_food_names(cats)
MEALS = ["Pre", "Intra", "Post", "Meal 1", "Meal 2", "Meal 3", "Meal 4", "Meal 5"]

ui.hero("Meal Planner.",
        "One row per food — amounts in grams, several foods per meal, "
        "macros totalling live against target.",
        kicker="NUTRITION")

if not active:
    st.info("👈 Pick or create a client in the sidebar first.")
    st.stop()

rec = cl.get_client(active)
daytype = st.radio("Day type", ["Training Day", "Non-Training Day"],
                   horizontal=True)
key = f"mealtbl::{active}::{daytype}"          # scopes ALL plan widget state

# ---- targets (keyed per client+daytype so edits never leak across records) ----
ui.label("DAILY TARGETS")
tgt = rec.get("targets", {}).get(daytype, {})
d = 2500 if daytype == "Training Day" else 2200
t1, t2, t3, t4 = st.columns(4)
t_cal = t1.number_input("Calories", 0, value=int(tgt.get("cal", d)), step=10,
                        key=f"{key}::t::cal")
t_pro = t2.number_input("Protein (g)", 0, value=int(tgt.get("protein", 200)),
                        step=5, key=f"{key}::t::protein")
t_fat = t3.number_input("Fats (g)", 0, value=int(tgt.get("fats", 60)),
                        step=5, key=f"{key}::t::fats")
t_carb = t4.number_input("Carbs (g)", 0, value=int(tgt.get("carbs", 280)),
                         step=5, key=f"{key}::t::carbs")


def _amount_of(row_dict):
    """Amount for a saved row, converting old Servings-only rows."""
    amt = row_dict.get("Amount")
    if amt not in (None, ""):
        return cl._f(amt)
    sv = (cl._f(row_dict.get("Servings"))
          if row_dict.get("Servings") not in (None, "") else 1.0)
    food = str(row_dict.get("Food") or "").strip()
    if food in lookup:
        kind, qty, _ = cl.serving_info(lookup[food].get("serving", ""))
        return sv * qty if kind in ("g", "ml") else sv
    return sv


def _merged(base_df, editor_state):
    """Apply a data_editor edit log onto its base dataframe."""
    df = base_df.copy()
    for i_str, changes in (editor_state.get("edited_rows") or {}).items():
        i = int(i_str)
        if i < len(df):
            for c, v in changes.items():
                if c in df.columns:
                    df.iloc[i, df.columns.get_loc(c)] = v
    dels = [i for i in (editor_state.get("deleted_rows") or []) if i < len(df)]
    if dels:
        df = df.drop(df.index[dels]).reset_index(drop=True)
    for new in (editor_state.get("added_rows") or []):
        df.loc[len(df)] = {c: new.get(c) for c in df.columns}
    return df


def _stash_draft(base_key, editor_key):
    """on_change: snapshot the merged table so drafts survive daytype/client
    toggles (widget state is dropped by Streamlit when a widget unmounts)."""
    state = st.session_state.get(editor_key)
    base = st.session_state.get(base_key)
    if state is not None and base is not None:
        st.session_state[f"{base_key}::draft"] = _merged(base, state)


# ---- build the plan: one compact table ----
ui.label("BUILD THE PLAN")
st.caption("Add rows with the ＋ at the bottom. Several rows can share the same "
           "meal. **Amount = grams** (drinks in ml, items like bagels by count).")

editor_key = key + "::editor"
draft_key = key + "::draft"
# restore an unsaved draft after the editor unmounted (daytype/client toggle)
if draft_key in st.session_state and editor_key not in st.session_state:
    st.session_state[key] = st.session_state.pop(draft_key)
if key not in st.session_state:
    saved = rec.get("meal_plans", {}).get(daytype) or []
    init = [{"Meal": r.get("Meal") or "Meal 1",
             "Food": str(r.get("Food") or "").strip(),
             "Amount": float(_amount_of(r))}
            for r in saved if str(r.get("Food") or "").strip()]
    st.session_state[key] = pd.DataFrame(
        init or [{"Meal": "Meal 1", "Food": "", "Amount": None}])

edited = st.data_editor(
    st.session_state[key],
    num_rows="dynamic", width="stretch", hide_index=True,
    column_config={
        "Meal": st.column_config.SelectboxColumn("Meal", options=MEALS,
                                                 width="small"),
        "Food": st.column_config.SelectboxColumn("Food", options=[""] + FOODS,
                                                 width="large"),
        "Amount": st.column_config.NumberColumn(
            "Amount", min_value=0.0, step=5.0, format="%g",
            help="grams · drinks in ml · items by count"),
    },
    key=editor_key,
    on_change=_stash_draft, args=(key, editor_key),
)

# ---- compute ----
rows = []
for _, r in edited.iterrows():
    food = str(r.get("Food") or "").strip()
    if not food:
        continue
    item = lookup.get(food)
    raw = r.get("Amount")
    missing = raw is None or (isinstance(raw, float) and pd.isna(raw))
    if item:
        amt = cl.default_amount(item) if missing else cl._f(raw)
        servings = cl.servings_from_amount(item, amt)
        label = f"{food} {cl.amount_label(item, amt)}"
    else:
        amt = 0.0 if missing else cl._f(raw)
        servings = 0.0
        label = f"{food} (not in database)"
    cal, pro, fat, carb = cl.macros_for(lookup, food, servings)
    rows.append({"Meal": r.get("Meal") or "Meal 1", "Food": food,
                 "Amount": amt, "Servings": round(servings, 4), "Label": label,
                 "Cal": round(cal), "Protein": round(pro, 1),
                 "Fats": round(fat, 1), "Carbs": round(carb, 1)})

# ---- day totals vs target ----
tc = sum(r["Cal"] for r in rows)
tp = round(sum(r["Protein"] for r in rows), 1)
tf = round(sum(r["Fats"] for r in rows), 1)
tk = round(sum(r["Carbs"] for r in rows), 1)

ui.label("DAY TOTALS VS TARGET")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Calories", f"{tc} / {t_cal}", f"{t_cal - tc} left")
m2.metric("Protein", f"{tp:g} / {t_pro}g", f"{round(t_pro - tp, 1):g} left")
m3.metric("Fats", f"{tf:g} / {t_fat}g", f"{round(t_fat - tf, 1):g} left")
m4.metric("Carbs", f"{tk:g} / {t_carb}g", f"{round(t_carb - tk, 1):g} left")
if t_cal:
    st.progress(min(tc / t_cal, 1.0), text=f"{round(100*tc/t_cal)}% of calorie target")
if tc > 0:
    pc, fc, cc = tp * 4, tf * 9, tk * 4
    st.caption(f"**Calorie split** — 🥩 Protein {round(100*pc/tc)}%  ·  "
               f"🥑 Fats {round(100*fc/tc)}%  ·  🍚 Carbs {round(100*cc/tc)}%")

# ---- by meal: foods with grams in parentheses ----
if rows:
    ui.label("BY MEAL")
    meals_present = list(dict.fromkeys(r["Meal"] for r in rows))
    order = [m for m in MEALS if m in meals_present] + \
            [m for m in meals_present if m not in MEALS]
    for meal in order:
        mr = [r for r in rows if r["Meal"] == meal]
        mc = sum(r["Cal"] for r in mr)
        mp = sum(r["Protein"] for r in mr)
        mf = sum(r["Fats"] for r in mr)
        mk = sum(r["Carbs"] for r in mr)
        st.markdown(
            f'**{meal}** — {round(mc)} cal · P {mp:.1f} · F {mf:.1f} · C {mk:.1f}'
            f'<br><span style="color:#78736A">'
            f'{"  +  ".join(r["Label"] for r in mr)}</span>',
            unsafe_allow_html=True)
    with st.expander("Show every food row"):
        st.dataframe(pd.DataFrame(rows)[["Meal", "Food", "Amount", "Cal",
                                         "Protein", "Fats", "Carbs"]],
                     width="stretch", hide_index=True)
else:
    st.info("Add foods in the table above to start building the plan.")

# ---- save / reset ----
st.divider()
b1, b2, _ = st.columns([2, 2, 5])
if b1.button("💾 Save this plan to client", type="primary"):
    plan_rows = ([{"Meal": r["Meal"], "Food": r["Food"],
                   "Servings": r["Servings"], "Amount": r["Amount"]}
                  for r in rows]
                 or [{"Meal": "Meal 1", "Food": "", "Servings": 1.0}])
    mp = rec.get("meal_plans", {}); mp[daytype] = plan_rows
    tg = rec.get("targets", {})
    tg[daytype] = {"cal": t_cal, "protein": t_pro, "fats": t_fat, "carbs": t_carb}
    cl.upsert_client(active, {"meal_plans": mp, "targets": tg})
    st.toast(f"Saved {daytype} plan for {active} ✓")

if b2.button("↺ Reset to last saved"):
    for k in [k for k in st.session_state if str(k).startswith(key)]:
        del st.session_state[k]
    st.rerun()

with st.expander("🔎 Browse the food database"):
    cat = st.selectbox("Category", cl.FOOD_CATS,
                       format_func=lambda c: f"{cl.CAT_ICON[c]} {cl.CAT_LABEL[c]}")
    df = pd.DataFrame(cats[cat])[["name", "serving", "calories", "protein",
                                  "fats", "carbs"]]
    df.columns = ["Food", "Serving", "Cal", "Protein", "Fats", "Carbs"]
    st.dataframe(df, width="stretch", hide_index=True)
