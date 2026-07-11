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
        "Pick foods from your database, set servings — calories &amp; macros "
        "total live against target. Training day or rest day.",
        kicker="NUTRITION")

if not active:
    st.info("👈 Pick or create a client in the sidebar first.")
    st.stop()

rec = cl.get_client(active)
daytype = st.radio("Day type", ["Training Day", "Non-Training Day"],
                   horizontal=True)
key = f"meal::{active}::{daytype}"

# ---- targets ----
ui.label("DAILY TARGETS")
tgt = rec.get("targets", {}).get(daytype, {})
d = 2500 if daytype == "Training Day" else 2200
t1, t2, t3, t4 = st.columns(4)
t_cal = t1.number_input("Calories", 0, value=int(tgt.get("cal", d)), step=10)
t_pro = t2.number_input("Protein (g)", 0, value=int(tgt.get("protein", 200)), step=5)
t_fat = t3.number_input("Fats (g)", 0, value=int(tgt.get("fats", 60)), step=5)
t_carb = t4.number_input("Carbs (g)", 0, value=int(tgt.get("carbs", 280)), step=5)

# ---- meal builder ----
if key not in st.session_state:
    saved = rec.get("meal_plans", {}).get(daytype)
    st.session_state[key] = pd.DataFrame(
        saved if saved else [{"Meal": "Meal 1", "Food": "", "Servings": 1.0}]
    )

ui.label("BUILD THE PLAN")
st.caption("Add rows with the ＋ at the bottom of the table. Pick a food, set servings.")
edited = st.data_editor(
    st.session_state[key],
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Meal": st.column_config.SelectboxColumn("Meal", options=MEALS, width="small"),
        "Food": st.column_config.SelectboxColumn("Food", options=[""] + FOODS,
                                                 width="large"),
        "Servings": st.column_config.NumberColumn("Servings", min_value=0.0,
                                                  step=0.25, format="%.2f"),
    },
    key=key + "::editor",
)

# ---- compute ----
rows = []
for _, r in edited.iterrows():
    food = str(r.get("Food", "") or "").strip()
    if not food:
        continue
    serv = r.get("Servings", 0) or 0
    cal, pro, fat, carb = cl.macros_for(lookup, food, serv)
    rows.append({"Meal": r.get("Meal", ""), "Food": food, "Servings": serv,
                 "Cal": round(cal), "Protein": round(pro, 1),
                 "Fats": round(fat, 1), "Carbs": round(carb, 1)})
res = pd.DataFrame(rows)

tc = int(res["Cal"].sum()) if not res.empty else 0
tp = round(res["Protein"].sum(), 1) if not res.empty else 0
tf = round(res["Fats"].sum(), 1) if not res.empty else 0
tk = round(res["Carbs"].sum(), 1) if not res.empty else 0

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

# ---- per-meal breakdown ----
if res.empty:
    st.info("Add foods in the table above (use the ＋ row at the bottom) to "
            "start building the plan.")
else:
    ui.label("BY MEAL")
    grp = res.groupby("Meal", sort=False).agg(
        Cal=("Cal", "sum"), Protein=("Protein", "sum"),
        Fats=("Fats", "sum"), Carbs=("Carbs", "sum")).reset_index()
    st.dataframe(grp, use_container_width=True, hide_index=True)
    with st.expander("Show every food row"):
        st.dataframe(res, use_container_width=True, hide_index=True)

# ---- save ----
st.divider()
if st.button("💾 Save this plan to client", type="primary"):
    plan_rows = [{"Meal": r["Meal"], "Food": r["Food"], "Servings": r["Servings"]}
                 for r in rows] or [{"Meal": "Meal 1", "Food": "", "Servings": 1.0}]
    mp = rec.get("meal_plans", {}); mp[daytype] = plan_rows
    tg = rec.get("targets", {})
    tg[daytype] = {"cal": t_cal, "protein": t_pro, "fats": t_fat, "carbs": t_carb}
    cl.upsert_client(active, {"meal_plans": mp, "targets": tg})
    st.success(f"Saved {daytype} plan for {active}.")

with st.expander("🔎 Browse the food database"):
    cat = st.selectbox("Category", cl.FOOD_CATS,
                       format_func=lambda c: f"{cl.CAT_ICON[c]} {cl.CAT_LABEL[c]}")
    df = pd.DataFrame(cats[cat])[["name", "serving", "calories", "protein",
                                  "fats", "carbs"]]
    df.columns = ["Food", "Serving", "Cal", "Protein", "Fats", "Carbs"]
    st.dataframe(df, use_container_width=True, hide_index=True)
